import torch
import torch.nn as nn
import torch.optim as optim
from torchinfo import summary

import hydra
from omegaconf import DictConfig

import optuna
import wandb

from src.data import get_dataloaders
from src.model import MNIST
from src.train import train, test


def objective(trial, cfg):
    lr = trial.suggest_float("lr", 1e-4, 1e-2, log=True)
    hidden_channels_1 = trial.suggest_int("hidden_channels_1", 4, 12)
    hidden_channels_2 = trial.suggest_int("hidden_channels_2", 8, 16)

    wandb.init(
        project="mnist_digit_recognizer",
        name=f"trial_{trial.number}",
        reinit=True,
        config={
            "learning_rate": lr,
            "hidden_channels_1": hidden_channels_1,
            "hidden_channels_2": hidden_channels_2,
            "batch_size": cfg.batch_size,
            "epochs": cfg.epochs,
        },
    )

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    train_loader, test_loader = get_dataloaders(cfg)

    model = MNIST(
        in_channels=1,
        hidden_channels_1=hidden_channels_1,
        hidden_channels_2=hidden_channels_2,
        num_classes=10,
    ).to(device)

    print(f"\n--- Model Summary for Trial {trial.number} ---")
    print(f"Hidden Channels: [{hidden_channels_1}, {hidden_channels_2}]")
    summary(model, input_size=(1, 1, 28, 28), verbose=1)

    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=lr)

    best_accuracy = 0.0

    for epoch in range(cfg.epochs):
        train_loss = train(model, train_loader, criterion, optimizer, device)
        accuracy = test(model, test_loader, device)
        wandb.log({"epoch": epoch, "train_loss": train_loss, "accuracy": accuracy})
        if accuracy > best_accuracy:
            best_accuracy = accuracy

    wandb.finish()

    return best_accuracy


@hydra.main(version_base=None, config_path="configs", config_name="config")
def main(cfg: DictConfig):

    study = optuna.create_study(direction="maximize")
    study.optimize(lambda trial: objective(trial, cfg), n_trials=10)

    print("BEST RESULT:")
    best_trial = study.best_trial

    print(f"  Final Accuracy: {best_trial.value:.2f}%")
    print("  Optimal Hyperparameters: ")
    for key, value in best_trial.params.items():
        print(f"    {key}: {value}")


if __name__ == "__main__":
    main()
