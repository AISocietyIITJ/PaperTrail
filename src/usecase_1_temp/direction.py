"""Direction assignment module using vectorized temporal and vocabulary generality heuristics."""
 
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
import yaml
 
from src.logger import logger
 
TEMPORAL_GAP_DAYS_DEFAULT = 365
GENERALITY_EPSILON_DEFAULT = 0.15
 
 
def compute_generality_scores(df: pd.DataFrame, max_features: int = 5000) -> pd.Series:
    """Precompute TF-IDF average IDF score per paper (lower = more foundational/common vocabulary)."""
    texts = (df["title"].fillna("") + " " + df["abstract"].fillna("")).astype(str)
    vec = TfidfVectorizer(max_features=max_features, stop_words="english", lowercase=True)
    vec.fit(texts)
    idf_map = dict(zip(vec.get_feature_names_out(), vec.idf_))
 
    def score(text: str) -> float:
        words = [w for w in text.lower().split() if w in idf_map]
        if not words:
            return float(max(idf_map.values())) if idf_map else 10.0
        return sum(idf_map[w] for w in words) / len(words)
 
    return texts.apply(score)
 
 
def assign_direction(
    edges: pd.DataFrame,
    df: pd.DataFrame,
    temporal_gap_days: int = TEMPORAL_GAP_DAYS_DEFAULT,
    generality_epsilon: float = GENERALITY_EPSILON_DEFAULT
) -> pd.DataFrame:
    """Vectorized directional orientation of candidate pairs A -> B in < 0.5 seconds at million-edge scale."""
    if "generality_score" not in df.columns:
        logger.info("Computing vocabulary generality scores...")
        df["generality_score"] = compute_generality_scores(df)
 
    dates = pd.to_datetime(df["published_date"]).values.astype("datetime64[s]")
    gen = df["generality_score"].values
    
    texts = (df["title"].fillna("") + " " + df["abstract"].fillna("")).astype(str)
    is_survey = texts.str.contains(r"\bsurvey\b|\breview\b", case=False, regex=True).values
 
    num_nodes = len(df)
    valid_bounds = (edges["node_a"] >= 0) & (edges["node_a"] < num_nodes) & \
                   (edges["node_b"] >= 0) & (edges["node_b"] < num_nodes)
    if not valid_bounds.all():
        dropped = int((~valid_bounds).sum())
        logger.warning(f"Dropping {dropped} candidate edges with out-of-bounds node indices.")
        edges = edges[valid_bounds].reset_index(drop=True)
 
    node_a = edges["node_a"].values.astype(np.int64)
    node_b = edges["node_b"].values.astype(np.int64)
    sim = edges["similarity"].values.astype(np.float32)
 
    date_a, date_b = dates[node_a], dates[node_b]
    # Convert timestamp delta to days
    gap_days = np.abs((date_a - date_b).astype("timedelta64[s]").astype(float)) / (24 * 3600)
 
    # Case 1: Temporal precedence wins if temporal gap >= 365 days
    temporal_mask = gap_days >= temporal_gap_days
    src_temp = np.where(date_a < date_b, node_a, node_b)[temporal_mask]
    dst_temp = np.where(date_a < date_b, node_b, node_a)[temporal_mask]
    sim_temp = sim[temporal_mask]
    reason_temp = np.full(len(src_temp), "temporal", dtype=object)
    logger.debug(f"Temporal precedence assigned direction for {len(src_temp)} edges.")
 
    # Case 2: Generality tie-breaking for same-year papers
    gen_mask = ~temporal_mask
    node_a_gen, node_b_gen = node_a[gen_mask], node_b[gen_mask]
    sim_gen_vals = sim[gen_mask]
    
    g_a, g_b = gen[node_a_gen], gen[node_b_gen]
    valid_epsilon = np.abs(g_a - g_b) >= generality_epsilon
 
    node_a_gen = node_a_gen[valid_epsilon]
    node_b_gen = node_b_gen[valid_epsilon]
    sim_gen_vals = sim_gen_vals[valid_epsilon]
    g_a = g_a[valid_epsilon]
    g_b = g_b[valid_epsilon]
    logger.debug(f"Generality tie-breaking applies to {len(node_a_gen)} edges (epsilon={generality_epsilon}).")
 
    # Lower generality score becomes source
    src_gen = np.where(g_a < g_b, node_a_gen, node_b_gen)
    dst_gen = np.where(g_a < g_b, node_b_gen, node_a_gen)
 
    # Guardrail: If designated source is a survey/review paper and dest is not, invert direction
    surv_src = is_survey[src_gen]
    surv_dst = is_survey[dst_gen]
    
    invert_mask = surv_src & (~surv_dst)
    drop_surv_mask = surv_src & surv_dst  # Both are same-year surveys, discard
    logger.debug(f"Survey guardrail: inverted {int(invert_mask.sum())} edges, "
                 f"dropped {int(drop_surv_mask.sum())} same-year survey-vs-survey edges.")
 
    keep_gen = ~drop_surv_mask
    src_gen_final = np.where(invert_mask[keep_gen], dst_gen[keep_gen], src_gen[keep_gen])
    dst_gen_final = np.where(invert_mask[keep_gen], src_gen[keep_gen], dst_gen[keep_gen])
    sim_gen_final = sim_gen_vals[keep_gen]
    reason_gen_final = np.full(len(src_gen_final), "generality", dtype=object)
 
    out = pd.DataFrame({
        "src": np.concatenate([src_temp, src_gen_final]),
        "dst": np.concatenate([dst_temp, dst_gen_final]),
        "similarity": np.concatenate([sim_temp, sim_gen_final]),
        "reason": np.concatenate([reason_temp, reason_gen_final]),
    })
    return out
 
 
def assign_edge_directions(config_path="config.yaml") -> pd.DataFrame:
    """Execute edge direction assignment directly from config."""
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
        
    edges_path = config["paths"]["candidate_edges"]
    interim_path = config["paths"]["interim_data"]
    out_path = config["paths"]["directed_edges"]
    
    gap = config["direction"].get("temporal_gap_days", 365)
    epsilon = config["direction"].get("generality_epsilon", 0.15)
    max_feat = config["direction"].get("tfidf_max_features", 5000)
    
    logger.info(f"Loading candidate edges ({edges_path}) and papers ({interim_path})...")
    edges = pd.read_parquet(edges_path)
    df = pd.read_parquet(interim_path)
    
    logger.info(f"Computing TF-IDF generality scores (max_features={max_feat})...")
    df["generality_score"] = compute_generality_scores(df, max_features=max_feat)
    
    logger.info(f"Assigning edge directions with vectorized optimization (temporal_gap={gap}d, epsilon={epsilon})...")
    directed = assign_direction(edges, df, temporal_gap_days=gap, generality_epsilon=epsilon)
    
    counts = directed["reason"].value_counts().to_dict()
    logger.info(f"Directed edges produced: {len(directed)}. Reason breakdown: {counts}")
    
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    directed.to_parquet(out_path, index=False)
    logger.info(f"Saved directed edges to {out_path}.")
    return directed
 
 
if __name__ == "__main__":
    assign_edge_directions()
