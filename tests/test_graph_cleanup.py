"""Unit tests for graph assembly, vectorized DAG enforcement, cycle removal, and transitive reduction."""

import networkx as nx
import pandas as pd
from src.build_graph import build_graph, remove_cycles, reduce_graph, graph_stats, enforce_acyclic_order


def test_enforce_acyclic_order():
    # Suppose we have 3 papers chronological by date: 0 (2018), 1 (2020), 2 (2022)
    df = pd.DataFrame({
        "node_idx": [0, 1, 2],
        "published_date": ["2018-01-01", "2020-01-01", "2022-01-01"],
        "generality_score": [1.0, 2.0, 3.0]
    })
    # Create valid forward edges (0->1, 1->2) and an invalid backward loop edge (2->0)
    edges = pd.DataFrame([
        {"src": 0, "dst": 1, "similarity": 0.80, "reason": "temporal"},
        {"src": 1, "dst": 2, "similarity": 0.85, "reason": "temporal"},
        {"src": 2, "dst": 0, "similarity": 0.75, "reason": "generality"},
    ])
    clean_edges, pruned_count = enforce_acyclic_order(edges, df)
    assert pruned_count == 1
    assert len(clean_edges) == 2
    assert clean_edges["src"].tolist() == [0, 1]
    assert clean_edges["dst"].tolist() == [1, 2]


def test_cycle_removal():
    # Create a triangular cycle: 0 -> 1 (0.9), 1 -> 2 (0.8), 2 -> 0 (0.6 - weakest edge)
    edges = pd.DataFrame([
        {"src": 0, "dst": 1, "similarity": 0.9, "reason": "temporal"},
        {"src": 1, "dst": 2, "similarity": 0.8, "reason": "temporal"},
        {"src": 2, "dst": 0, "similarity": 0.6, "reason": "generality"},
    ])
    G_raw = build_graph(edges)
    assert not nx.is_directed_acyclic_graph(G_raw)
    
    G_acyclic, removed_count = remove_cycles(G_raw)
    assert nx.is_directed_acyclic_graph(G_acyclic)
    assert removed_count == 1
    assert not G_acyclic.has_edge(2, 0)
    assert G_acyclic.has_edge(0, 1) and G_acyclic.has_edge(1, 2)


def test_transitive_reduction_preserves_attributes():
    # 0 -> 1 -> 2, plus direct redundant shortcut 0 -> 2
    edges = pd.DataFrame([
        {"src": 0, "dst": 1, "similarity": 0.95, "reason": "temporal"},
        {"src": 1, "dst": 2, "similarity": 0.85, "reason": "temporal"},
        {"src": 0, "dst": 2, "similarity": 0.70, "reason": "temporal"},
    ])
    G_raw = build_graph(edges)
    G_reduced = reduce_graph(G_raw)
    
    assert not G_reduced.has_edge(0, 2)  # redundant transitive shortcut should be removed
    assert G_reduced.has_edge(0, 1) and G_reduced.has_edge(1, 2)
    
    # Attributes on remaining edges must be preserved
    assert G_reduced[0][1]["weight"] == 0.95
    assert G_reduced[0][1]["reason"] == "temporal"


def test_graph_stats():
    G = nx.DiGraph()
    G.add_edge(0, 1, weight=0.8, reason="temporal")
    G.add_node(2)  # isolated node
    stats = graph_stats(G)
    assert stats["nodes"] == 3
    assert stats["edges"] == 1
    assert stats["isolated_nodes"] == 1
    assert stats["is_dag"] is True
