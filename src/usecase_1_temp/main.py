"""Main CLI entrypoint for executing PaperTrail graph generation and Neo4j queries."""
 
import argparse
from src.usecase_1_temp.data_prep import prepare_dataset
from src.usecase_1_temp.embed import generate_embeddings
from src.usecase_1_temp.candidate_edges import generate_candidate_edges
from src.usecase_1_temp.direction import assign_edge_directions
from src.usecase_1_temp.build_graph import assemble_graph
from src.usecase_1_temp.ingest_neo4j import ingest_to_neo4j

from src.usecase_1_temp.query import load_neo4j_driver, generate_path_neo4j

from src.logger import logger
 
def main():
    parser = argparse.ArgumentParser(description="PaperTrail Structured Research Path Generation Pipeline & Query Interface")
    parser.add_argument("--run-pipeline", action="store_true", help="Execute complete dataset prep and graph building")
    parser.add_argument("--ingest-neo4j", action="store_true", help="Push generated pipeline data into Neo4j")
    parser.add_argument("--query", type=str, help="Generate an ordered foundational reading path from Neo4j")
    parser.add_argument("--config", default="config.yaml", help="Path to config yaml file")
    
    args = parser.parse_args()
    
    if args.run_pipeline:
        logger.info("=== RUNNING PAPERTRAIL GRAPH GENERATION PIPELINE ===")
        prepare_dataset(args.config)
        generate_embeddings(args.config)
        generate_candidate_edges(args.config)
        assign_edge_directions(args.config)
        assemble_graph(args.config)
        logger.info("=== PIPELINE RUN COMPLETE ===")
 
    elif args.ingest_neo4j:
        logger.info("=== INGESTING DATA INTO NEO4J ===")
        ingest_to_neo4j(args.config)
        
    elif args.query:
        config, driver, model = load_neo4j_driver(args.config)
        path = generate_path_neo4j(args.query, driver, model, max_hops=config["query"]["max_hops"])
        
        logger.info(f"=================== NEO4J READING PATH FOR: '{args.query}' ===================")
        if path.empty:
            logger.warning("No matching path found in domain subgraph.")
        else:
            for _, r in path.iterrows():
                logger.info(f"[Hop {r['hop_distance']}] {r['title']} ({r['published_date']})")
        logger.info("===================================================================================")
        driver.close()
        
    else:
        parser.print_help()
 
if __name__ == "__main__":
    main()