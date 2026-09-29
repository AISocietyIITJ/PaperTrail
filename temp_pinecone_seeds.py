import os
import sys
import math
from dotenv import load_dotenv
from neo4j import GraphDatabase
from pinecone import Pinecone
from sentence_transformers import SentenceTransformer

# Load environment variables
load_dotenv()
from src.config import AURA_URI, AURA_USER, AURA_PASSWORD, yaml_config

NEO4J_URI = os.getenv("NEO4J_URI") or AURA_URI
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME") or os.getenv("NEO4J_USER") or AURA_USER
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD") or AURA_PASSWORD
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_NAME = yaml_config.get("embedding", {}).get("pinecone_index", os.getenv("PINECONE_INDEX_NAME", "papertrail-papers"))


def test_pinecone_seeds(query_text, top_k=25):
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))
    
    print(f"\n[1] Loading SPECTER2 model and embedding query: '{query_text}'")
    model = SentenceTransformer('allenai/specter2_base')
    query_embedding = model.encode(query_text).tolist()
    
    print(f"[2] Searching Pinecone index '{PINECONE_INDEX_NAME}' for top 1500 semantic matches to bypass corrupted data...")
    pc = Pinecone(api_key=PINECONE_API_KEY)
    index = pc.Index(PINECONE_INDEX_NAME)
    
    response = index.query(
        vector=query_embedding,
        top_k=1500,
        include_metadata=True
    )
    
    candidates = []
    print("\n[3] Reranking using Neo4j Influence Score (s_node)...")
    
    with driver.session() as session:
        # Extract all pids and create a mapping for semantic scores and titles
        pinecone_map = {}
        for match in response['matches']:
            pid = match['id']
            pinecone_map[pid] = {
                'title': match['metadata'].get('title', 'Unknown Title'),
                'semantic_score': match['score']
            }
        
        pids = list(pinecone_map.keys())
        
        # Fetch all records in a single batch query to prevent timeouts
        result = session.run(
            "MATCH (p:Paper) WHERE p.paperId IN $pids RETURN p.paperId AS pid, p.s_node AS s_node, p.abstract AS abstract",
            pids=pids,
        )
        
        for record in result:
            pid = record["pid"]
            abstract = record.get("abstract")
            
            # Filter out junk PDF fragments by requiring a valid abstract
            if not abstract or len(str(abstract).strip()) < 20:
                continue
                
            s_node = record.get("s_node") or 0.0
            
            # Map back to Pinecone scores
            semantic_score = pinecone_map[pid]['semantic_score']
            title = pinecone_map[pid]['title']
            
            # Reranking math: Base Score + Influence Tie-breaker
            rerank_score = semantic_score + (0.02 * math.log(s_node + 1.0))
            candidates.append((rerank_score, pid, title, semantic_score, s_node))
                
    # Sort by the combined Rerank Score
    candidates.sort(key=lambda x: x[0], reverse=True)
    
    print(f"\n{'='*80}")
    print(f"--- TOP {top_k} SEED PAPERS ---")
    print(f"{'='*80}")
    
    for i, (score, pid, title, sem_score, s_node) in enumerate(candidates[:top_k], 1):
        # Clean title for Windows terminal
        safe_title = title.encode('ascii', 'replace').decode('ascii')
        print(f"Seed {i}: {safe_title}")
        print(f"  |- ID: {pid}")
        print(f"  |- Semantic Match: {sem_score:.4f}")
        print(f"  |- Influence Score: {s_node:.4f}")
        print(f"  |- Final Reranked Score: {score:.4f}\n")
        
    driver.close()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
        test_pinecone_seeds(query)
    else:
        print("Please provide a query string. Example: python temp_pinecone_seeds.py \"graph neural networks\"")
