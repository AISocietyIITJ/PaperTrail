"""Data ingestion, cleaning, and optional domain filtering module."""
 
from pathlib import Path
import pandas as pd
import yaml
 
from src.logger import logger
 
RAW_PATH = "data/raw/arXiv_scientific_dataset.csv"
 
 
def load_raw(path=RAW_PATH) -> pd.DataFrame:
    """Load raw dataset and ensure standard column names and parsed dates."""
    try:
        df = pd.read_csv(path, low_memory=False, on_bad_lines="skip")
    except Exception as e:
        logger.warning(f"Standard CSV read failed ({e}); retrying with python engine...")
        df = pd.read_csv(path, engine="python", on_bad_lines="skip")
    
    # Parse dates cleanly without crashing on mixed formats or NAs
    df["published_date"] = pd.to_datetime(df["published_date"], format="mixed", errors="coerce")
    df["updated_date"] = pd.to_datetime(df["updated_date"], format="mixed", errors="coerce")
    
    # The arXiv CSV names the abstract column 'summary'. Map it to 'abstract' for downstream compatibility.
    if "abstract" not in df.columns and "summary" in df.columns:
        logger.debug("Mapping 'summary' column to 'abstract' for downstream compatibility.")
        df["abstract"] = df["summary"]
        
    return df
 
 
def clean(df: pd.DataFrame) -> pd.DataFrame:
    """Clean NA values, duplicates, and resolve arXiv version re-submissions."""
    before = len(df)
    df = df.dropna(subset=["abstract", "title", "published_date"]).copy()
    logger.debug(f"Dropped {before - len(df)} rows with missing abstract/title/published_date.")
    
    before = len(df)
    df = df.drop_duplicates(subset=["title"])
    logger.debug(f"Dropped {before - len(df)} duplicate-title rows.")
    
    # Strip version suffix (e.g., cs-9308101v1 -> cs-9308101) so re-submissions don't create duplicate nodes
    df["arxiv_base_id"] = df["id"].str.replace(r"v\d+$", "", regex=True)
    
    # Retain the latest updated version for each base ID
    before = len(df)
    df = df.sort_values("updated_date").drop_duplicates(subset=["arxiv_base_id"], keep="last")
    logger.debug(f"Collapsed {before - len(df)} re-submission rows, keeping latest version per arxiv_base_id.")
    
    df = df.reset_index(drop=True)
    df["node_idx"] = df.index  # stable integer index used across all downstream steps
    return df
 
 
def filter_domain(
    df: pd.DataFrame,
    category_codes: list[str] | None = None,
    keyword: str | None = None,
    max_papers: int | None = None
) -> pd.DataFrame:
    """Filter to target domain category and optional keyword matching in title or abstract."""
    out = df.copy()
    if category_codes and len(category_codes) > 0:
        out = out[out["category_code"].isin(category_codes)]
        logger.debug(f"Filtered to category_codes={category_codes}, {len(out)} papers remaining.")
    if keyword and str(keyword).strip() != "" and str(keyword).lower() != "null" and keyword is not None:
        mask = (
            out["title"].str.contains(keyword, case=False, na=False) |
            out["abstract"].str.contains(keyword, case=False, na=False)
        )
        out = out[mask]
        logger.debug(f"Filtered to keyword='{keyword}', {len(out)} papers remaining.")
    if max_papers and int(max_papers) > 0 and len(out) > int(max_papers):
        # Sample across timeline and sort by date for clean temporal graph structure
        logger.debug(f"Sampling down to max_papers={max_papers} (random_state=42).")
        out = out.sample(n=int(max_papers), random_state=42).sort_values("published_date")
    return out.reset_index(drop=True).assign(node_idx=lambda d: d.index)
 
 
def prepare_dataset(config_path="config.yaml") -> pd.DataFrame:
    """Execute dataset preparation directly from config."""
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
        
    raw_path = config["paths"]["raw_data"]
    interim_path = config["paths"]["interim_data"]
    cats = config["domain"].get("category_codes", [])
    kw = config["domain"].get("keyword")
    max_p = config["domain"].get("max_papers")
    
    logger.info(f"Loading raw data from {raw_path}...")
    df = load_raw(raw_path)
    logger.info(f"Loaded {len(df)} rows. Cleaning dataset...")
    df_clean = clean(df)
    logger.info(f"Cleaned to {len(df_clean)} unique papers. Filtering for categories {cats}, keyword '{kw}', max_papers={max_p}...")
    out = filter_domain(df_clean, category_codes=cats, keyword=kw, max_papers=max_p)
    logger.info(f"Filtered dataset size: {len(out)} papers.")
    
    Path(interim_path).parent.mkdir(parents=True, exist_ok=True)
    out.to_parquet(interim_path, index=False)
    logger.info(f"Saved prepared dataset to {interim_path}.")
    return out
 
 
if __name__ == "__main__":
    prepare_dataset()