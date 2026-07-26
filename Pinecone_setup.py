import configz
from pinecone import Pinecone,ServerlessSpec
import time
import pandas as pd
import random
from torch.utils.data import DataLoader
from Embed_gen import dataset
from UC3 import recommended_embeddings, paper_embeddings

pc= Pinecone(api_key=configz.pc_api)
index_name="paper-embeds"

if pc.has_index(name=index_name):
    pc.delete_index(name=index_name)

pc.create_index(name=index_name,dimension=768,spec=ServerlessSpec(cloud="aws", region="us-east-1"))

description = pc.describe_index(name=index_name)

index= pc.Index(host=description.host)
random.seed(42)

paper_embeddings_list= paper_embeddings.tolist()

records=[
    {
        "id":str(i),
        "values":vec.tolist() if hasattr(vec, 'tolist') else list(vec),
        "metadata": {
            "title": str(t),
            "category": str(cat)
        }
    }
    for i,vec,t,cat in zip(dataset['id'],paper_embeddings_list,dataset['title'],dataset['category'])
]

batch_size=100

for i in range(0,len(records),batch_size):

    batch = records[i:i+batch_size]
    index.upsert(vectors=batch)
    while index.describe_index_stats().total_vector_count==0:
        time.sleep(1)


for i in recommended_embeddings.tolist():
    outputs= index.query(vector =i,top_k=3, include_metadata=True)

outputs_dict=outputs.to_dict()

for rec in outputs_dict['matches']:
    meta_dict= rec['metadata']
    print(meta_dict['title'])
    print(meta_dict['category'])


