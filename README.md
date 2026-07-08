# MNIST Digit Classification with PyTorch

A lightweight Convolutional Neural Network (CNN) for handwritten digit recognition on the MNIST dataset.

This project demonstrates a complete deep learning workflow using **PyTorch**, **Hydra**, **Weights & Biases (WandB)**, and **Optuna** while satisfying the following constraints:

- Model with **< 10,000 trainable parameters**
- **> 98.5%** test accuracy
- Trains in **< 20 epochs**
- Reproducible experiments using fixed random seeds
- Modular project structure

---

## Features

- PyTorch CNN implementation
- Hydra configuration management
- WandB experiment tracking
- Optuna hyperparameter tuning
- Reproducible training
- Modular and PEP8-compliant code

---

## Results

| Metric | Value |
|--------|------:|
| Test Accuracy | **98.62%** |
| Trainable Parameters | **9098** |
| Epochs | **8** |

---

## Project Structure

```
learn_pytorch/
│
├── configs/
│   └── config.yaml
│
├── src/
│   ├── dataset.py
│   ├── engine.py
│   ├── model.py
│   ├── train.py
│   ├── tune.py
│   └── utils.py
│
├── outputs/
├── wandb/
├── pyproject.toml
├── uv.lock
└── README.md
```

---

## Tech Stack

- Python
- PyTorch
- Hydra
- Weights & Biases (WandB)
- Optuna
- uv

---

## Installation

Clone the repository

```bash
git clone <repository-url>
cd learn_pytorch
```

Create and activate the virtual environment using **uv**

```bash
uv sync
```

or install dependencies manually

```bash
pip install -r requirements.txt
```

---

## Configuration

All training configurations are managed using **Hydra**.

Example configuration (`configs/config.yaml`):

```yaml
training:
  batch_size: 64
  learning_rate: 0.001
  epochs: 8

model:
  in_channels: 1
  num_classes: 10

seed: 42
```

---

## Training

Run the training script

```bash
python src/train.py
```

The script will

- Load the MNIST dataset
- Train the CNN
- Evaluate on the test set
- Log metrics to WandB

---

## Hyperparameter Tuning

Hyperparameter tuning is performed using **Optuna**.

Run

```bash
python src/tune.py
```

Optuna searches for the best hyperparameters and logs each trial as a separate WandB experiment.

Example tuned hyperparameter:

- Learning Rate

---

## Experiment Tracking

Weights & Biases is used to log

- Training Loss
- Training Accuracy
- Test Accuracy
- Hyperparameters
- Experiment Configurations

Each training run and Optuna trial is automatically tracked.

---

## Reproducibility

To ensure reproducible experiments:

- Fixed random seeds
- Hydra configuration management
- Deterministic training setup

---

## Model Summary

| Property | Value |
|-----------|------:|
| Architecture | CNN |
| Trainable Parameters | 9098 |
| Dataset | MNIST |
| Optimizer | Adam |
| Loss Function | Cross Entropy Loss |

---

## Assignment Requirements

| Requirement | Status |
|------------|--------|
| PyTorch Implementation | ✅ |
| Model < 10K Parameters | ✅ |
| Test Accuracy > 98.5% | ✅ |
| Train in <20 Epochs | ✅ |
| Hydra Configuration | ✅ |
| WandB Logging | ✅ |
| Optuna Hyperparameter Tuning | ✅ |
| Reproducibility | ✅ |
| Modular Code Structure | ✅ |

---

## Future Improvements

- Tune additional hyperparameters (batch size, optimizer)
- Save the best model checkpoint
- Docker support
- Mixed precision (FP16) training
- Learning rate scheduling

---

## Author

**Harshika Bajaj**

IIT Jodhpur