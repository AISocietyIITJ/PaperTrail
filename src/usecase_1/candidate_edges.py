"""Candidate edge generation via Pinecone similarity search."""

import os
from pathlib import Path
import numpy as np
import pandas as pd
import yaml
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from pinecone import Pinecone
import time

from src.config import PINECONE_API_KEY


def get_candidate_edges_pinecone(
    num_nodes: int,
    index_name: str,
    k: int = 15,
    sim_threshold: float = 0.55,
    max_workers: int = 20
) -> pd.DataFrame:
    """Perform top-k similarity queries against Pinecone using threaded requests."""
    pc = Pinecone(api_key=PINECONE_API_KEY)
    index = pc.Index(index_name)
    
    k_actual = min(k + 1, num_nodes) # +1 because self is always included
    
    src_nodes = []
    dst_nodes = []
    sim_vals = []
    
    def fetch_neighbors(node_id):
        for attempt in range(3):
            try:
                res = index.query(id=str(node_id), top_k=k_actual)
                return node_id, res['matches']
            except Exception as e:
                time.sleep(1)
        return node_id, []

    print(f"Querying Pinecone for {num_nodes} nodes using {max_workers} threads...")
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(fetch_neighbors, i): i for i in range(num_nodes)}
        
        for future in tqdm(as_completed(futures), total=num_nodes, desc="Pinecone queries"):
            node_id, matches = future.result()
            for match in matches:
                src_nodes.append(node_id)
                dst_nodes.append(int(match['id']))
                sim_vals.append(float(match['score']))

    edges = pd.DataFrame({
        "node_a": src_nodes,
        "node_b": dst_nodes,
        "similarity": sim_vals
    })

    # Filter invalid self-loops, out-of-bounds node indices, and below similarity threshold
    valid_mask = (edges["node_a"] != edges["node_b"]) & \
                 (edges["node_a"] >= 0) & (edges["node_a"] < num_nodes) & \
                 (edges["node_b"] >= 0) & (edges["node_b"] < num_nodes) & \
                 (edges["similarity"] >= sim_threshold)
    edges = edges[valid_mask].copy()

    if edges.empty:
        return pd.DataFrame(columns=["node_a", "node_b", "similarity"])

    # Fast 64-bit integer deduplication for symmetric pairs (a,b) vs (b,a)
    edges["min_node"] = np.minimum(edges["node_a"], edges["node_b"])
    edges["max_node"] = np.maximum(edges["node_a"], edges["node_b"])
    edges["pair_key"] = edges["min_node"].astype(np.int64) * 1000000000 + edges["max_node"].astype(np.int64)
    
    edges = edges.sort_values("similarity", ascending=False).drop_duplicates("pair_key")
    edges = edges.drop(columns=["pair_key", "min_node", "max_node"]).reset_index(drop=True)
    
    return edges


def generate_candidate_edges(config_path="config.yaml") -> pd.DataFrame:
    """Execute candidate edges generation directly from config."""
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
        
    interim_path = config["paths"]["interim_data"]
    out_path = config["paths"]["candidate_edges"]
    top_k = config["candidate_edges"]["top_k"]
    threshold = config["candidate_edges"]["similarity_threshold"]
    pinecone_index = config["embedding"].get("pinecone_index", "papertrail-papers")
    
    print(f"Loading dataset to determine node count from {interim_path}...")
    df = pd.read_parquet(interim_path)
    num_nodes = len(df)
    
    print(f"Searching for candidate edges (k={top_k}, threshold={threshold}) via Pinecone...")
    edges = get_candidate_edges_pinecone(
        num_nodes=num_nodes, 
        index_name=pinecone_index, 
        k=top_k, 
        sim_threshold=threshold,
        max_workers=20
    )
    print(f"Found {len(edges)} unique candidate edge pairs.")
    
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    edges.to_parquet(out_path, index=False)
    print(f"Saved candidate edges to {out_path}.")
    return edges


if __name__ == "__main__":
    generate_candidate_edges()
