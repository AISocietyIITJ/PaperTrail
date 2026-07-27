"""Unit tests for direction assignment logic and vocabulary generality heuristics."""

import pandas as pd
import numpy as np
from src.direction import assign_direction, compute_generality_scores


def test_compute_generality_scores():
    df = pd.DataFrame({
        "title": ["A general survey on neural attention", "Specific long-context sparse flash attention optimization"],
        "abstract": ["An overview and comprehensive survey of attention models.", "We propose sparse kernel memory optimization techniques."]
    })
    scores = compute_generality_scores(df)
    assert len(scores) == 2
    assert isinstance(scores.iloc[0], (float, np.floating))
    assert isinstance(scores.iloc[1], (float, np.floating))


def test_assign_direction_temporal():
    # Gap >= 365 days -> temporal direction wins regardless of vocabulary score
    df = pd.DataFrame({
        "published_date": ["2017-06-01", "2021-09-01"],
        "title": ["Older foundational paper", "Newer specific optimization paper"],
        "abstract": ["Abstract one", "Abstract two"],
        "generality_score": [5.0, 1.0]  # Notice older has higher score (more specific vocab), but temporal must override
    })
    edges = pd.DataFrame([{"node_a": 0, "node_b": 1, "similarity": 0.85}])
    out = assign_direction(edges, df, temporal_gap_days=365)
    
    assert len(out) == 1
    assert out.loc[0, "src"] == 0
    assert out.loc[0, "dst"] == 1
    assert out.loc[0, "reason"] == "temporal"


def test_assign_direction_generality_and_survey():
    # Gap < 365 days -> generality direction decides, but survey excluded from source role
    df = pd.DataFrame({
        "published_date": ["2020-01-01", "2020-03-01"],
        "title": ["A comprehensive survey of attention mechanisms", "A new self-attention model architecture"],
        "abstract": ["This survey covers everything in literature.", "We propose a novel self-attention model for parsing."],
        "generality_score": [2.0, 4.0]  # Node 0 has lower score (more general), BUT it is a survey paper
    })
    edges = pd.DataFrame([{"node_a": 0, "node_b": 1, "similarity": 0.75}])
    out = assign_direction(edges, df, temporal_gap_days=365, generality_epsilon=0.1)
    
    assert len(out) == 1
    # Node 0 is a survey, so direction must be inverted: Node 1 -> Node 0
    assert out.loc[0, "src"] == 1
    assert out.loc[0, "dst"] == 0
    assert out.loc[0, "reason"] == "generality"


def test_assign_direction_ambiguous_drop():
    df = pd.DataFrame({
        "published_date": ["2020-01-01", "2020-02-01"],
        "title": ["Model A variation", "Model B variation"],
        "abstract": ["Simultaneous concurrent work A", "Simultaneous concurrent work B"],
        "generality_score": [3.00, 3.05]  # Difference (0.05) < epsilon (0.15)
    })
    edges = pd.DataFrame([{"node_a": 0, "node_b": 1, "similarity": 0.80}])
    out = assign_direction(edges, df, temporal_gap_days=365, generality_epsilon=0.15)
    
    assert len(out) == 0  # Should drop ambiguous simultaneous pairs rather than arbitrary assignment
