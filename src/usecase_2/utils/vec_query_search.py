from sentence_transformers import SentenceTransformer
from pinecone import Pinecone, ServerlessSpec
import time
from src.config import PINECONE_API_KEY
from src.logger import logger


INDEX_NAME = "interest-granite-125m"
VECTOR_DIMENSION = 768  


_embedding_model = None

def user_query_to_embd(text: str):
    global _embedding_model
    if _embedding_model is None:
        logger.info("Loading SentenceTransformer model: ibm-granite/granite-embedding-125m-english")
        try:
            _embedding_model = SentenceTransformer("ibm-granite/granite-embedding-125m-english")
        except Exception:
            logger.exception("Failed to load embedding model")
            raise
        logger.info("Embedding model loaded successfully")

    logger.debug(f"Generating embedding for text: {text!r}")
    embeddings = _embedding_model.encode(text, normalize_embeddings=True)
    return embeddings


def search_vector_db(text: str):
    logger.info("Connecting to Pinecone")
    pc = Pinecone(api_key=PINECONE_API_KEY)

    existing_indexes = [index.name for index in pc.list_indexes()]
    logger.debug(f"Existing Pinecone indexes: {existing_indexes}")

    if INDEX_NAME not in existing_indexes:
        logger.info(f"Index '{INDEX_NAME}' not found, creating it")
        try:
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
                logger.debug(f"Waiting for index '{INDEX_NAME}' to become ready...")
                time.sleep(1)
            logger.info(f"Index '{INDEX_NAME}' created and ready")
        except Exception:
            logger.exception(f"Failed to create Pinecone index '{INDEX_NAME}'")
            raise

    index = pc.Index(INDEX_NAME)

    logger.info("Generating query embedding")
    query_vector = user_query_to_embd(text)
    query_vector = query_vector.tolist()

    logger.info(f"Querying Pinecone index '{INDEX_NAME}' (top_k=10)")
    try:
        query_response = index.query(
            vector=query_vector,
            top_k=10,
            include_metadata=True,
            include_values=False,
        )
    except Exception:
        logger.exception("Pinecone query failed")
        raise

    logger.debug(f"Raw query response has {len(query_response['matches'])} matches")

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
        if float(match['score']) >= 0.5:
            vector_ids.append({"vector_id": match['id'], "score": match['score']})

    logger.info(f"Selected {len(vector_ids)} matches above score threshold 0.5")
    logger.debug(f"Selected vector IDs: {vector_ids}")

    return vector_ids