import pandas as pd
import torch
from adapters import AutoAdapterModel
from transformers import AutoTokenizer, DataCollatorWithPadding
from torch.utils.data import DataLoader
import numpy as np
import configz
dataset= pd.read_csv('arXiv_scientific_dataset.csv', )
act_dataset= dataset.head(32768)


tokenizer= AutoTokenizer.from_pretrained('allenai/specter2_base')
model= AutoAdapterModel.from_pretrained('allenai/specter2_base')
model.load_adapter('allenai/specter2', source ='hf', set_active=True)


text_list= (act_dataset['title']+ " " + tokenizer.sep_token + " " + act_dataset['summary']).tolist()


Loader= DataLoader(dataset=text_list,batch_size=64,shuffle=True)

model.eval()
model.to('cuda')

total_embeddings=[]
with torch.inference_mode():
    for batch in Loader:
        input= tokenizer(text= list(batch),padding=True,return_tensors="pt",truncation=True, max_length=512).to('cuda')

        with torch.autocast(device_type='cuda'):
            output= model(**input)

        embeddings= output.last_hidden_state[:,0,:].detach().cpu().tolist()
        total_embeddings.append(embeddings)






