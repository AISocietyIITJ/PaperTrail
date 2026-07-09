import torch
import hydra
import wandb
import os
import random
import numpy as np
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
import torchvision
from torch.utils.data import DataLoader,random_split
import torchvision.datasets as dsets
import torchvision.transforms as transforms
import optuna
from omegaconf import DictConfig

#=======================================================================

def set_seed(seed=42):
    random.seed(seed)

    np.random.seed(seed)

    os.environ['PYTHON_SEED']=str(seed)

    torch.manual_seed(seed)
    torch.cuda.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)

    torch.backends.cudnn.benchmark=False
    torch.backends.cudnn.deterministic=True


set_seed(42)

#=====================================================================

batch_size=64
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

dataset= dsets.MNIST(root='datasets/', transform=transforms.ToTensor())
num_sample= len(dataset)

train_size= int(0.70*num_sample)
val_size= int(0.15*num_sample)
test_size= num_sample-train_size-val_size

train_dset,val_dset,test_dset=random_split(dataset=dataset,lengths=[train_size,val_size,test_size])

train_loader= DataLoader(dataset=train_dset,batch_size= batch_size, shuffle=True)
val_loader= DataLoader(dataset=val_dset,batch_size= batch_size, shuffle=False)
test_loader= DataLoader(dataset=test_dset,batch_size= batch_size, shuffle=False)

#===============================================================================

class Inv_Resid_block(nn.Module):
    def __init__(self,in_channels,out_channels,exp_ratio,stride,padding):
        super(Inv_Resid_block,self).__init__()
        new_dim = in_channels*exp_ratio
        self.conv_layer=nn.Sequential(
            nn.Conv2d(in_channels,new_dim,kernel_size=(1,1),stride=1),
            nn.BatchNorm2d(new_dim),
            nn.ReLU6(),
            nn.Conv2d(new_dim,new_dim,kernel_size=(3,3),stride=stride,padding=padding,groups=new_dim),
            nn.BatchNorm2d(new_dim),
            nn.ReLU6(),
            nn.Conv2d(new_dim,out_channels,kernel_size=(1,1),stride=1),
            nn.BatchNorm2d(out_channels)
        )
        self.skip= stride==1 and in_channels==out_channels

    def forward(self,x):
        identity=x
        if self.skip:
            x= identity+ self.conv_layer(x)
            return x
        else:
            return self.conv_layer(x)
        
#===========================================================================

class TaskNet(nn.Module):
    def __init__(self, in_channels=1,num_classes=10):
        super(TaskNet,self).__init__()
        
        self.conv0= nn.Sequential(nn.Conv2d(in_channels, out_channels=4,kernel_size=(3,3), stride=2,padding=(1,1)) ,
                                  nn.BatchNorm2d(4),
                                  nn.ReLU())
        
        self.conv1= Inv_Resid_block(4,8,1,1,1)

        self.conv2=Inv_Resid_block(8,16,4,2,1)

        self.conv3=Inv_Resid_block(16,32,4,1,1)
        
        self.conv4=nn.Sequential(
            nn.Conv2d(32,out_channels=48,kernel_size=1,stride=1,padding=0),
            nn.BatchNorm2d(48),
            nn.ReLU6()
        )
        self.avgpool=nn.AdaptiveAvgPool2d(1)
        self.fc=nn.Sequential(
            nn.Linear(48,num_classes),
            nn.Dropout(p=0.2)
        )

    def forward(self,x):
        x=self.conv0(x)

        x=self.conv1(x)

        x=self.conv2(x)

        x=self.conv3(x)

        x=self.conv4(x)

        x=self.avgpool(x)

        x= x.reshape(x.shape[0],-1)
        x=self.fc(x)  

        return x    

#===========================================================================

def create_objective(cfg):  
    def objective(trial):
        lr = trial.suggest_float("lr",cfg.optuna.min_lr,cfg.optuna.max_lr,log=True)
        num_epochs = trial.suggest_int("num_epochs",cfg.optuna.min_epochs,cfg.optuna.max_epochs)

        model=TaskNet().to(device=device)

        optimizer= optim.Adam(model.parameters(),lr=lr)
        loss_fn=nn. CrossEntropyLoss()

        for epoch in range(num_epochs):
            model.train()
            for batch_idx, (data, targets) in enumerate(train_loader):
                data= data.to(device)
                targets= targets.to(device)


                logits= model(data)
                loss = loss_fn(logits, targets)

                optimizer.zero_grad()
                loss.backward()
                optimizer.step()

        num_correct= 0
        num_samples=0
        model.eval()

        with torch.no_grad(): 
            for x,y in val_loader:
                x = x.to(device)
                y = y.to(device)


                x1 = model(x)
                _, predictions= x1.max(1)
                num_correct += (predictions==y).sum().item()
                num_samples +=predictions.size(0)

            accuracy= float(num_correct)/float(num_samples)*100

        return accuracy
    
    return objective

#===========================================================================

@hydra.main(version_base=None, config_path="config", config_name="config")
def main(cfg: DictConfig) -> None:

    study= optuna.create_study(direction="maximize", pruner=optuna.pruners.MedianPruner(n_startup_trials=5,n_warmup_steps=3))
    study.optimize(create_objective(cfg),n_trials=cfg.optuna.n_trials)

    lr= study.best_params["lr"]
    num_epochs= study.best_params["num_epochs"]


    run = wandb.init(
        entity=cfg.wandb.entity,
        project="Logging_for_task1",
        config={
            "learning_rate":lr,
            "architecture":cfg.wandb.architecture,
            "dataset": cfg.wandb.dataset,
            "epochs":num_epochs 
        }
    )

    model= TaskNet().to(device=device)

    loss_fn= nn.CrossEntropyLoss()
    optimizer= optim.Adam(model.parameters(),lr=lr)

    step=0

    for epoch in range(num_epochs):
        model.train()
        for batch_idx, (data, targets) in enumerate(train_loader):
            data= data.to(device)
            targets= targets.to(device)


            logits= model(data)
            loss = loss_fn(logits, targets)

            optimizer.zero_grad()

            loss.backward()

            optimizer.step()
            
            wandb.log({
                "batch_loss_per_epoch": loss.item()
            }, step = step)

            step+=1

        model.eval()
        num_correct=0
        total=0


        with torch.no_grad():
            for x,y in test_loader:
                x = x.to(device)
                y = y.to(device)


                x1 = model(x)
                _, predictions= x1.max(1)
                num_correct += (predictions==y).sum().item()
                total+=predictions.size(0)

        accuracy= float(num_correct)/float(total)*100

        wandb.log({
            "epoch": epoch,
            "Acc_per_epoch": accuracy
        }, step=step)

        print(f"Epoch {epoch} complete. Accuracy: {accuracy:.2f}%")

    wandb.finish()

#===========================================================================
    
    total_params= sum(p.numel() for p in model.parameters())
    print (f"Total parameters:{total_params}")
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"Trainable parameters: {trainable_params}")
    
#===========================================================================

if __name__ == "__main__":
    main()




