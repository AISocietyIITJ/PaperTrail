from sentence_transformers import SentenceTransformer
from pinecone import Pinecone, ServerlessSpec
import time
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from config import pinecone


PINECONE_API_KEY = pinecone 
INDEX_NAME = "academic-interests"
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

def user_query_to_embd(text:str):

    embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
    embeddings = embedding_model.encode(text, normalize_embeddings=True)
    return embeddings

text = '3D Computer Vson'



def search_vector_db(text:str):
    query_vector = user_query_to_embd(text)
    query_vector = query_vector.tolist()

    query_response = index.query(
        vector=query_vector,
        top_k=10,                     
        include_metadata=True,       
        include_values=False, 
    )

    print("Query Results:")
    for match in query_response['matches']:
        metadata = match.get('metadata', {})
        interest = metadata.get('interest', 'N/A')
        print(f"ID: {match['id']} | Score: {match['score']} | Interest: {interest}")

    vector_ids = []
    for match in query_response['matches']:
        if(float(match['score']) >= 0.5):
            vector_ids.append(match['id'])

    return vector_ids

print(search_vector_db(text))