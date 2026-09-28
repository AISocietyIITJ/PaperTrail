import json
import math
import numpy as np

def mrr(candidate_grades,k,relevance_threshold=2):
    for idx,candidate_grade in enumerate(candidate_grades):
        if candidate_grade >= relevance_threshold:
            return 1/(idx+1)
        return 0.0

def dcg(relevance_scores,k):
    relevance_scores=relevance_scores[:k]
    dcg=0
    for idx,rel in enumerate(relevance_scores):
        z= (2**rel - 1) / math.log2(idx + 2)
        dcg=dcg+z

    return dcg

def ndcg(candidate_grades,k):
    candidate_grades=candidate_grades[:k]
    dcg_score= dcg(candidate_grades,k)

    sorted_candidate_grades= sorted(candidate_grades,reverse=True)
    idcg_score= dcg(sorted_candidate_grades,k)

    return dcg_score/idcg_score if idcg_score>0 else 0.0

def evaluation(filename):
    with open(filename,"r",encoding="utf-8") as f:
        queries= json.load(f)

    ndcg_5_list=[]
    ndcg_10_list=[]
    mrr_10_list=[]
    for i,obj in enumerate(queries):
        candidates= obj['candidates']

        sorted_candidates=sorted(candidates,key= lambda x: x['rank'])

        sorted_grades= [int(candidate['llm_grade']['llm_grade']) for candidate in sorted_candidates]

        ndcg_5_list.append(ndcg(sorted_grades,k=5))
        ndcg_10_list.append(ndcg(sorted_grades,k=10))
        mrr_10_list.append(mrr(sorted_grades,k=10))

    return {
        "Model":"BGE_Reranker_large",
        "Total Queries Evaluated": len(queries),
        "NDCG@5": float(np.mean(ndcg_5_list)),
        "NDCG@10": float(np.mean(ndcg_10_list)),
        "MRR@10": float(np.mean(mrr_10_list)),
    }


if __name__ == "__main__":
    results = evaluation("benchmark_llm_graded_bge_large.json")

    print("\n" + "=" * 35)
    print("      RERANKER EVALUATION METRICS    ")
    print("=" * 35)
    for metric, score in results.items():
        if isinstance(score, float):
            print(f"{metric:<23}: {score:.4f}")
        else:
            print(f"{metric:<23}: {score}")
    print("=" * 35 + "\n")