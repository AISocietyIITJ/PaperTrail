import pandas as pd
import torch
from adapters import AutoAdapterModel
from transformers import AutoTokenizer, DataCollatorWithPadding
from torch.utils.data import DataLoader
import numpy as np
import configz
from UC3 import compute_token,compute_output
import csv

def load_dataset(filename='arXiv_scientific_dataset.csv'):
    dataset= pd.read_csv(filename, engine="python", quoting=csv.QUOTE_NONE, on_bad_lines='skip')

    return dataset

def create_loader(tokenizer,dataset):
    text_list= (dataset['title'].fillna("")+ " " + tokenizer.sep_token + " " + dataset['summary'].fillna("")).astype(str).tolist()
    text_list_refined=[i.strip() for i in text_list if i.strip() !="[SEP]"]

    Loader= DataLoader(dataset=text_list_refined,batch_size=64,shuffle=False,drop_last=False,pin_memory=True, num_workers=2,collate_fn=lambda batch:compute_token(tokenizer,batch))

    return Loader

def create_paper_embeds(model, loader,dataset):
    fp= np.memmap("paper_embeddings.dat", dtype='float32', mode='w+', shape=(len(dataset),768))
    idx=0   
    with torch.inference_mode():  
        for batch in loader:
            batch_gp={}
            for key,value in batch.items():
                batch_gp[key]= value.to('cuda', non_blocking=True)

            batch=batch_gp

            with torch.autocast(device_type='cuda'):
                output= compute_output(model,batch)

            embeddings= output.last_hidden_state[:,0,:].detach().cpu().numpy().astype('float32')
            batch_size= len(embeddings)
            fp[idx:idx+batch_size]= embeddings
            idx+=batch_size

    fp.flush()


def main():
    model= AutoAdapterModel.from_pretrained('allenai/specter2_base')
    model.load_adapter('allenai/specter2', source ='hf', set_active=True)
    tokenizer= AutoTokenizer.from_pretrained('allenai/specter2_base', use_fast=True)

    dataset= load_dataset('arXiv_scientific_dataset.csv')
    loader= create_loader(tokenizer,dataset)
    model.eval()
    model.to('cuda')

    create_paper_embeds(model,loader,dataset)

if __name__=="__main__":
    main()
    




