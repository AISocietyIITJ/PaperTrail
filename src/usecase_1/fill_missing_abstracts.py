import os
import time
import requests
from neo4j import GraphDatabase
from dotenv import load_dotenv

# Explicitly load .env
load_dotenv()

from src.config import AURA_URI, AURA_USER, AURA_PASSWORD

NEO4J_URI = os.getenv("NEO4J_URI") or AURA_URI
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME") or os.getenv("NEO4J_USER") or AURA_USER
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD") or AURA_PASSWORD

# Semantic Scholar API batch endpoint (fetches up to 500 papers at once)
S2_BATCH_API_URL = "https://api.semanticscholar.org/graph/v1/paper/batch?fields=paperId,abstract"

def batched(items, size):
    for i in range(0, len(items), size):
        yield items[i : i + size]

def fill_missing_abstracts(driver):
    print("🔍 Fetching paper IDs with missing abstracts from Neo4j...")
    with driver.session() as session:
        # Get all paperIds missing abstracts
        query = """
        MATCH (p:Paper)
        WHERE p.abstract IS NULL OR toString(p.abstract) = ''
        RETURN p.paperId AS paperId
        """
        result = session.run(query)
        paper_ids = [record["paperId"] for record in result if record["paperId"]]
        
    print(f"Found {len(paper_ids)} papers missing abstracts.")
    
    if not paper_ids:
        print("No missing abstracts to process.")
        return

    updates = []
    
    # Process in batches of 500 (Semantic Scholar API limit)
    batch_size = 500
    total_batches = (len(paper_ids) // batch_size) + (1 if len(paper_ids) % batch_size != 0 else 0)
    
    print(f"🌐 Querying Semantic Scholar Batch API in {total_batches} batches...")
    for i, batch in enumerate(batched(paper_ids, batch_size)):
        print(f"  -> Processing batch {i+1}/{total_batches}...")
        
        retries = 3
        while retries > 0:
            try:
                # We use a POST request to send up to 500 IDs at once
                response = requests.post(
                    S2_BATCH_API_URL,
                    json={"ids": batch},
                    timeout=30
                )
                
                if response.status_code == 429:
                    print(f"     ⏳ Rate limit hit (429). Waiting 5 seconds before retry...")
                    time.sleep(5)
                    retries -= 1
                    continue
                    
                response.raise_for_status()
                data = response.json()
                
                # The API returns an array matching the requested IDs
                for paper in data:
                    if paper and paper.get("abstract"):
                        updates.append({
                            "paperId": paper["paperId"],
                            "abstract": paper["abstract"]
                        })
                break # Success, exit retry loop
                        
            except Exception as e:
                print(f"     ⚠️ Error fetching batch {i+1}: {e}")
                break
                
        # Polite sleep for rate limiting (Semantic Scholar restricts unauthenticated users)
        time.sleep(3.5)
        
    print(f"\n✅ Successfully retrieved {len(updates)} abstracts from Semantic Scholar.")
    
    if updates:
        print("💾 Writing updated abstracts back to Neo4j...")
        with driver.session() as session:
            # Write back in batches of 1000 for efficiency
            for batch in batched(updates, 1000):
                update_query = """
                UNWIND $batch AS row
                MATCH (p:Paper {paperId: row.paperId})
                SET p.abstract = row.abstract
                """
                session.run(update_query, batch=batch).consume()
        print("🎉 Neo4j update complete!")
    else:
        print("⚠️ No new abstracts were found to update.")

if __name__ == "__main__":
    if not NEO4J_PASSWORD:
        print("WARNING: Neo4j password is not set in environment or config. Connection may fail.")
    
    print(f"Connecting to Neo4j at {NEO4J_URI}...")
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))
    try:
        fill_missing_abstracts(driver)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
    finally:
        driver.close()
