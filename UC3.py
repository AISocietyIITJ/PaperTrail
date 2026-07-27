import torch
from adapters import AutoAdapterModel
from transformers import AutoTokenizer
from Embed_gen import total_embeddings

query=input("Enter query:")

model= AutoAdapterModel.from_pretrained("allenai/specter2_base")
tokenizer= AutoTokenizer.from_pretrained("allenai/specter2_base")

model.load_adapter("allenai/specter2_adhoc_query", source="hf", set_activ=True)

tokens= tokenizer(text=query,padding=True, return_tensors="pt")

output= model(**tokens)

A=output.last_hidden_state[:,0,:]
embedding= A.detach().cpu()

paper_embeddings=torch.tensor(total_embeddings).reshape(-1,768)

print(embedding.shape)
print(paper_embeddings.shape)

distances= torch.mm(embedding,paper_embeddings.t())

top_n=3

recommended_indices= torch.topk(distances, k=top_n, dim=1, largest=True)[1]

recommended_embeddings= paper_embeddings[recommended_indices].reshape(-1,768)
print(recommended_embeddings.shape)


