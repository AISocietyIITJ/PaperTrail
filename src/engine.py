import torch
import wandb
def train(
    model,
    train_loader,
    optimizer,
    criterion,
    device,
    num_epochs
):

    model.train()

    for epoch in range(num_epochs):

        running_loss = 0.0

        for batch_idx, (data, targets) in enumerate(train_loader):

            data = data.to(device)
            targets = targets.to(device)

            scores = model(data)

            loss = criterion(scores, targets)

            optimizer.zero_grad()

            loss.backward()

            optimizer.step()

            running_loss += loss.item()

        avg_loss = running_loss /len(train_loader)

        print(f"Epoch {epoch+1}/{num_epochs} completed")

        wandb.log({
            "epoch" : epoch+1,
            "train_loss" : avg_loss,
        })
    return avg_loss 

def check_accuracy(loader, model,device):
    if loader.dataset.train:
        print("Checking accuracy on training data")
    else:
        print("Checking accuracy on test data")

    num_correct = 0
    num_samples = 0
    model.eval()

    with torch.no_grad():
        for x,y in loader:
            x = x.to(device = device)
            y = y.to(device = device)


            scores = model(x)
            _, predictions = scores.max(1)
            num_correct +=(predictions == y).sum()
            num_samples+=predictions.size(0)

    accuracy = (num_correct/num_samples) * 100

    print(f"Got {num_correct} / {num_samples} with accuracy {accuracy :.2f} %")

    model.train()
    return accuracy

