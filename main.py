"""Backend-facing functions for the three PaperTrail use cases."""
import argparse
import os
import pandas as pd
from pinecone import Pinecone
from src.config import PINECONE_API_KEY
from sentence_transformers import SentenceTransformer
import yaml
import torch,gc

from src.usecase_2.embedding.generate_alias import generate_phrase
from src.usecase_2.embedding.gen_alias_new import generate_domain_aliases
from src.usecase_2.embedding.gen_interest_no_alias import gen_res_emb_ingestion
from src.usecase_2.embedding.generate_embedding_prof import gen_prof_emb_ingestion
from src.usecase_2.ingestion.load_professor import ingest_proff_connect_edges
from src.usecase_2.ingestion.load_research_node import ingest_research_node
from src.usecase_1.build_graph import assemble_graph
from src.usecase_1.candidate_edges import generate_candidate_edges
from src.usecase_1.data_prep import prepare_dataset as prepare_reading_path_data
from src.usecase_1.direction import assign_edge_directions
from src.usecase_1.embed import generate_embeddings as generate_reading_path_embeddings
from src.usecase_1.query_pipeline import generate_reading_path as generate_structured_path
from src.usecase_2.local_llm.testing import get_interest_topics
from src.usecase_2.utils.get_prof_info import query_graph_db
from src.usecase_2.utils.vec_query_search import search_vector_db
from src.usecase_2.utils.parsing_resume import extract_text_from_pdf
from src.usecase_1.ingest_neo4j import ingest_to_neo4j as ingest_reading_path_to_neo4j
from src.usecase_1.precompute_costs import run_precompute as precompute_reading_path_costs
from src.usecase_3.document_setter import docs_setter
from src.usecase_3.reranker_fin import return_reranked_docs
from src.usecase_3.user_query_rephrasing import rephrase_user_query

def generate_reading_path_pipeline(config_path="config.yaml"):
    gc.collect()
    torch.cuda.empty_cache()
    """Run the complete data prep and graph building pipeline."""
    
    prepare_reading_path_data(config_path)
    generate_reading_path_embeddings(config_path)
    generate_candidate_edges(config_path)
    assign_edge_directions(config_path)
    assemble_graph(config_path)

def get_reading_path(query: str, hops: int = 2, config_path="config.yaml"):
    """Use case 1: return a JSON-ready foundational reading path."""
    return generate_structured_path(query, hops=hops)


def setup_academic_profiles_pipeline():
    """Use case 2: run setup, generating aliases, embeddings, and ingesting nodes/edges."""

    print("\n" + "=" * 60)
    print("PaperTrail Academic Profiles Setup (Use Case 2)")
    print("=" * 60)

    print("\n[1/5] Generating phrase aliases...")
    # generate_phrase()
    generate_domain_aliases()

    print("[2/5] Generating research embeddings...")
    gen_res_emb_ingestion()

    print("[3/5] Generating professor embeddings...")
    # gen_prof_emb_ingestion()

    print("[4/5] Ingesting research nodes...")
    ingest_research_node()

    print("[5/5] Ingesting professor connections...")
    ingest_proff_connect_edges()

    print("\nSetup complete.")


def find_academic_profiles(
    query: str,
    resume_path: str | None = None,
    resume_text: str | None = None,
):
    """Use case 2: return professors matching a query and optional resume data.

    ``resume_path`` refers to a file on the server.  API clients can instead
    send ``resume_text`` (or omit both) so the query works without access to
    the server filesystem.
    """
    
    if resume_text is None:
        resume_text = extract_text_from_pdf(resume_path) if resume_path else ""

    interests = get_interest_topics(query, resume_text)
    if interests is None:
        return None
    if not interests:
        # The local LLM can occasionally omit its expected JSON fields.  The
        # request query is still a useful semantic-search input, so do not
        # discard an otherwise valid API request in that case.
        interests = query.strip()
        if not interests:
            return {"interests": None, "interest_ids": [], "professors": []}

    interest_ids = search_vector_db(interests)
    return {
        "interests": interests,
        "interest_ids": interest_ids,
        "professors": query_graph_db(interest_ids),
    }


