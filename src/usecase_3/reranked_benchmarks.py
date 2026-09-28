import json
import yaml
from src.usecase_3.reranker_fin import return_reranked_docs
from src.usecase_3.document_setter import docs_setter_2


def main():
    with open('benchmark_dataset_for_llm.json', "r", encoding="utf-8") as f:
        candidates_per_query=json.load(f)

    rereanked_benchmarks=[]

    for idx,obj in enumerate(candidates_per_query,1):
        query=obj["query"]
        target_paper_id= obj['target_paper_id']
        candidates= obj["candidates"]

        modified_candidates=[sublist[1] for sublist in docs_setter_2(candidates)]
        if not modified_candidates:
            print(f"Skipping query_id {obj['query_id']} - no candidates available.")
            obj["candidates"] = []
            continue
        
        # reranked_docs= return_reranked_docs(query,modified_candidates,50)[1]
        reranked_indices,_,reranked_scores=return_reranked_docs(query,modified_candidates,50)
       
        for new_rank, (og_idx, score) in enumerate(zip(reranked_indices, reranked_scores), start=1):
            candidates[og_idx]["rank"] = new_rank
            candidates[og_idx]["reranked_score"] = score

            
        rereanked_benchmarks.append({
            "query_id": obj['query_id'],
            "target_paper_id": target_paper_id,
            "query": query,
            "candidates": candidates
        })

    
    with open("benchmark_reranked_jina.json","w",encoding="utf-8") as f:
        json.dump(rereanked_benchmarks,f,indent=2)


        
if __name__=="__main__":
    main()



    

