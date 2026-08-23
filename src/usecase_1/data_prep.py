"""Data ingestion, cleaning, and optional domain filtering module."""

from pathlib import Path
import pandas as pd
import yaml

RAW_PATH = "data/raw/arXiv_scientific_dataset.csv"


def load_raw(path=RAW_PATH) -> pd.DataFrame:
    """Load raw dataset and ensure standard column names and parsed dates."""
    df = pd.read_csv(path, low_memory=False)
    
    # Parse dates cleanly without crashing on mixed formats or NAs
    df["published_date"] = pd.to_datetime(df["published_date"], format="mixed", errors="coerce")
    df["updated_date"] = pd.to_datetime(df["updated_date"], format="mixed", errors="coerce")
    
    # The arXiv CSV names the abstract column 'summary'. Map it to 'abstract' for downstream compatibility.
    if "abstract" not in df.columns and "summary" in df.columns:
        df["abstract"] = df["summary"]
        
    return df


def clean(df: pd.DataFrame) -> pd.DataFrame:
    """Clean NA values, duplicates, and resolve arXiv version re-submissions."""
    df = df.dropna(subset=["abstract", "title", "published_date"]).copy()
    df = df.drop_duplicates(subset=["title"])
    
    # Strip version suffix (e.g., cs-9308101v1 -> cs-9308101) so re-submissions don't create duplicate nodes
    df["arxiv_base_id"] = df["id"].str.replace(r"v\d+$", "", regex=True)
    
    # Retain the latest updated version for each base ID
    df = df.sort_values("updated_date").drop_duplicates(subset=["arxiv_base_id"], keep="last")
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
    if keyword and str(keyword).strip() != "" and str(keyword).lower() != "null" and keyword is not None:
        mask = (
            out["title"].str.contains(keyword, case=False, na=False) |
            out["abstract"].str.contains(keyword, case=False, na=False)
        )
        out = out[mask]
    if max_papers and int(max_papers) > 0 and len(out) > int(max_papers):
        # Sample across timeline and sort by date for clean temporal graph structure
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
    
    print(f"Loading raw data from {raw_path}...")
    df = load_raw(raw_path)
    print(f"Loaded {len(df)} rows. Cleaning dataset...")
    df_clean = clean(df)
    print(f"Cleaned to {len(df_clean)} unique papers. Filtering for categories {cats}, keyword '{kw}', max_papers={max_p}...")
    out = filter_domain(df_clean, category_codes=cats, keyword=kw, max_papers=max_p)
    print(f"Filtered dataset size: {len(out)} papers.")
    
    Path(interim_path).parent.mkdir(parents=True, exist_ok=True)
    out.to_parquet(interim_path, index=False)
    print(f"Saved prepared dataset to {interim_path}.")
    return out


if __name__ == "__main__":
    prepare_dataset()
