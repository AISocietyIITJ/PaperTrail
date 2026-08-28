import pandas as pd
from sentence_transformers import SentenceTransformer
from pinecone import Pinecone, ServerlessSpec
import os
import time
from src.config import PINECONE_API_KEY

from src.logger import logger
 
 
script_dir = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(script_dir, "../../../data/professor_updated1.csv")
 
INDEX_NAME = "prof-profile"
VECTOR_DIMENSION = 1024 
 
def gen_prof_emb_ingestion():
    pc = Pinecone(api_key=PINECONE_API_KEY)
 
    existing_indexes = [index.name for index in pc.list_indexes()]
    if INDEX_NAME not in existing_indexes:
        logger.info(f"Creating Pinecone index '{INDEX_NAME}' with dimension {VECTOR_DIMENSION}...")
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
    logger.info(f"Loading professor profiles from {file_path}...")
    df = pd.read_csv(file_path)
 
    df['Combined_Text'] = df['Affiliation'].fillna('') + ": " + df['Interests'].fillna('')
 
    logger.info("Building sentence embeddings")
    model = SentenceTransformer("Qwen/Qwen3-Embedding-0.6B")  
    embeddings = model.encode(df['Combined_Text'].tolist(), normalize_embeddings=True)
 
    vectors_to_upsert = []
    vector_ids = []
 
    for idx, row in df.iterrows():
        vector_id = f"interest_{idx}"
        vector_ids.append(vector_id)
        
        vector_values = embeddings[idx].tolist()
        
        metadata = {
            "interest": str(row['Interests']),
            "Prof_name":str(row['Name'])
        }
        
        vectors_to_upsert.append((vector_id, vector_values, metadata))
 
    BATCH_SIZE = 100
    logger.info(f"Upserting {len(vectors_to_upsert)} vectors to Pinecone")
    for i in range(0, len(vectors_to_upsert), BATCH_SIZE):
        batch = vectors_to_upsert[i:i + BATCH_SIZE]
        index.upsert(vectors=batch)
        logger.debug(f"Upserted batch {i} to {min(i + BATCH_SIZE, len(vectors_to_upsert))}")
 
    logger.info("[OK] Pinecone ingestion complete")
 
    df['vector_id'] = vector_ids
    df_final = df[['Name','Affiliation','Interests','Cited By','Profile URL','h-index','i10-index','vector_id']]
    df_final.to_csv(file_path, index=False)
    logger.info("[OK] Updated professor_updated1.csv with vector IDs")
 
if __name__ == "__main__":
    gen_prof_emb_ingestion()
