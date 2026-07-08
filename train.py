import os
import torch
import torch.nn as nn
import torch.optim as optim
import hydra
from omegaconf import DictConfig, OmegaConf
import wandb
from src.models.MNIST_classifier import MNIST_classifier
from src.datasets.mnist_dataloader import get_mnist_loaders
from src.utils.evaluation import compute_accuracy
from torch.optim.lr_scheduler import CosineAnnealingLR

DEVICE = 'cuda' if torch.cuda.is_available() else 'cpu'
print(f"Using device: {DEVICE}")

@hydra.main(version_base=None, config_path="conf", config_name="config")
def train(cfg: DictConfig) -> float:
    print(OmegaConf.to_yaml(cfg))
    
    print(f"Training on {cfg.dataset} dataset...")
    print(f"Hyperparameters: LR={cfg.lr}, Batch Size={cfg.batch_size}")
    input_channels = 1
    num_classes = 10
    learning_rate = cfg.lr
    batch_size = cfg.batch_size
    num_epochs = cfg.epochs

    run = wandb.init(
        project="mnist model",
        group="optuna sweep",
        config=OmegaConf.to_container(cfg=cfg, resolve=True),
        reinit=True
    )

    train_loader, test_loader = get_mnist_loaders(data_dir="./data", batch_size=batch_size)

    model = MNIST_classifier(inp_channel=input_channels, num_classes=num_classes)
    model = model.to(device=DEVICE)
    
    optimizer = optim.Adam(model.parameters(), lr=learning_rate)
    shedular = CosineAnnealingLR(optimizer=optimizer, T_max=num_epochs)
    loss_fn = nn.CrossEntropyLoss()

    train_acc_list = []
    for epoch in range(num_epochs):
        losses = []
        model.train()

        for batch_idx, (features, targets) in enumerate(train_loader):
            features = features.to(DEVICE)
            targets = targets.to(DEVICE)

            logits = model(features)
            loss = loss_fn(logits, targets)
            optimizer.zero_grad()

            loss.backward()
            optimizer.step()
            shedular.step()

            losses.append(loss.item())
        
        train_loss = (sum(losses) / len(losses))
        print(f"{epoch+1}/{num_epochs} epoch | loss = {train_loss:.4f}")

        
        train_acc = compute_accuracy(model=model, data_loader=train_loader, device=DEVICE)
        val_acc = compute_accuracy(model=model,data_loader=test_loader, device=DEVICE)
        print(f"Train Acc : {train_acc:.4f}| Val Acc: {val_acc:.4f}")
        train_acc_list.append(train_acc)

        wandb.log({
            "epoch":epoch,
            "train/loss":train_loss,
            "train/accuracy":train_acc,
            "train/val_accuracy":val_acc,
            "lr":learning_rate
        })

    test_acc = compute_accuracy(model=model, data_loader=test_loader, device=DEVICE)
    print(f"Test Acc : {test_acc}")

    
    print(f"Parameters after trail : lr={cfg.lr:.4f}, batch_size={cfg.batch_size} -> Accuracy: {test_acc:.4f}")
    print("-------------------------------------------------------------------------------------------------------\n")
    
    os.makedirs('checkpoints', exist_ok=True)
    torch.save(model.state_dict(), 'checkpoints/mnistModel.pt')
    
    run.finish()
    return test_acc

if __name__ == "__main__":
    train()