import json
import random
from ollama import Client
from src.config import REPHRASING_API_KEY,PINECONE_API_KEY
from pinecone import Pinecone
from src.usecase_3.llm_rephrase_prompt import query_rec_prompt


def sampling_papers():
    pc = Pinecone(api_key=PINECONE_API_KEY)
    index = pc.Index('papertrail-papers')

    id_list=[]

    for v in index.list_paginated().vectors:
        vec_id = v.get("id") if isinstance(v, dict) else v.id
        id_list.append(vec_id)

    random.seed(42)
    final_id_list= random.sample(id_list,20)

    search_res = index.fetch(ids=final_id_list)

    sampled_papers=[]

    for paper_id, vector_data in search_res.vectors.items():
        metadata = vector_data.metadata
        sampled_papers.append({
            "paper_id": paper_id,
            "title": metadata.get("title", ""),
            "abstract": metadata.get("abstract", "")
        })

    return sampled_papers

client = Client(
    host="https://ollama.com",
    headers={"Authorization": f"Bearer {REPHRASING_API_KEY}"}
)

def query_generator_fn(content_text):
    response= client.chat(
            model='gemma4',
            format='json',
            messages=[
                {
                    "role":"system",
                    "content": query_rec_prompt
                },
                {
                    "role":"user",
                    "content": content_text
                }
            ]
        )
    
    output=response.message.content.strip()
    cleaned_response = output.strip()
    if cleaned_response.startswith("```json"):
        cleaned_response = cleaned_response[7:]
    if cleaned_response.startswith("```"):
        cleaned_response = cleaned_response[3:]
    if cleaned_response.endswith("```"):
        cleaned_response = cleaned_response[:-3]

    cleaned_response = cleaned_response.strip()
    cleaned_response = cleaned_response.replace("\\n", "\n")

    final_response= json.loads(cleaned_response)
    return final_response


def main():
    sampled_papers= sampling_papers()
    sampled_paper_queries=[]
    for paper in sampled_papers:
        content_text = f"paper_id:{paper['paper_id']}\nTitle: {paper['title']}\nAbstract: {paper['abstract']}"
        query=query_generator_fn(content_text)
        sampled_paper_queries.append(query)

    print(json.dumps(sampled_paper_queries[:5],indent=2))

    with open("benchmark_queries.json","w",encoding="utf-8") as f:
        json.dump(sampled_paper_queries,f,indent=2)

if __name__=="__main__":
    main()