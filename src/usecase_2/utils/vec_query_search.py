from sentence_transformers import SentenceTransformer
from pinecone import Pinecone, ServerlessSpec
import time
from src.config import PINECONE_API_KEY


INDEX_NAME = "academic-interest"
VECTOR_DIMENSION = 384  


_embedding_model = None

def user_query_to_embd(text: str):
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
    embeddings = _embedding_model.encode(text, normalize_embeddings=True)
    return embeddings


def search_vector_db(text: str):
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

    query_vector = user_query_to_embd(text)
    query_vector = query_vector.tolist()

    query_response = index.query(
        vector=query_vector,
        top_k=10,                     
        include_metadata=True,       
        include_values=False, 
    )

    print("      Vector matches")
    print("      " + "-" * 72)
    print(f"      {'ID':<14} {'Score':<10} Interest")
    print("      " + "-" * 72)
    for match in query_response['matches']:
        metadata = match.get('metadata', {})
        interest = metadata.get('interest', 'N/A')
        print(f"      {match['id']:<14} {float(match['score']):<10.4f} {interest}")

    vector_ids = []
    for match in query_response['matches']:
        if(float(match['score']) >= 0.5):
            vector_ids.append(match['id'])

    print(f"      Selected IDs: {', '.join(vector_ids) if vector_ids else 'None'}")
    return vector_ids
