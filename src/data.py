import torch
from torch.utils.data import DataLoader
import torchvision.datasets as datasets
import torchvision.transforms as transforms


def get_dataloaders(cfg):
    torch.manual_seed(cfg.seed)
    transform = transforms.Compose(
        [transforms.ToTensor(), transforms.Normalize((0.1307,), (0.3081,))]
    )
    train_dataset = datasets.MNIST(
        root="dataset/", train=True, transform=transform, download=True
    )
    train_loader = DataLoader(
        dataset=train_dataset, batch_size=cfg.batch_size, shuffle=True
    )
    test_dataset = datasets.MNIST(
        root="dataset/",
        train=False,
        transform=transform,
        download=True,
    )
    test_loader = DataLoader(
        dataset=test_dataset,
        batch_size=cfg.batch_size,
        shuffle=False,
    )

    return train_loader, test_loader
