import torch

with torch.no_grad():
    def compute_accuracy(model, data_loader, device):
        model.eval()
        correct_predictions = 0
        total_samples = 0

        for features, targets in data_loader:
            features, targets = features.to(device), targets.to(device)
            logits = model(features)
            _, predicted_labels = torch.max(logits, 1)
            total_samples += targets.size(0)
            correct_predictions += (predicted_labels == targets).sum().item()

        return (correct_predictions / total_samples) * 100
