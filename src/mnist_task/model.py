import torch.nn as nn


class SmallCNN(nn.Module):
    """MNIST classifier using standard and depthwise-separable convolutions to stay under 10k params."""

    def __init__(
        self,
        c1: int = 16,
        c2: int = 24,
        c3: int = 48,
        c4: int = 64,
        num_classes: int = 10,
    ):
        super().__init__()

        # Conv 1: Normal Conv, 1 -> c1
        self.conv1 = nn.Conv2d(1, c1, kernel_size=3, padding=1, bias=False)
        self.bn1 = nn.BatchNorm2d(c1)

        # Conv 2: Normal Conv, c1 -> c2 (downsample)
        self.conv2 = nn.Conv2d(c1, c2, kernel_size=3, stride=2, padding=1, bias=False)
        self.bn2 = nn.BatchNorm2d(c2)

        # Conv 3: Depthwise Separable, c2 -> c3 (downsample)
        self.conv3_dw = nn.Conv2d(
            c2, c2, kernel_size=3, stride=2, padding=1, groups=c2, bias=False
        )
        self.conv3_pw = nn.Conv2d(c2, c3, kernel_size=1, bias=False)
        self.bn3 = nn.BatchNorm2d(c3)

        # Conv 4: Depthwise Separable, c3 -> c4
        self.conv4_dw = nn.Conv2d(
            c3, c3, kernel_size=3, stride=1, padding=1, groups=c3, bias=False
        )
        self.conv4_pw = nn.Conv2d(c3, c4, kernel_size=1, bias=False)
        self.bn4 = nn.BatchNorm2d(c4)

        self.pool = nn.AdaptiveAvgPool2d(1)
        self.fc = nn.Linear(c4, num_classes)
        self.relu = nn.ReLU(inplace=True)
        self.dropout = nn.Dropout(0.1)

    def forward(self, x):
        x = self.relu(self.bn1(self.conv1(x)))
        x = self.dropout(x)
        x = self.relu(self.bn2(self.conv2(x)))
        x = self.dropout(x)

        # Conv 3: DW-separable
        x = self.conv3_dw(x)
        x = self.relu(self.bn3(self.conv3_pw(x)))
        x = self.dropout(x)

        # Conv 4: DW-separable
        x = self.conv4_dw(x)
        x = self.relu(self.bn4(self.conv4_pw(x)))

        x = self.pool(x).flatten(1)
        return self.fc(x)
