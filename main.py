"""Backend-facing functions for the three PaperTrail use cases."""
import argparse
import os

def generate_reading_path_pipeline(config_path="config.yaml"):
    """Run the complete data prep and graph building pipeline."""
    from src.usecase_1.build_graph import assemble_graph
    from src.usecase_1.candidate_edges import generate_candidate_edges
    from src.usecase_1.data_prep import prepare_dataset as prepare_reading_path_data
    from src.usecase_1.direction import assign_edge_directions
    from src.usecase_1.embed import generate_embeddings as generate_reading_path_embeddings

    prepare_reading_path_data(config_path)
    generate_reading_path_embeddings(config_path)
    generate_candidate_edges(config_path)
    assign_edge_directions(config_path)
    assemble_graph(config_path)

def get_reading_path(query: str, config_path="config.yaml"):
    """Use case 1: return a JSON-ready foundational reading path."""
    from src.usecase_1.query import generate_path_neo4j, load_neo4j_driver

    config, driver, model = load_neo4j_driver(config_path)
    try:
        path = generate_path_neo4j(query, driver, model, max_hops=config["query"]["max_hops"])
        return path.to_dict(orient="records")
    finally:
        driver.close()


def setup_academic_profiles_pipeline():
    """Use case 2: run setup, generating aliases, embeddings, and ingesting nodes/edges."""
    from src.usecase_2.embedding.generate_alias import generate_phrase
    from src.usecase_2.embedding.generate_embedding import gen_res_emb_ingestion
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


def find_academic_profiles(query: str, resume_path: str):
    """Use case 2: return professors matching a query and resume PDF path."""
    from src.usecase_2.local_llm.extractor import get_interest_topics
    from src.usecase_2.utils.get_prof_info import query_graph_db
    from src.usecase_2.utils.vec_query_search import search_vector_db
    from src.usecase_2.utils.parsing_resume import extract_text_from_pdf
    
    interests = get_interest_topics(query, extract_text_from_pdf(resume_path))
    if not interests:
        return {"interests": None, "interest_ids": [], "professors": []}

    interest_ids = search_vector_db(interests)
    return {
        "interests": interests,
        "interest_ids": interest_ids,
        "professors": query_graph_db(interest_ids),
    }


def recommend_papers(query: str, top_n: int = 5):
    """Use case 3: return the top matching paper records for a query."""
    if top_n < 1:
        raise ValueError("top_n must be at least 1")

    from pinecone import Pinecone
    from src.config import PINECONE_API_KEY
    from src.usecase_3.Pinecone_setup import return_output
    from src.usecase_3.UC3 import get_recommendations

    index = Pinecone(api_key=PINECONE_API_KEY).Index("paper-embeds")
    return return_output(index, get_recommendations(query, top_n))



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PaperTrail Unified API")
    parser.add_argument("--run-reading-pipeline", action="store_true", help="Execute complete dataset prep and graph building")
    parser.add_argument("--ingest-reading-neo4j", action="store_true", help="Push generated pipeline data into Neo4j")
    parser.add_argument("--query-reading", type=str, help="Generate an ordered foundational reading path from Neo4j")
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
        from src.usecase_1.ingest_neo4j import ingest_to_neo4j as ingest_reading_path_to_neo4j

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
        result = find_academic_profiles(query="Suggest me the proffs", resume_path=resume_path)
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
    else:
        parser.print_help()

