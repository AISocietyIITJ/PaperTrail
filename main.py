"""
Central API entry point for PaperTrail.
Exposes standard functions for the unified use cases.
"""
import argparse

# ==========================================
# 1. Reading Path Generation Pipeline
# ==========================================
from src.usecase_1.data_prep import prepare_dataset as prepare_reading_path_data
from src.usecase_1.embed import generate_embeddings as generate_reading_path_embeddings
from src.usecase_1.candidate_edges import generate_candidate_edges
from src.usecase_1.direction import assign_edge_directions
from src.usecase_1.build_graph import assemble_graph
from src.usecase_1.ingest_neo4j import ingest_to_neo4j as ingest_reading_path_to_neo4j
from src.usecase_1.query import load_neo4j_driver, generate_path_neo4j

def generate_reading_path_pipeline(config_path="config.yaml"):
    """Run the complete data prep and graph building pipeline."""
    prepare_reading_path_data(config_path)
    generate_reading_path_embeddings(config_path)
    generate_candidate_edges(config_path)
    assign_edge_directions(config_path)
    assemble_graph(config_path)

def query_reading_path(query_str: str, config_path="config.yaml"):
    """Query a specific reading path."""
    config, driver, model = load_neo4j_driver(config_path)
    path = generate_path_neo4j(query_str, driver, model, max_hops=config["query"]["max_hops"])
    driver.close()
    return path

# ==========================================
# 2. Academic Profiles & Interests
# ==========================================
from src.usecase_2.embedding.generate_embedding import gen_res_emb_ingestion as ingest_academic_interests_pinecone
from src.usecase_2.embedding.generate_embedding_prof import gen_prof_emb_ingestion as ingest_professor_profiles_pinecone
from src.usecase_2.utils.get_prof_info import query_graph_db as query_academic_profiles

# ==========================================
# 3. Paper Recommendations
# ==========================================
from src.usecase_3.UC3 import get_recommendations as get_paper_recommendations
from src.usecase_3.Pinecone_setup import main as setup_recommendations_pinecone


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PaperTrail Unified API")
    parser.add_argument("--run-reading-pipeline", action="store_true", help="Execute complete dataset prep and graph building")
    parser.add_argument("--ingest-reading-neo4j", action="store_true", help="Push generated pipeline data into Neo4j")
    parser.add_argument("--query-reading", type=str, help="Generate an ordered foundational reading path from Neo4j")
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
        path = query_reading_path(args.query_reading, args.config)
        print(f"\n=================== NEO4J READING PATH FOR: '{args.query_reading}' ===================")
        if path.empty:
            print("No matching path found in domain subgraph.")
        else:
            for _, r in path.iterrows():
                print(f"[Hop {r['hop_distance']}] {r['title']} ({r['published_date']})")
        print("===================================================================================\n")
    else:
        parser.print_help()
