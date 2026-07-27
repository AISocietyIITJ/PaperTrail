import pandas as pd
from sentence_transformers import SentenceTransformer
import numpy as np
from pinecone import Pinecone, ServerlessSpec
import os
import time
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from config import pinecone


script_dir = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(script_dir, "../../data/professor_updated1.csv")

PINECONE_API_KEY = pinecone 
INDEX_NAME = "prof-profile"
VECTOR_DIMENSION = 384  


pc = Pinecone(api_key=PINECONE_API_KEY)


existing_indexes = [index.name for index in pc.list_indexes()]
if INDEX_NAME not in existing_indexes:
    pc.create_index(
        name=INDEX_NAME,
        dimension=VECTOR_DIMENSION,
        metric="cosine", 
        spec=ServerlessSpec(
            cloud="aws",
            region="us-east-1" 
        )
    )
    while not pc.describe_index(INDEX_NAME).status['ready']:
        time.sleep(1)


index = pc.Index(INDEX_NAME)
df = pd.read_csv(file_path)


def gen_prof_emb_ingestion():
    df['Combined_Text'] = df['Affiliation'].fillna('') + ": " + df['Interests'].fillna('')

    print("Generating sentence embeddings...")
    embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
    embeddings = embedding_model.encode(df['Combined_Text'].tolist(), normalize_embeddings=True)


    vectors_to_upsert = []
    vector_ids = []

    for idx, row in df.iterrows():

        vector_id = f"interest_{idx}"
        vector_ids.append(vector_id)
        
        vector_values = embeddings[idx].tolist()
        
        metadata = {
            "interest": str(row['Interests'])
        }
        
        vectors_to_upsert.append((vector_id, vector_values, metadata))

    BATCH_SIZE = 100
    print("Upserting vectors to Pinecone...")
    for i in range(0, len(vectors_to_upsert), BATCH_SIZE):
        batch = vectors_to_upsert[i:i + BATCH_SIZE]
        index.upsert(vectors=batch)

    print("Ingestion complete!")



    df['vector_id'] = vector_ids
    df_final = df[['Name','Affiliation','Interests','Cited By','Profile URL','h-index','i10-index','vector_id']]
    df_final.to_csv(file_path, index=False)
    print("Updated 'interests_with_aliases.csv' with vector IDs.")

gen_prof_emb_ingestion()