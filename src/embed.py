"""Semantic embedding module using SPECTER2 with CUDA optimization and disk verification."""

import os
from pathlib import Path
import numpy as np
import pandas as pd
import yaml
import torch
from sentence_transformers import SentenceTransformer


def embed_corpus(
    df: pd.DataFrame,
    model_name: str,
    batch_size: int = 256,
    adapter_name: str | None = None,
    out_path: str | None = None
) -> np.ndarray:
    """Encode title and abstract using SentenceTransformers (with automatic CUDA GPU scaling and cache check)."""
    # Instant cache verification: if embeddings.npy already exists and matches dataset length, skip!
    if out_path and os.path.exists(out_path) and os.path.getsize(out_path) > 1000:
        try:
            cached_arr = np.load(out_path, mmap_mode="r")
            if cached_arr.shape[0] == len(df) and cached_arr.shape[1] == 768:
                print(f"Verified pre-computed embeddings at '{out_path}' ({round(os.path.getsize(out_path)/(1024*1024), 2)} MB). Skipping embedding generation!")
                return np.load(out_path)
        except Exception:
            pass # Re-compute if file read fails

    device = "cuda" if torch.cuda.is_available() else "cpu"
    if device == "cuda":
        gpu_name = torch.cuda.get_device_name(0)
        vram_gb = round(torch.cuda.get_device_properties(0).total_memory / (1024**3), 2)
        print(f"CUDA Active: utilizing GPU '{gpu_name}' ({vram_gb} GB VRAM) for high-speed batched embedding.")
    else:
        print("Notice: CUDA device not active; proceeding with CPU inference.")

    print(f"Loading embedding model: {model_name} on device '{device}'...")
    model = SentenceTransformer(model_name, device=device)
    
    if adapter_name and hasattr(model, "load_adapter"):
        try:
            print(f"Attaching PEFT adapter: {adapter_name}...")
            model.load_adapter(adapter_name)
        except Exception as e:
            print(f"Notice: Could not load adapter '{adapter_name}' ({e}). Proceeding with base model embeddings.")
    
    texts = (df["title"].fillna("") + ". " + df["abstract"].fillna("")).tolist()
    print(f"Encoding {len(texts)} papers with batch size {batch_size} on {device.upper()}...")
    
    embeddings = model.encode(
        texts,
        batch_size=batch_size,
        show_progress_bar=True,
        normalize_embeddings=True,
        convert_to_numpy=True,
    )
    res = embeddings.astype("float32")
    if out_path:
        Path(out_path).parent.mkdir(parents=True, exist_ok=True)
        np.save(out_path, res)
        print(f"Saved new embeddings (shape: {res.shape}) to {out_path}.")
    return res


def generate_embeddings(config_path="config.yaml") -> np.ndarray:
    """Execute embedding generation directly from config with intelligent cache bypass."""
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
        
    interim_path = config["paths"]["interim_data"]
    out_path = config["paths"]["embeddings"]
    model_name = config["embedding"]["model_name"]
    adapter_name = config["embedding"].get("adapter_name")
    batch_size = config["embedding"].get("batch_size", 256)
    
    print(f"Loading dataset from {interim_path}...")
    df = pd.read_parquet(interim_path)
    
    embeddings = embed_corpus(df, model_name=model_name, batch_size=batch_size, adapter_name=adapter_name, out_path=out_path)
    return embeddings


if __name__ == "__main__":
    generate_embeddings()
