from pathlib import Path

import hydra
import torch
import torch.nn as nn
import wandb
from omegaconf import DictConfig, OmegaConf
from torchinfo import summary

from mnist_task.data import get_dataloaders
from mnist_task.model import SmallCNN
from mnist_task.utils import get_device, set_seed

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = str(PROJECT_ROOT / "configs")


def train_one_epoch(
    model, loader, optimizer, criterion, device, scaler=None, use_mixed=False
):
    model.train()
    total_loss, correct, total = 0.0, 0, 0
    device_type = device.type
    autocast_enabled = use_mixed and device_type in {"cpu", "mps"}

    # Use float16 on MPS/CUDA and bfloat16 on CPU.
    dtype = torch.float16 if device_type in {"cuda", "mps"} else torch.bfloat16

    for x, y in loader:
        x, y = x.to(device), y.to(device)
        optimizer.zero_grad()

        if autocast_enabled:
            if device_type == "cuda":
                autocast_ctx = torch.cuda.amp.autocast(dtype=torch.float16)
            else:
                autocast_ctx = torch.autocast(device_type=device_type, dtype=dtype)

            with autocast_ctx:
                out = model(x)
                loss = criterion(out, y)
            if scaler is not None:
                scaler.scale(loss).backward()
                scaler.step(optimizer)
                scaler.update()
            else:
                loss.backward()
                optimizer.step()
        else:
            out = model(x)
            loss = criterion(out, y)
            loss.backward()
            optimizer.step()

        total_loss += loss.item() * x.size(0)
        correct += (out.argmax(1) == y).sum().item()
        total += x.size(0)
    return total_loss / total, correct / total


@torch.no_grad()
def evaluate(model, loader, criterion, device):
    model.eval()
    total_loss, correct, total = 0.0, 0, 0
    for x, y in loader:
        x, y = x.to(device), y.to(device)
        out = model(x)
        loss = criterion(out, y)
        total_loss += loss.item() * x.size(0)
        correct += (out.argmax(1) == y).sum().item()
        total += x.size(0)
    return total_loss / total, correct / total


def run_training(cfg: DictConfig, log_to_wandb: bool = True):
    set_seed(cfg.seed)

    # Prefer Apple Silicon MPS, then CUDA, then CPU.
    device = get_device()
    print(f"Using device: {device}")

    model = SmallCNN(
        c1=cfg.model.c1, c2=cfg.model.c2, c3=cfg.model.c3, c4=cfg.model.c4
    ).to(device)

    n_params = sum(p.numel() for p in model.parameters())
    if n_params >= 10_000:
        raise ValueError(f"Model has {n_params} params, must be < 10,000")

    train_loader, test_loader = get_dataloaders(
        data_dir=cfg.dataset.data_dir,
        batch_size=cfg.trainer.batch_size,
        num_workers=cfg.trainer.num_workers,
        pin_memory=device.type == "cuda",
    )

    optimizer = torch.optim.Adam(
        model.parameters(), lr=cfg.optimizer.lr, weight_decay=cfg.optimizer.weight_decay
    )
    # Cosine annealing scheduler for better convergence
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
        optimizer, T_max=cfg.trainer.epochs
    )
    criterion = nn.CrossEntropyLoss()

    scaler = (
        torch.amp.GradScaler(device.type)
        if cfg.trainer.mixed_precision and device.type in {"cpu", "cuda", "mps"}
        else None
    )

    if log_to_wandb:
        wandb.init(
            project="papertrail-mnist", config=OmegaConf.to_container(cfg, resolve=True)
        )
        wandb.watch(model)

    best_acc = 0.0
    for epoch in range(cfg.trainer.epochs):
        train_loss, train_acc = train_one_epoch(
            model,
            train_loader,
            optimizer,
            criterion,
            device,
            scaler,
            cfg.trainer.mixed_precision,
        )
        test_loss, test_acc = evaluate(model, test_loader, criterion, device)
        scheduler.step()
        best_acc = max(best_acc, test_acc)

        print(
            f"Epoch {epoch+1}/{cfg.trainer.epochs} | train_loss {train_loss:.4f} train_acc {train_acc:.4f} "
            f"| test_loss {test_loss:.4f} test_acc {test_acc:.4f}"
        )

        if log_to_wandb:
            wandb.log(
                {
                    "epoch": epoch + 1,
                    "train_loss": train_loss,
                    "train_acc": train_acc,
                    "test_loss": test_loss,
                    "test_acc": test_acc,
                    "n_params": n_params,
                    "lr": scheduler.get_last_lr()[0],
                }
            )

    # Log advanced WandB plots at the end of training
    if log_to_wandb:
        # Collect all predictions for confusion matrix
        all_preds = []
        all_labels = []
        model.eval()
        with torch.no_grad():
            for x, y in test_loader:
                x = x.to(device)
                out = model(x)
                all_preds.extend(out.argmax(1).cpu().numpy())
                all_labels.extend(y.numpy())

        # Confusion matrix
        wandb.log(
            {
                "confusion_matrix": wandb.plot.confusion_matrix(
                    probs=None,
                    y_true=all_labels,
                    preds=all_preds,
                    class_names=[str(i) for i in range(10)],
                )
            }
        )

        # Table of sample predictions
        x_sample, y_sample = next(iter(test_loader))
        x_sample = x_sample[:32].to(device)
        y_sample = y_sample[:32]
        with torch.no_grad():
            out_sample = model(x_sample)
            preds_sample = out_sample.argmax(1).cpu().numpy()

        table = wandb.Table(columns=["image", "label", "prediction"])
        for img, lbl, prd in zip(x_sample.cpu(), y_sample, preds_sample):
            img_np = (img.squeeze().numpy() * 0.3081 + 0.1307) * 255
            img_np = img_np.clip(0, 255).astype("uint8")
            table.add_data(wandb.Image(img_np), int(lbl), int(prd))
        wandb.log({"test_predictions_sample": table})

        wandb.summary["best_test_acc"] = best_acc
        wandb.summary["n_params"] = n_params
        wandb.finish()

    torch.save(model.state_dict(), "model.pt")

    return best_acc, n_params


@hydra.main(config_path=CONFIG_PATH, config_name="config", version_base=None)
def main(cfg: DictConfig):
    model = SmallCNN(c1=cfg.model.c1, c2=cfg.model.c2, c3=cfg.model.c3, c4=cfg.model.c4)
    summary(model, input_size=(1, 1, 28, 28))
    run_training(cfg)


if __name__ == "__main__":
    main()
