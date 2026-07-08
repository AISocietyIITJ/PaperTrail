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
import time



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
    


DEVICE = 'cuda' if torch.cuda.is_available() else 'cpu'
print(DEVICE)

train_dataset = datasets.MNIST(root="/dataset", train=True, download=True, transform=transforms.ToTensor())
test_dataset = datasets.MNIST(root="/dataset", train=False, download=True, transform=transforms.ToTensor())



@hydra.main(version_base=None, config_path="conf", config_name="config")
def train(cfg: DictConfig) -> None:
    print(OmegaConf.to_yaml(cfg))
    
    print(f"Training on {cfg.dataset} dataset...")
    print(f"Hyperparameters: LR={cfg.lr}, Batch Size={cfg.batch_size}")
    input_channels = 1
    num_classes = 10
    learning_rate = cfg.lr
    batch_size = cfg.batch_size
    num_epochs = 10

    train_loader = DataLoader(dataset=train_dataset,batch_size=batch_size,shuffle=True)
    test_loader = DataLoader(dataset=test_dataset, batch_size=batch_size, shuffle=True)

    model = MNIST_classifier(inp_channel=1, num_classes=10)

    # # checking the dimension are perfect with random value
    x = torch.randn(1, 1, 28, 28)
    print(model(x).shape)

    model = model.to(device=DEVICE)
    optimizer = optim.Adam(model.parameters(), lr=learning_rate)
    loss_fn = nn.CrossEntropyLoss()

    start_time = time.time()
    train_acc_list, valid_acc_list = [], []
    for epoch in range(num_epochs):
        losses = []
        model.train()

        for batch_idx, (features, targets) in enumerate(train_loader):
            features = features.to(DEVICE)
            targets = targets.ti(DEVICE)

            logits = model(features)
            loss = loss_fn(logits, targets)
            optimizer.zero_grad()

            loss.backward()
            optimizer.step()

            losses.append(loss.item())
        
        print(f"{epoch+1}/{num_epochs} epoch | loss = {(sum(losses)/len(losses)):.4f}")


    


    
if __name__ == "__main__":
    train()