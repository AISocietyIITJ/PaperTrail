"""Backend-facing functions for the three PaperTrail use cases."""
import argparse
import os
import pandas as pd
from pinecone import Pinecone
from src.config import PINECONE_API_KEY
from sentence_transformers import SentenceTransformer
import yaml

from src.usecase_2.embedding.generate_alias import generate_phrase
from src.usecase_2.embedding.generate_embedding import gen_res_emb_ingestion
from src.usecase_2.embedding.generate_embedding_prof import gen_prof_emb_ingestion
from src.usecase_2.ingestion.load_proffesor import ingest_proff_connect_edges
from src.usecase_2.ingestion.load_reaseach_node import ingest_research_node
from src.usecase_1.build_graph import assemble_graph
from src.usecase_1.candidate_edges import generate_candidate_edges
from src.usecase_1.data_prep import prepare_dataset as prepare_reading_path_data
from src.usecase_1.direction import assign_edge_directions
from src.usecase_1.embed import generate_embeddings as generate_reading_path_embeddings
from src.usecase_1.query import generate_path_neo4j, load_neo4j_driver
from src.usecase_2.local_llm.extractor import get_interest_topics
from src.usecase_2.utils.get_prof_info import query_graph_db
from src.usecase_2.utils.vec_query_search import search_vector_db
from src.usecase_2.utils.parsing_resume import extract_text_from_pdf
from src.usecase_1.ingest_neo4j import ingest_to_neo4j as ingest_reading_path_to_neo4j

def generate_reading_path_pipeline(config_path="config.yaml"):
    """Run the complete data prep and graph building pipeline."""
    
    prepare_reading_path_data(config_path)
    generate_reading_path_embeddings(config_path)
    generate_candidate_edges(config_path)
    assign_edge_directions(config_path)
    assemble_graph(config_path)

def get_reading_path(query: str, config_path="config.yaml"):
    """Use case 1: return a JSON-ready foundational reading path."""

    config, driver, model = load_neo4j_driver(config_path)
    try:
        path = generate_path_neo4j(query, driver, model, max_hops=config["query"]["max_hops"])
        return path.to_dict(orient="records")
    finally:
        driver.close()


def setup_academic_profiles_pipeline():
    """Use case 2: run setup, generating aliases, embeddings, and ingesting nodes/edges."""
    from src.usecase_2.embedding.generate_alias import generate_phrase
    from src.usecase_2.embedding.gen_interest_no_alias import gen_res_emb_ingestion
    from src.usecase_2.embedding.generate_embedding_prof import gen_prof_emb_ingestion
    from src.usecase_2.ingestion.load_proffesor import ingest_proff_connect_edges
    from src.usecase_2.ingestion.load_reaseach_node import ingest_research_node

    print("\n" + "=" * 60)
    print("PaperTrail Academic Profiles Setup (Use Case 2)")
    print("=" * 60)

    print("\n[1/5] Generating phrase aliases...")
    generate_phrase()

    print("[2/5] Generating research embeddings...")
    gen_res_emb_ingestion()

    print("[3/5] Generating professor embeddings...")
    gen_prof_emb_ingestion()

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
    from src.usecase_2.local_llm.extractor import get_interest_topics
    from src.usecase_2.utils.get_prof_info import query_graph_db
    from src.usecase_2.utils.vec_query_search import search_vector_db
    from src.usecase_2.utils.parsing_resume import extract_text_from_pdf
    
    if resume_text is None:
        resume_text = extract_text_from_pdf(resume_path) if resume_path else ""

    interests = get_interest_topics(query, resume_text)
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


def recommend_papers(query: str, top_n: int = 5, config_path="config.yaml"):
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
    query_vector = _main_embedding_model.encode([query], normalize_embeddings=True)[0].tolist()

    print(f"Querying top {top_n} recommendations from Pinecone index '{pinecone_index}'...")
    pc = Pinecone(api_key=PINECONE_API_KEY)
    index = pc.Index(pinecone_index)
    
    # Query pinecone and fetch metadata
    # The vectors in Pinecone were ingested by usecase 1, but wait!
    # In usecase 1, we ONLY pushed vectors, not metadata!
    # Wait, earlier I discovered that `search_res.matches[0].id` is the `node_idx`.
    # Let's just fetch the matches, get their IDs, and look up the paper titles in the parquet file!
    search_res = index.query(vector=query_vector, top_k=top_n, include_metadata=False)
    
    df_papers = pd.read_parquet(config["paths"]["interim_data"])
    
    results = []
    for match in search_res.matches:
        node_idx = int(match.id)
        # Look up paper info in df
        paper_info = df_papers[df_papers["node_idx"] == node_idx].iloc[0]
        results.append({
            "score": match.score,
            "title": paper_info["title"],
            "published_date": paper_info["published_date"],
            "abstract": paper_info["abstract"],
            "arxiv_id": str(paper_info.get("arxiv_base_id", ""))
        })
        
    return results



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PaperTrail Unified API")
    parser.add_argument("--run-reading-pipeline", action="store_true", help="Execute complete dataset prep and graph building")
    parser.add_argument("--ingest-reading-neo4j", action="store_true", help="Push generated pipeline data into Neo4j")
    parser.add_argument("--query-reading", type=str, help="Generate an ordered foundational reading path from Neo4j")
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
        
    elif args.query_reading:
        path = get_reading_path(args.query_reading, args.config)
        print(f"\n=================== NEO4J READING PATH FOR: '{args.query_reading}' ===================")
        if not path:
            print("No matching path found in domain subgraph.")
        else:
            for r in path:
                print(f"[Hop {r['hop_distance']}] {r['title']} ({r['published_date']})")
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
        for i, rec in enumerate(recs, 1):
            print(f"\n[{i}] {rec['title']}")
            print(f"Date: {str(rec['published_date']).split('T')[0]} | Similarity Score: {rec['score']:.4f}")
            # print a snippet of abstract
            abstract_snippet = (rec['abstract'][:200] + '...') if len(str(rec['abstract'])) > 200 else rec['abstract']
            print(f"Abstract: {abstract_snippet}")
        print("\n=========================================================================================\n")
    else:
        parser.print_help()

