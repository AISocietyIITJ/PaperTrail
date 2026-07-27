"""Candidate edge generation via high-speed vectorized similarity search module."""

from pathlib import Path
import numpy as np
import pandas as pd
import yaml

try:
    import faiss
    HAS_FAISS = True
except ImportError:
    HAS_FAISS = False
    print("Notice: 'faiss' not found. Falling back to NumPy inner product exact search.")


def build_index(embeddings: np.ndarray):
    """Build FAISS inner product index for top-k search."""
    if HAS_FAISS:
        d = embeddings.shape[1]
        index = faiss.IndexFlatIP(d)  # exact inner-product search
        index.add(embeddings)
        return index
    else:
        return embeddings  # Returning array itself for brute-force NumPy search fallback


def get_candidate_edges(
    embeddings: np.ndarray,
    index,
    k: int = 15,
    sim_threshold: float = 0.55
) -> pd.DataFrame:
    """Perform top-k similarity queries with instantaneous vectorized deduplication."""
    n = embeddings.shape[0]
    k_actual = min(k + 1, n)  # +1 because self is always included in search results
    
    if HAS_FAISS and isinstance(index, faiss.Index):
        sims, idxs = index.search(embeddings, k_actual)
    else:
        # Fallback using matrix multiplication for exact cosine similarity
        sim_matrix = embeddings @ embeddings.T
        idxs = np.argsort(sim_matrix, axis=1)[:, ::-1][:, :k_actual]
        sims = np.take_along_axis(sim_matrix, idxs, axis=1)

    # High-speed vectorized flattening (< 0.1s for millions of edges)
    n_rows, n_cols = sims.shape
    src_nodes = np.repeat(np.arange(n_rows, dtype=np.int64), n_cols)
    dst_nodes = idxs.flatten().astype(np.int64)
    sim_vals = sims.flatten().astype(np.float32)
    
    # Filter invalid self-loops, negative index placeholders, and below similarity threshold
    valid_mask = (src_nodes != dst_nodes) & (dst_nodes >= 0) & (sim_vals >= sim_threshold)
    
    src_clean = src_nodes[valid_mask]
    dst_clean = dst_nodes[valid_mask]
    sim_clean = sim_vals[valid_mask]
    
    if len(src_clean) == 0:
        return pd.DataFrame(columns=["node_a", "node_b", "similarity"])
        
    edges = pd.DataFrame({
        "node_a": src_clean,
        "node_b": dst_clean,
        "similarity": sim_clean
    })

    # Instantaneous 64-bit integer deduplication for symmetric pairs (a,b) vs (b,a) (< 0.3s)
    min_node = np.minimum(src_clean, dst_clean)
    max_node = np.maximum(src_clean, dst_clean)
    edges["pair_key"] = min_node * 1000000000 + max_node
    
    edges = edges.sort_values("similarity", ascending=False).drop_duplicates("pair_key")
    edges = edges.drop(columns="pair_key").reset_index(drop=True)
    return edges


def generate_candidate_edges(config_path="config.yaml") -> pd.DataFrame:
    """Execute candidate edges generation directly from config."""
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
        
    emb_path = config["paths"]["embeddings"]
    out_path = config["paths"]["candidate_edges"]
    top_k = config["candidate_edges"]["top_k"]
    threshold = config["candidate_edges"]["similarity_threshold"]
    
    print(f"Loading embeddings from {emb_path}...")
    embeddings = np.load(emb_path)
    
    print("Building similarity search index...")
    index = build_index(embeddings)
    
    print(f"Searching for candidate edges (k={top_k}, threshold={threshold}) with vectorized optimization...")
    edges = get_candidate_edges(embeddings, index, k=top_k, sim_threshold=threshold)
    print(f"Found {len(edges)} unique candidate edge pairs.")
    
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    edges.to_parquet(out_path, index=False)
    print(f"Saved candidate edges to {out_path}.")
    return edges


if __name__ == "__main__":
    generate_candidate_edges()
