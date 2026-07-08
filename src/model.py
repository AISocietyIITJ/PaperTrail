import torch
import torch.nn as nn
from torchinfo import summary


class MNIST(nn.Module):
    def __init__(self, in_channels, hidden_channels_1, hidden_channels_2, num_classes):
        super(MNIST, self).__init__()
        self.features = nn.Sequential(
            nn.Conv2d(in_channels, hidden_channels_1, kernel_size=3, padding=1),
            nn.BatchNorm2d(hidden_channels_1),
            nn.ReLU(),
            nn.MaxPool2d(2),
            nn.Conv2d(
                hidden_channels_1,
                hidden_channels_1,
                kernel_size=3,
                padding=1,
                groups=hidden_channels_1,
            ),
            nn.Conv2d(
                hidden_channels_1,
                hidden_channels_2,
                kernel_size=1,
            ),
            nn.BatchNorm2d(hidden_channels_2),
            nn.ReLU(),
            nn.MaxPool2d(2),
        )

        self.classifier = nn.Sequential(
            nn.Flatten(), nn.Linear(hidden_channels_2 * 7 * 7, num_classes)
        )

    def forward(self, x):
        x = self.features(x)
        x = self.classifier(x)
        return x


if __name__ == "__main__":
    model = MNIST(1, 8, 16, 10)

    summary(model, input_size=(1, 1, 28, 28))