def recommend_papers(query:str, top_n: int = 5, config_path="config.yaml"):
    """Use case 3: return the top matching paper records for a query directly from Pinecone."""
    if top_n < 1:
        raise ValueError("top_n must be at least 1")

    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
        
    model_name = config["embedding"]["model_name"]
    pinecone_index = config["embedding"]["pinecone_index"]

    print(f"Embedding query using {model_name}...")
    global _main_embedding_model
    if '_main_embedding_model' not in globals() or _main_embedding_model is None:
        _main_embedding_model = SentenceTransformer(model_name)

    print(query)
    query_fin= rephrase_user_query(query)
    print(query_fin)
    if(query.lower()==query_fin.lower()):return []

    query_vector = _main_embedding_model.encode([query_fin], normalize_embeddings=True)[0].tolist()

    print(f"Querying top recommendations from Pinecone index '{pinecone_index}'...")
    pc = Pinecone(api_key=PINECONE_API_KEY)
    index = pc.Index(pinecone_index)
    
    # Query pinecone with candidate buffer to account for missing/filtered nodes
    fetch_k = max(top_n * 3, 30)
    search_res = index.query(vector=query_vector, top_k=fetch_k, include_metadata=True)

    final_formatted_docs= [l[1] for l in docs_setter(search_res.matches)]
    titles=[l[0] for l in docs_setter(search_res.matches)]
    abstracts=[l[2] for l in docs_setter(search_res.matches)]

    top_n_indices,top_n_reranked_docs,reranked_scores= return_reranked_docs(query_fin,final_formatted_docs)

    print(f"Length of recommended docs:{len(top_n_indices)}")

    recommended_doc_titles= [titles[i] for i in top_n_indices]
    recommended_doc_abstracts=[abstracts[i] for i in top_n_indices]

    print(f"Length of recommended titles:{len(recommended_doc_titles)}")

    sim_scores= [next((match.score for match in search_res.matches if ((match.metadata is not None) and (match.metadata.get('title') == title))),0.0) for title in recommended_doc_titles]

    title_to_score={
            title : sc

            for (title,sc) in zip(recommended_doc_titles,sim_scores)
    }
    filtered_results = [(score,idx,doc) for score,idx,doc in zip(reranked_scores,top_n_indices,top_n_reranked_docs) if score >=0.001]

    if filtered_results:
        reranked_scores,top_n_indices,top_n_reranked_docs=map(list,zip(*filtered_results))
    else:
        reranked_scores,top_n_indices,top_n_reranked_docs=[],[],[]
    
    results = []

    if len(reranked_scores)!=0:
        for title, abstract,rr_score in zip(recommended_doc_titles, recommended_doc_abstracts,reranked_scores):
            results.append({
                "score": float(title_to_score[title]),
                "title": str(title),
                "abstract": str(abstract),
                "reranked_score": float(rr_score)
            })
            
    return results



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PaperTrail Unified API")
    parser.add_argument("--run-reading-pipeline", action="store_true", help="Execute complete dataset prep and graph building")
    parser.add_argument("--ingest-reading-neo4j", action="store_true", help="Push generated pipeline data into Neo4j")
    parser.add_argument("--precompute-costs", action="store_true", help="Precompute NEWST node/edge costs in Neo4j")
    parser.add_argument("--query-reading", type=str, help="Generate an ordered foundational reading path from Neo4j")
    parser.add_argument("--hops", type=int, default=2, help="Number of hops for reading path graph traversal")
    parser.add_argument("--recommend-papers", type=str, help="Execute Use Case 3 to find top N most relevant papers for a query")
    parser.add_argument("--top-n", type=int, default=5, help="Number of papers to recommend for Use Case 3")
    parser.add_argument("--run-academic-profiles-setup", action="store_true", help="Execute Use Case 2 setup (alias, embeddings, graph ingestion)")
    parser.add_argument("--get-proffesors", action="store_true", help="Execute Use Case 2 setup (alias, embeddings, graph ingestion)")
    parser.add_argument("--config", default="config.yaml", help="Path to config yaml file")
    
    args = parser.parse_args()

    if args.run_reading_pipeline:
        print("=== RUNNING PAPERTRAIL GRAPH GENERATION PIPELINE ===")
        generate_reading_path_pipeline(args.config)
        print("=== PIPELINE RUN COMPLETE ===")

    elif args.ingest_reading_neo4j:
        print("=== INGESTING DATA INTO NEO4J ===")
        ingest_reading_path_to_neo4j(args.config)

    elif args.precompute_costs:
        print("=== PRECOMPUTING NEWST COSTS IN NEO4J ===")
        precompute_reading_path_costs(config_path=args.config)
        
    elif args.query_reading:
        print(f"\n=================== NEO4J READING PATH FOR: '{args.query_reading}' ===================")
        # The function itself prints the steps, but we can also capture the returned list
        path = get_reading_path(args.query_reading, args.hops, args.config)
        if not path:
            print("No matching path found in domain subgraph.")
        print("===================================================================================\n")
    elif args.run_academic_profiles_setup:
        setup_academic_profiles_pipeline()

    elif args.get_proffesors:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        resume_path = os.path.join(script_dir, "data/Resume_HerilNMistry.pdf")
        result = find_academic_profiles(query="Suggest me the proffs CV", resume_path=resume_path)
        print(f"Interests: {result['interests']}")
        print(f"Interest IDs: {result['interest_ids']}")
        print("-"*60)
        if not result["professors"]:
            print("No matching professors found.")
        else:
            for pro in result["professors"]:
                for key, value in pro.items():
                    print(f"  {key}: {value}")
                print("-"*60)
                
    elif args.recommend_papers:
        print(f"\n=================== PAPER RECOMMENDATIONS FOR: '{args.recommend_papers}' ===================")
        recs = recommend_papers(args.recommend_papers, top_n=args.top_n, config_path=args.config)
        if (len(recs)!=0):
            for i, rec in enumerate(recs, 1):
                print(f"\n[{i}] {rec['title']}")
                print(f"Similarity Score: {rec['score']:.4f}")
                # print a snippet of abstract
                abstract_snippet = (rec['abstract'][:200] + '...') if len(str(rec['abstract'])) > 200 else rec['abstract']
                print(f"Abstract: {abstract_snippet}")
                print(f"Reranked_score: {rec['reranked_score']}")
            print("\n=========================================================================================\n")
        else:
            print("Papers relevant to query are not found")
            print("\n=========================================================================================\n")
    else:
        parser.print_help()

# Date: {str(rec['published_date']).split('T')[0]} |