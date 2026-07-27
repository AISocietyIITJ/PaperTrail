
import random
import numpy as np
import torch


def set_seed(seed: int) -> None:
    """
    Set random seeds for reproducibility.

    Args:
        seed (int): Random seed value.
    """

    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)

    if torch.cuda.is_available():
        torch.cuda.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)

    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False


def count_parameters(model) -> int:
    """
    Count the number of trainable parameters in the model.

    Args:
        model: PyTorch model

    Returns:
        int: Number of trainable parameters
    """

    return sum(
        p.numel()
        for p in model.parameters()
        if p.requires_grad
    )


def save_model(model, filepath: str) -> None:
    """
    Save model weights.

    Args:
        model: PyTorch model
        filepath (str): Path to save model
    """

    torch.save(model.state_dict(), filepath)
    print(f"Model saved to {filepath}")


def load_model(model, filepath: str):
    """
    Load model weights.

    Args:
        model: PyTorch model
        filepath (str): Path of saved model

    Returns:
        model: Model with loaded weights
    """

    model.load_state_dict(torch.load(filepath))
    model.eval()

    print(f"Model loaded from {filepath}")

    return model