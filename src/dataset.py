from torch.utils.data import DataLoader
import torchvision.datasets as datasets
import torchvision.transforms as transforms

def get_dataloaders(batch_size):
    train_dataset = datasets.MNIST(root='dataset/', train=True, transform=transforms.Compose([transforms.ToTensor(),transforms.Normalize((0.1307,),(0.3081,))]), download=True)
    train_loader = DataLoader(dataset=train_dataset, batch_size=batch_size, shuffle=True)
    test_dataset = datasets.MNIST(root='dataset/', train=False, transform=transforms.Compose([transforms.ToTensor(),transforms.Normalize((0.1307,),(0.3081,))]), download=True)
    test_loader = DataLoader(dataset=test_dataset, batch_size=batch_size, shuffle=True)
    return train_loader, test_loader