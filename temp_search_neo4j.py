import os
import sys
from dotenv import load_dotenv
from neo4j import GraphDatabase

# Load .env variables
load_dotenv()

from src.config import AURA_URI, AURA_USER, AURA_PASSWORD

NEO4J_URI = os.getenv("NEO4J_URI") or AURA_URI
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME") or os.getenv("NEO4J_USER") or AURA_USER
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD") or AURA_PASSWORD

def search_neo4j_directly(keyword):
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))
    
    print(f"Searching Neo4j directly for keyword: '{keyword}'...")
    
    # We use a case-insensitive search on both Title and Abstract.
    # We order by citationCount so the most important papers float to the top.
    query = """
    MATCH (p:Paper)
    WHERE toLower(p.title) CONTAINS toLower($keyword) 
       OR toLower(p.abstract) CONTAINS toLower($keyword)
    RETURN p.paperId AS paperId, p.title AS title, 
           left(p.abstract, 150) + '...' AS abstract_snippet, 
           p.citationCount AS citations
    ORDER BY p.citationCount DESC
    LIMIT 15
    """
    
    with driver.session() as session:
        result = session.run(query, keyword=keyword)
        records = list(result)
        
        if not records:
            print("No papers found matching that keyword in Neo4j.")
        
        for i, record in enumerate(records, 1):
            title = record["title"] or "Unknown"
            # Ensure windows terminal doesn't crash on weird characters
            safe_title = title.encode('ascii', 'replace').decode('ascii')
            snippet = record["abstract_snippet"] or "No abstract available"
            safe_snippet = snippet.encode('ascii', 'replace').decode('ascii').replace('\n', ' ')
            
            print(f"\n[{i}] {safe_title} (Citations: {record['citations']})")
            print(f"    Abstract: {safe_snippet}")
            print(f"    ID: {record['paperId']}")

    driver.close()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        keyword = " ".join(sys.argv[1:])
        search_neo4j_directly(keyword)
    else:
        print("Please provide a keyword to search for, e.g., python temp_search_neo4j.py transformer")
