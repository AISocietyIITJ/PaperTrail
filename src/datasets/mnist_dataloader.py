from torch.utils.data import DataLoader
from torchvision import datasets, transforms

def get_mnist_loaders(data_dir="./data", batch_size=64):
    transform = transforms.Compose([transforms.ToTensor()])
    
    train_dataset = datasets.MNIST(root=data_dir, train=True, download=True, transform=transform)
    test_dataset = datasets.MNIST(root=data_dir, train=False, download=True, transform=transform)
    
    train_loader = DataLoader(dataset=train_dataset, batch_size=batch_size, shuffle=True)
    test_loader = DataLoader(dataset=test_dataset, batch_size=batch_size, shuffle=False)
    
    return train_loader, test_loader
