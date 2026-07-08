import torch


def train(model, train_loader, criterion, optimizer, device):
    model.train()

    total_loss = 0.0

    for images, labels in train_loader:
        images = images.to(device)
        labels = labels.to(device)

        optimizer.zero_grad()
        outputs = model(images)

        loss = criterion(outputs, labels)
        loss.backward()

        optimizer.step()

        total_loss += loss.item()

    return total_loss / len(train_loader)


def test(model, test_loader, device):
    model.eval()

    correct = 0.0
    samples = 0.0

    with torch.no_grad():
        for images, labels in test_loader:
            images = images.to(device)
            labels = labels.to(device)

            outputs = model(images)

            predictions = torch.argmax(outputs, dim=1)

            correct += (labels == predictions).sum().item()
            samples += predictions.size(0)

    return 100 * (correct / samples)
