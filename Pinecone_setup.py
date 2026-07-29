import configz
from pinecone import Pinecone,ServerlessSpec
import time
import pandas as pd
import random
from torch.utils.data import DataLoader
import numpy as np
from Embed_gen import load_dataset
from UC3 import read_paper_embeds, get_recommendations

def create_pc_index(index_name):

    pc= Pinecone(api_key=configz.pc_api)
    if pc.has_index(name=index_name):
        pc.delete_index(name=index_name)

    pc.create_index(name=index_name,dimension=768,spec=ServerlessSpec(cloud="aws", region="us-east-1"))

    while not pc.describe_index(index_name).status['ready']:
        time.sleep(1)

    description = pc.describe_index(name=index_name)
    index= pc.Index(host=description.host)
    random.seed(42)

    return index

def load_data_to_pc(index,batch_size,dataset,paper_embeddings):
    for i in range(0,len(paper_embeddings),batch_size):

        batch_info= dataset.iloc[i:i+batch_size]
        batch_embeds = paper_embeddings[i:i+batch_size]
        

        records= [{
            "id": f"paper_{i+idx}",
            "values":vec.tolist(),
            "metadata":{
                "title": str(title),
                "category": str(cat)                
            }
        }
        for idx,(vec,title,cat) in enumerate(zip(batch_embeds,batch_info['title'].fillna(""),batch_info['category'].fillna("")))]
        index.upsert(vectors=records)

def return_output(index,recommended_embeddings):
    all_outputs=[]
    for i in recommended_embeddings.tolist():
        output= index.query(vector =i,top_k=3, include_metadata=True)
        all_outputs.append(output.to_dict())

    
    return all_outputs

def print_results(all_outputs):
    for out_dict in all_outputs:   
        for idx,rec in enumerate(out_dict['matches']):
            meta_dict= rec['metadata']
            print(f"{idx+1}.")
            print(f"Title:{meta_dict['title']}")
            print(f"Category:{meta_dict['category']}")
            print(f"Similarity_score:{rec['score']}")

            print("--"*15)

def main():
    index= create_pc_index("paper-embeds")

    dataset= load_dataset()
    dataset_fin=dataset.dropna(axis=0, how="all", subset=['title','summary']).reset_index(drop=True)

    paper_embeddings= read_paper_embeds()

    load_data_to_pc(index,150,dataset_fin,paper_embeddings)

    recommended_embeddings_fin=get_recommendations()

    all_outputs_list= return_output(index,recommended_embeddings_fin)

    print_results(all_outputs_list)


if __name__=="__main__":
    main()
    