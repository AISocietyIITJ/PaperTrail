import torch
import torch.nn as nn
from torchinfo import summary
import torch.nn.functional as F


class MNIST_classifier(nn.Module):
    def __init__(self,inp_channel=1, num_classes=10):
        super(MNIST_classifier, self).__init__()
        self.conv1=nn.Conv2d(in_channels=inp_channel,out_channels=8,kernel_size=(3,3),stride=(1,1),padding=(1,1))
        self.pool = nn.MaxPool2d(kernel_size=(2,2), stride=(2,2))
        self.conv2=nn.Conv2d(in_channels=8, out_channels=16, kernel_size=(3,3), stride=(1,1), padding=(1,1))
        self.fc = nn.Linear(16*7*7,num_classes)
        self.dropout = nn.Dropout(p=0.3)

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