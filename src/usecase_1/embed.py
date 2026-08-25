"""Semantic embedding module using SPECTER2 with CUDA optimization and Pinecone ingestion."""

import os
from pathlib import Path
import numpy as np
import pandas as pd
import yaml
import torch
import time
from sentence_transformers import SentenceTransformer
from pinecone import Pinecone, ServerlessSpec

# Import API key
from src.config import PINECONE_API_KEY


def embed_corpus(
    df: pd.DataFrame,
    model_name: str,
    index_name: str,
    dimension: int = 768,
    batch_size: int = 256,
    adapter_name: str | None = None,
) -> None:
    """Encode title and abstract using SentenceTransformers and upsert to Pinecone."""
    pc = Pinecone(api_key=PINECONE_API_KEY)

    existing_indexes = [index.name for index in pc.list_indexes()]
    if index_name not in existing_indexes:
        print(f"Creating Pinecone index '{index_name}' with dimension {dimension}...")
        pc.create_index(
            name=index_name,
            dimension=dimension,
            metric="cosine", 
            spec=ServerlessSpec(
                cloud="aws",
                region="us-east-1" 
            )
        )
        while not pc.describe_index(index_name).status['ready']:
            time.sleep(1)

    index = pc.Index(index_name)

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
            print(f"Attaching adapter: {adapter_name}...")
            model.load_adapter(adapter_name)
        except Exception as e:
            print(f"Notice: Could not load adapter '{adapter_name}' ({e}).")
            print("The allenai/specter2 adapter is built on an outdated framework and cannot be loaded by modern PEFT. Proceeding with base model embeddings instead.")
    
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
    
    # Upsert to Pinecone
    print("Upserting vectors to Pinecone...")
    vectors_to_upsert = []
    
    for idx, emb in enumerate(res):
        vector_id = str(idx) # Using the integer index as string
        vector_values = emb.tolist()
        vectors_to_upsert.append((vector_id, vector_values))

    PINECONE_BATCH_SIZE = 200
    for i in range(0, len(vectors_to_upsert), PINECONE_BATCH_SIZE):
        batch = vectors_to_upsert[i:i + PINECONE_BATCH_SIZE]
        index.upsert(vectors=batch)
        if i % (PINECONE_BATCH_SIZE * 5) == 0 and i > 0:
            print(f"Upserted {i} vectors...")

    print(f"Successfully upserted {len(vectors_to_upsert)} vectors to Pinecone index '{index_name}'.")


def generate_embeddings(config_path="config.yaml") -> None:
    """Execute embedding generation directly from config and upsert to Pinecone."""
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
        
    interim_path = config["paths"]["interim_data"]
    
    model_name = config["embedding"]["model_name"]
    adapter_name = config["embedding"].get("adapter_name")
    batch_size = config["embedding"].get("batch_size", 256)
    pinecone_index = config["embedding"].get("pinecone_index", "papertrail-papers")
    pinecone_dim = config["embedding"].get("pinecone_dimension", 768)
    
    print(f"Loading dataset from {interim_path}...")
    df = pd.read_parquet(interim_path)
    
    embed_corpus(
        df, 
        model_name=model_name, 
        index_name=pinecone_index, 
        dimension=pinecone_dim,
        batch_size=batch_size, 
        adapter_name=adapter_name
    )


if __name__ == "__main__":
    generate_embeddings()
