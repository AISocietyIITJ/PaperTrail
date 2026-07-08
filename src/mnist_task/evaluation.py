import torch
import torch.nn as nn
from torchinfo import summary

from mnist_task.data import get_dataloaders
from mnist_task.model import SmallCNN
from mnist_task.utils import get_device, set_seed


@torch.no_grad()
def compute_accuracy(model, loader, device) -> float:
    model.eval()
    correct, total = 0, 0
    for x, y in loader:
        x, y = x.to(device), y.to(device)
        preds = model(x).argmax(dim=1)
        correct += (preds == y).sum().item()
        total += x.size(0)
    return correct / total


def main(checkpoint_path: str = "model.pt"):
    set_seed(42)
    device = get_device()
    print(f"Using device: {device}")

    model = SmallCNN()
    model.load_state_dict(torch.load(checkpoint_path, map_location="cpu"))

    n_params = sum(p.numel() for p in model.parameters())
    print(f"Total parameters: {n_params}")
    summary(model, input_size=(1, 1, 28, 28))

    model = model.to(device)

    _, test_loader = get_dataloaders(
        data_dir="./data",
        pin_memory=device.type == "cuda",
    )
    acc = compute_accuracy(model, test_loader, device)
    print(f"Test accuracy: {acc:.4%}")

    assert n_params < 10_000, f"FAILS constraint: {n_params} params"
    assert acc > 0.985, f"FAILS constraint: {acc:.4%} accuracy"
    print("Meets both constraints")


if __name__ == "__main__":
    main()
