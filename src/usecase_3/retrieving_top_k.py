from ollama import Client
from src.config import REPHRASING_API_KEY, PINECONE_API_KEY
from pinecone import Pinecone
import json
import yaml
import torch

with open("config.yaml", "r") as file:
    data = yaml.safe_load(file)

# local_embed_client = Client(host="http://localhost:11434")

# client = Client(
#     host="https://ollama.com",
#     headers={"Authorization": f"Bearer {REPHRASING_API_KEY}"}
# )

from adapters import AutoAdapterModel
from transformers import AutoTokenizer

def compute_token(tokenizer, query, **kwargs):        
    tokens= tokenizer(text=query,padding=True, truncation=True,return_tensors="pt",max_length=512, **kwargs)
    return tokens

def query_emb(model,tokens):
    with torch.no_grad():
        tokens = {k: v.to(model.device) for k, v in tokens.items()}
        output=model(**tokens)

    A=output.last_hidden_state[:,0,:]
    embedding= A[0].detach().cpu()

    return embedding

def retrieve_top_k(embedding,top_k=50, index_name=data['embedding']['pinecone_index']):
    pc = Pinecone(api_key=PINECONE_API_KEY)
    index = pc.Index(index_name)

    results= index.query(vector=embedding,top_k=top_k,include_metadata=True, namespace='__default__')

    candidates=[]

    for match in results.matches:
        candidates.append({
            "paper_id":match.id,
            "title":match.metadata.get('title'),
            "abstract":match.metadata.get('abstract'),
            "score": match.score
        })

    return candidates

def main():
    with open("benchmark_queries.json","r",encoding ="utf-8") as f:
        queries=json.load(f)

    retrieved_benchmark_dataset=[]

    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model= AutoAdapterModel.from_pretrained("allenai/specter2_base")
    tokenizer= AutoTokenizer.from_pretrained("allenai/specter2_base", use_fast=True)
    model.load_adapter("allenai/specter2_adhoc_query", source="hf", set_active=True)   

    model.eval() 

    # query="long-term temporal convolutions LTC-CNN action recognition UCF101 HMDB51"
    for idx, obj in enumerate(queries,1):
        query= obj['query']
        target_paper_id=obj['paper_id']

        tokens= compute_token(tokenizer,query)
        query_vector=query_emb(model,tokens).numpy().tolist()

        candidates=retrieve_top_k(query_vector)

        retrieved_record = {
                "query_id": f"q_{idx:03d}",
                "target_paper_id": target_paper_id,
                "query": query,
                "candidates": candidates
            }

        retrieved_benchmark_dataset.append(retrieved_record)

    with open("benchmark_dataset_for_llm.json","w",encoding="utf-8") as f:
        json.dump(retrieved_benchmark_dataset,f,indent=2)

# Quick test to inspect returned metadata keys
    # output= compute_output(model,compute_token(tokenizer,query))
    # query_vector=query_emb(output).numpy().tolist()

    # pc = Pinecone(api_key=PINECONE_API_KEY)
    # index = pc.Index('papertrail-papers')

    # test_res = index.query(vector=query_vector, top_k=1, include_metadata=True)

    # if test_res.matches:
    #     print("MATCH ID:", test_res.matches[0].id)
    #     print("METADATA OBJECT:", test_res.matches[0].metadata)
    # else:
    #     print("No matches returned.")

if __name__=="__main__":
    main()