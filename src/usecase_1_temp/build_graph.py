"""Graph assembly, vectorized DAG enforcement, and transitive reduction module."""
 
from pathlib import Path
import pickle
import networkx as nx
import pandas as pd
import yaml
 
from src.logger import logger
 
 
def enforce_acyclic_order(edges: pd.DataFrame, df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Vectorized total-order DAG enforcement: eliminates cycle potential in O(E) time at million-edge scale."""
    if "generality_score" not in df.columns:
        df = df.assign(generality_score=0.0)
        
    # Create strict topological timeline order (earlier publication -> foundational vocab -> node index)
    df_sorted = df.sort_values(by=["published_date", "generality_score", "node_idx"], ascending=[True, True, True])
    rank_map = dict(zip(df_sorted["node_idx"], range(len(df_sorted))))
    
    src_rank = edges["src"].map(rank_map)
    dst_rank = edges["dst"].map(rank_map)
    
    valid_mask = src_rank < dst_rank
    removed_count = int((~valid_mask).sum())
    
    return edges[valid_mask].reset_index(drop=True), removed_count
 
 
def build_graph(directed_edges: pd.DataFrame) -> nx.DiGraph:
    """Build directed graph with similarity weights and trace reasons."""
    G = nx.DiGraph()
    for row in directed_edges.itertuples():
        G.add_edge(int(row.src), int(row.dst), weight=float(row.similarity), reason=str(row.reason))
    return G
 
 
def remove_cycles(G: nx.DiGraph) -> tuple[nx.DiGraph, int]:
    """Iteratively break cycles by removing the lowest-weight edge in each found cycle (for small subgraphs)."""
    G = G.copy()
    removed_count = 0
    while True:
        try:
            cycle = nx.find_cycle(G)
        except nx.NetworkXNoCycle:
            break
        # Drop the lowest-weight (lowest semantic similarity) edge in the cycle
        weakest = min(cycle, key=lambda e: G[e[0]][e[1]]["weight"])
        weight = G[weakest[0]][weakest[1]]["weight"]
        G.remove_edge(*weakest[:2])
        removed_count += 1
        logger.debug(f"Removed cycle edge {weakest[:2]} (weight={weight})")
    return G, removed_count
 
 
def reattach_attrs(reduced: nx.DiGraph, original: nx.DiGraph) -> nx.DiGraph:
    """Re-attach edge attributes (weight, reason) dropped by transitive reduction."""
    for u, v in reduced.edges():
        if original.has_edge(u, v):
            reduced[u][v].update(original[u][v])
    return reduced
 
 
def reduce_graph(G: nx.DiGraph) -> nx.DiGraph:
    """Perform transitive reduction on a DAG and retain edge attributes."""
    reduced = nx.transitive_reduction(G)
    return reattach_attrs(reduced, G)
 
 
def graph_stats(G: nx.DiGraph) -> dict:
    """Compute structural metrics for the graph."""
    return {
        "nodes": G.number_of_nodes(),
        "edges": G.number_of_edges(),
        "weakly_connected_components": nx.number_weakly_connected_components(G) if G.number_of_nodes() > 0 else 0,
        "isolated_nodes": sum(1 for n in G.nodes if G.degree(n) == 0),
        "is_dag": nx.is_directed_acyclic_graph(G)
    }
 
 
def validate_graph(G: nx.DiGraph, df: pd.DataFrame) -> dict:
    """Validate structural integrity of the DAG and ensure zero temporal date-order violations."""
    stats = graph_stats(G)
    
    date_violations = 0
    dates = pd.to_datetime(df["published_date"]).to_dict()
    for u, v, data in G.edges(data=True):
        if data.get("reason") == "temporal":
            if dates[u] > dates[v]:
                date_violations += 1
 
    avg_out = sum(dict(G.out_degree()).values()) / G.number_of_nodes() if G.number_of_nodes() > 0 else 0
    return {
        **stats,
        "avg_out_degree": round(float(avg_out), 4),
        "date_violations": date_violations,
    }
 
 
def assemble_graph(config_path="config.yaml") -> nx.DiGraph:
    """Execute scalable graph assembly directly from config."""
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
        
    directed_path = config["paths"]["directed_edges"]
    interim_path = config["paths"]["interim_data"]
    out_path = config["paths"]["graph_path"]
    
    logger.info(f"Loading directed edges from {directed_path} and dataset from {interim_path}...")
    edges = pd.read_parquet(directed_path)
    df = pd.read_parquet(interim_path)
    
    logger.info(f"Executing vectorized total-order DAG enforcement over {len(edges)} edges...")
    clean_edges, pruned_count = enforce_acyclic_order(edges, df)
    if pruned_count > 0:
        logger.warning(f"Pruned {pruned_count} cycle-inducing ambiguous edges via vectorized ordering.")
        
    logger.info("Assembling NetworkX DiGraph...")
    G_final = build_graph(clean_edges)
    
    # Ensure all dataset nodes are registered in the graph even if isolated
    G_final.add_nodes_from(df["node_idx"].tolist())
    
    report = validate_graph(G_final, df)
    logger.info("================== GRAPH VALIDATION REPORT ==================")
    for k, v in report.items():
        logger.info(f"  {k}: {v}")
    logger.info("=============================================================")
    
    try:
        assert report["is_dag"] is True, "Error: Resulting graph contains cycles after cleanup."
        assert report["date_violations"] == 0, f"Error: Found {report['date_violations']} date order violations on temporal edges."
    except AssertionError as e:
        logger.error(str(e))
        raise
    
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "wb") as f:
        pickle.dump(G_final, f)
    logger.info(f"Saved validated DAG to {out_path}.")
    return G_final
 
 
if __name__ == "__main__":
    assemble_graph()
 
