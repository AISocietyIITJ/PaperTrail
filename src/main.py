"""Main CLI entrypoint for executing PaperTrail graph generation and research topic queries."""

import argparse
from src.data_prep import prepare_dataset
from src.embed import generate_embeddings
from src.candidate_edges import generate_candidate_edges
from src.direction import assign_edge_directions
from src.build_graph import assemble_graph
from src.query import load_resources, generate_path


def main():
    parser = argparse.ArgumentParser(description="PaperTrail Structured Research Path Generation Pipeline & Query Interface")
    parser.add_argument("--run-pipeline", action="store_true", help="Execute complete dataset preparation, embedding, edge direction, and graph assembly")
    parser.add_argument("--query", type=str, help="Generate an ordered foundational reading path for a research topic query")
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
        
    elif args.query:
        config, model, G, df, embeddings = load_resources(args.config)
        path = generate_path(
            args.query,
            model,
            G,
            df,
            embeddings,
            max_hops=config["query"]["max_hops"],
            top_n_targets=config["query"]["top_n_targets"]
        )
        print(f"\n=================== READING PATH FOR: '{args.query}' ===================")
        if path.empty:
            print("No matching path found in domain subgraph.")
        else:
            for _, r in path.iterrows():
                print(f"[Hop {r['hop_distance']}] {r['title']} ({str(r['published_date']).split('T')[0]})")
        print("===================================================================================\n")
        
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
