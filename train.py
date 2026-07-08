import numpy as np
import torch
import torchvision
import torch.nn as nn
from torch.utils.data import DataLoader
import torch.optim as optim
import torch.nn.functional as F
import torchvision.datasets as datasets
import torchvision.transforms as transforms
import hydra
from omegaconf import DictConfig, OmegaConf
from torchinfo import summary
import wandb



class MNIST_classifier(nn.Module):
    def __init__(self,inp_channel=1, num_classes=10):
        super(MNIST_classifier, self).__init__()
        self.conv1=nn.Conv2d(in_channels=inp_channel,out_channels=8,kernel_size=(3,3),stride=(1,1),padding=(1,1))
        self.pool = nn.MaxPool2d(kernel_size=(2,2), stride=(2,2))
        self.conv2=nn.Conv2d(in_channels=8, out_channels=16, kernel_size=(3,3), stride=(1,1), padding=(1,1))
        self.fc = nn.Linear(16*7*7,num_classes)

    def forward(self,x):
        x = F.leaky_relu(self.conv1(x))
        x = self.pool(x)
        x = F.leaky_relu(self.conv2(x))
        x = self.pool(x)
        x = x.reshape(x.shape[0],-1)
        x = self.fc(x)
        return x
    

model = MNIST_classifier(inp_channel=1, num_classes=10)
print(summary(model=model))


DEVICE = 'cuda' if torch.cuda.is_available() else 'cpu'
print(DEVICE)

train_dataset = datasets.MNIST(root="./dataset", train=True, download=True, transform=transforms.ToTensor())
test_dataset = datasets.MNIST(root="./dataset", train=False, download=True, transform=transforms.ToTensor())

def compute_accuracy(model, data_loader, device):
    
    with torch.no_grad():

        corr_pred, num_samples = 0,0

        for batch_idx,(features, targets) in enumerate(data_loader):
            features = features.to(device)
            targets = targets.to(device)

            logit = model(features)
            _,predicted_label = torch.max(logit,1)
            num_samples += targets.size(0)
            corr_pred += (predicted_label == targets).sum()
        return float(corr_pred)/num_samples * 100


@hydra.main(version_base=None, config_path="conf", config_name="config")
def train(cfg: DictConfig) -> float:
    print(OmegaConf.to_yaml(cfg))
    
    print(f"Training on {cfg.dataset} dataset...")
    print(f"Hyperparameters: LR={cfg.lr}, Batch Size={cfg.batch_size}")
    input_channels = 1
    num_classes = 10
    learning_rate = cfg.lr
    batch_size = cfg.batch_size
    num_epochs = cfg.epochs

    run = wandb.init(
        project="mnist model",
        group="optuna sweep",
        config=OmegaConf.to_container(cfg=cfg,resolve=True),
        reinit=True
    )

    train_loader = DataLoader(dataset=train_dataset,batch_size=batch_size,shuffle=True)
    test_loader = DataLoader(dataset=test_dataset, batch_size=batch_size, shuffle=True)

    model = MNIST_classifier(inp_channel=input_channels, num_classes=num_classes)

    # # checking the dimension are perfect with random value
    # x = torch.randn(1, 1, 28, 28)
    # print(model(x).shape)

    model = model.to(device=DEVICE)
    optimizer = optim.Adam(model.parameters(), lr=learning_rate)
    loss_fn = nn.CrossEntropyLoss()

    train_acc_list = []
    for epoch in range(num_epochs):
        losses = []
        model.train()

        for batch_idx, (features, targets) in enumerate(train_loader):
            features = features.to(DEVICE)
            targets = targets.to(DEVICE)

            logits = model(features)
            loss = loss_fn(logits, targets)
            optimizer.zero_grad()

            loss.backward()
            optimizer.step()

            losses.append(loss.item())
        
        train_loss = (sum(losses)/len(losses))
        print(f"{epoch+1}/{num_epochs} epoch | loss = {train_loss:.4f}")

        model.eval()
        with torch.no_grad():
            train_acc = compute_accuracy(model=model, data_loader=train_loader,device=DEVICE)
            print(f"Train Acc : {train_acc:.4f}")
            train_acc_list.append(train_acc)

        wandb.log({
            "epoch":epoch,
            "train/loss":train_loss,
            "train/accuracy":train_acc
        })

    
    model.eval()
    test_acc = compute_accuracy(model=model, data_loader=test_loader, device=DEVICE)
    print(f"Test Acc : {test_acc}")

    print(f"Parameters after trail : lr={cfg.lr:.4f}, batch_size={cfg.batch_size} -> Accuracy: {test_acc:.4f}")
    print("-------------------------------------------------------------------------------------------------------\n")
    torch.save(model.state_dict(), 'save-data/mnistModel.pt')
    
    run.finish()
    return test_acc



    
if __name__ == "__main__":
    train()