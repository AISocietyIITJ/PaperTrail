"""Query interface and topological reading path extraction module."""

import pickle
from pathlib import Path
import networkx as nx
import numpy as np
import pandas as pd
import yaml
from sentence_transformers import SentenceTransformer
from src.build_graph import reduce_graph


def find_target(
    query_text: str,
    model,
    df: pd.DataFrame,
    embeddings: np.ndarray,
    top_n: int = 1
) -> list[int]:
    """Identify the top-n target paper node indices matching a query string."""
    q_emb = model.encode([query_text], normalize_embeddings=True)
    sims = (embeddings @ q_emb.T).flatten()
    top_idxs = sims.argsort()[::-1][:top_n]
    return [int(idx) for idx in top_idxs]


def get_reading_path(
    target_idx: int,
    G: nx.DiGraph,
    df: pd.DataFrame,
    max_hops: int | None = 4
) -> pd.DataFrame:
    """Extract topologically sorted reading path leading to a target node with query-time transitive reduction."""
    if target_idx not in G or (G.in_degree(target_idx) == 0 and G.out_degree(target_idx) == 0):
        if target_idx < len(df):
            res = df.loc[[target_idx], ["node_idx", "title", "published_date"]].copy()
            res["hop_distance"] = 0
            return res.reset_index(drop=True)
        return pd.DataFrame(columns=["node_idx", "title", "published_date", "hop_distance"])

    if max_hops is None:
        ancestors = nx.ancestors(G, target_idx)
    else:
        lengths = nx.single_target_shortest_path_length(G, target_idx, cutoff=max_hops)
        ancestors = set(lengths.keys()) - {target_idx}

    node_set = ancestors | {target_idx}
    subG = G.subgraph(node_set).copy()

    if not nx.is_directed_acyclic_graph(subG):
        raise ValueError("Subgraph is not a DAG — verify cycle removal during graph assembly.")

    # Execute dynamic query-time transitive reduction on the topic subgraph (< 5ms)
    if len(subG) > 2 and subG.number_of_edges() > 1:
        subG = reduce_graph(subG)

    ordered_idxs = list(nx.topological_sort(subG))
    hop_dist = nx.single_target_shortest_path_length(G, target_idx, cutoff=max_hops)

    result = df.loc[ordered_idxs, ["node_idx", "title", "published_date"]].copy()
    result["hop_distance"] = result["node_idx"].map(hop_dist).fillna(0).astype(int)
    return result.reset_index(drop=True)


def generate_path(
    query_text: str,
    model,
    G: nx.DiGraph,
    df: pd.DataFrame,
    embeddings: np.ndarray,
    max_hops=4,
    top_n_targets=1
) -> pd.DataFrame:
    """Generate a cohesive reading path across top target matches, ordered foundational to advanced."""
    targets = find_target(query_text, model, df, embeddings, top_n=top_n_targets)
    print(f"Query: '{query_text}' -> Matched target node indices: {targets}")
    for t in targets:
        print(f"  Target [{t}]: {df.loc[t, 'title']} ({str(df.loc[t, 'published_date']).split('T')[0]})")
        
    paths = [get_reading_path(t, G, df, max_hops=max_hops) for t in targets]
    if not paths:
        return pd.DataFrame()
        
    combined = pd.concat(paths).drop_duplicates(subset="node_idx").sort_values("published_date")
    return combined.reset_index(drop=True)


def load_resources(config_path="config.yaml"):
    """Helper to load model, graph, dataframe, and embeddings into memory for querying."""
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
        
    interim_path = config["paths"]["interim_data"]
    emb_path = config["paths"]["embeddings"]
    graph_path = config["paths"]["graph_path"]
    model_name = config["embedding"]["model_name"]
    adapter_name = config["embedding"].get("adapter_name")
    
    print("Loading domain dataset...")
    df = pd.read_parquet(interim_path)
    print("Loading embeddings...")
    embeddings = np.load(emb_path)
    print("Loading graph DAG...")
    with open(graph_path, "rb") as f:
        G = pickle.load(f)
        
    print(f"Loading embedding model {model_name}...")
    model = SentenceTransformer(model_name)
    if adapter_name and hasattr(model, "load_adapter"):
        try:
            model.load_adapter(adapter_name)
        except Exception as e:
            print(f"Notice during adapter attachment: {e}")
            
    return config, model, G, df, embeddings


if __name__ == "__main__":
    config, model, G, df, embeddings = load_resources()
    test_query = "self-attention transformer mechanism"
    path_df = generate_path(
        test_query,
        model,
        G,
        df,
        embeddings,
        max_hops=config["query"]["max_hops"],
        top_n_targets=config["query"]["top_n_targets"]
    )
    print(f"\nReading Path for '{test_query}':")
    print(path_df.to_string(index=False))
