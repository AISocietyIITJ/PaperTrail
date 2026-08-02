"""Main CLI entrypoint for executing PaperTrail graph generation and Neo4j queries."""

import argparse
from src.data_prep import prepare_dataset
from src.embed import generate_embeddings
from src.candidate_edges import generate_candidate_edges
from src.direction import assign_edge_directions
from src.build_graph import assemble_graph
from src.ingest_neo4j import ingest_to_neo4j
from src.query import load_neo4j_driver, generate_path_neo4j

def main():
    parser = argparse.ArgumentParser(description="PaperTrail Structured Research Path Generation Pipeline & Query Interface")
    parser.add_argument("--run-pipeline", action="store_true", help="Execute complete dataset prep and graph building")
    parser.add_argument("--ingest-neo4j", action="store_true", help="Push generated pipeline data into Neo4j")
    parser.add_argument("--query", type=str, help="Generate an ordered foundational reading path from Neo4j")
    parser.add_argument("--config", default="config.yaml", help="Path to config yaml file")
    
    args = parser.parse_args()
    
    if args.run_pipeline:
        print("=== RUNNING PAPERTRAIL GRAPH GENERATION PIPELINE ===")
        prepare_dataset(args.config)
        generate_embeddings(args.config)
        generate_candidate_edges(args.config)
        assign_edge_directions(args.config)
        assemble_graph(args.config)
        print("=== PIPELINE RUN COMPLETE ===")

    elif args.ingest_neo4j:
        print("=== INGESTING DATA INTO NEO4J ===")
        ingest_to_neo4j(args.config)
        
    elif args.query:
        config, driver, model = load_neo4j_driver(args.config)
        path = generate_path_neo4j(args.query, driver, model, max_hops=config["query"]["max_hops"])
        
        print(f"\n=================== NEO4J READING PATH FOR: '{args.query}' ===================")
        if path.empty:
            print("No matching path found in domain subgraph.")
        else:
            for _, r in path.iterrows():
                print(f"[Hop {r['hop_distance']}] {r['title']} ({r['published_date']})")
        print("===================================================================================\n")
        driver.close()
        
    else:
        parser.print_help()

if __name__ == "__main__":
    main()