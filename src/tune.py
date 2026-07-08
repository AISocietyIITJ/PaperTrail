import optuna
import wandb

import hydra
from omegaconf import DictConfig

import torch
import torch.nn as nn
import torch.optim as optim

from src.model import CNN
from src.dataset import get_dataloaders
from src.engine import train, check_accuracy
from src.utils import set_seed


@hydra.main(version_base=None, config_path="../configs", config_name="config")
def main(cfg: DictConfig):

    set_seed(cfg.seed)

    device = torch.device(
        "cuda" if torch.cuda.is_available() else "cpu"
    )

    def objective(trial):

        # -----------------------------
        # Hyperparameters to tune
        # -----------------------------
        learning_rate = trial.suggest_float(
            "learning_rate",
            1e-4,
            1e-2,
            log=True,
        )

        wandb.login()
        wandb.init(
            project="mnist-classifier-optuna",
            config={
                "learning_rate": learning_rate,
                "epochs": cfg.training.epochs,
                "batch_size": cfg.training.batch_size,
            },
        )

        train_loader, test_loader = get_dataloaders(
            cfg.training.batch_size
        )

        model = CNN(
            in_channels=cfg.model.in_channels,
            num_classes=cfg.model.num_classes,
        ).to(device)

        criterion = nn.CrossEntropyLoss()

        optimizer = optim.Adam(
            model.parameters(),
            lr=learning_rate,
        )

        train(
            model=model,
            train_loader=train_loader,
            optimizer=optimizer,
            criterion=criterion,
            device=device,
            num_epochs=cfg.training.epochs,
        )

        accuracy = check_accuracy(
            test_loader,
            model,
            device,
        )

        wandb.log({
            "test_accuracy": accuracy,
        })

        wandb.finish()

        return accuracy

    study = optuna.create_study(direction="maximize")

    study.optimize(
        objective,
        n_trials=3,
    )

    print("\nBest Accuracy:", study.best_value)
    print("Best Parameters:", study.best_params)


if __name__ == "__main__":
    main()