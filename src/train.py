from torchinfo import summary
import wandb

import hydra
from omegaconf import DictConfig

import torch
import torch.nn as nn
import torch.optim as optim

from src.model import CNN
from src.dataset import get_dataloaders
from src.engine import train, check_accuracy
from src.utils import set_seed, count_parameters

@hydra.main( version_base = None , config_path = "../configs" , config_name = "config")


def main(cfg : DictConfig):

    wandb.login()

    wandb.init(
        project="mnist-classifier",
        config={
            "batch_size": cfg.training.batch_size,
            "learning_rate": cfg.training.learning_rate,
            "epochs": cfg.training.epochs,
            "seed" : cfg.seed
        }
    )
    # -----------------------------
    # Reproducibility
    # -----------------------------
    set_seed(cfg.seed)

    # -----------------------------
    # Device Configuration
    # -----------------------------
    device = torch.device(
        "cuda" if torch.cuda.is_available() else "cpu"
    )

    print(f"Using device: {device}")

    # -----------------------------
    # Data Loaders
    # -----------------------------
    train_loader, test_loader = get_dataloaders(cfg.training.batch_size)

    # -----------------------------
    # Model
    # -----------------------------
    model = CNN(
        in_channels=cfg.model.in_channels,
        num_classes=cfg.model.num_classes
    ).to(device)

    summary(model,input_size=(1,1,28,28),)

    wandb.watch(model,log="all")

    # -----------------------------
    # Print Parameter Count
    # -----------------------------
    total_params = count_parameters(model)

    wandb.log({"total_parameters" : total_params})

    print(f"Total Trainable Parameters: {total_params}")

    if total_params >= 10000:
        print("WARNING: Model exceeds 10,000 parameters!")

    # -----------------------------
    # Loss Function & Optimizer
    # -----------------------------
    criterion = nn.CrossEntropyLoss()

    optimizer = optim.Adam(
        model.parameters(),
        lr=cfg.training.learning_rate
    )

    # -----------------------------
    # Training
    # -----------------------------
    train(
        model=model,
        train_loader=train_loader,
        optimizer=optimizer,
        criterion=criterion,
        device=device,
        num_epochs=cfg.training.epochs,
    )

    # -----------------------------
    # Evaluation
    # -----------------------------
    print("\nTraining Accuracy")

    train_accuracy = check_accuracy(
        train_loader,
        model,
        device,
    )

    print("\nTesting Accuracy")

    test_accuracy =check_accuracy(
        test_loader,
        model,
        device,
    )

    wandb.log({
        "train_accuracy": train_accuracy,
        "test_accuracy": test_accuracy,
    })




if __name__ == "__main__":
    main()