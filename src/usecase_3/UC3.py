import torch
from adapters import AutoAdapterModel
from transformers import AutoTokenizer
import numpy as np

def compute_token(tokenizer, query, **kwargs):        
    tokens= tokenizer(text=query,padding=True, truncation=True,return_tensors="pt",max_length=512, **kwargs)
    return tokens

def compute_output(model,tokens):
    output=model(**tokens)

    return output

def user_query_emb(output):

    A=output.last_hidden_state[:,0,:]
    embedding= A.detach().cpu()

    return embedding

def read_paper_embeds():
    mmap= torch.tensor(np.memmap("paper_embeddings.dat", dtype='float32', mode='r'))
    paper_embeddings= torch.as_tensor(mmap).reshape(-1,768)
    return paper_embeddings

def recommend_embeddings(user_embed, paper_embeds, top_n, device):
    user_embed=user_embed.to(device)
    paper_embeds=paper_embeds.to(device)

    distances= torch.mm(user_embed,paper_embeds.t())
    recommended_indices= torch.topk(distances, k=top_n, dim=1, largest=True)[1]
    recommended_embeddings= paper_embeds[recommended_indices].reshape(-1,768)

    return recommended_embeddings

def get_recommendations():
    query=input("Enter query:")
    top_n= int(input("Enter top_n"))

    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model= AutoAdapterModel.from_pretrained("allenai/specter2_base")
    tokenizer= AutoTokenizer.from_pretrained("allenai/specter2_base", use_fast=True)

    model.load_adapter("allenai/specter2_adhoc_query", source="hf", set_active=True)

    model.to(device)
    model.eval()

    tokens=compute_token(tokenizer,query).to(device)
    with torch.inference_mode():
        output= compute_output(model,tokens)
        embedding= user_query_emb(output)

    paper_embeddings= read_paper_embeds()
    recommended_embeddings= recommend_embeddings(embedding,paper_embeddings,top_n,device)

    return recommended_embeddings

if __name__=="__main__":
    recommended_embeddings_fin= get_recommendations()




