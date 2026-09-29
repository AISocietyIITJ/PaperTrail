import os
from neo4j import GraphDatabase

# Import connection details just like precompute_costs.py
from src.config import AURA_URI, AURA_USER, AURA_PASSWORD

NEO4J_URI = os.getenv("NEO4J_URI") or AURA_URI
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME") or os.getenv("NEO4J_USER") or AURA_USER
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD") or AURA_PASSWORD

def run_analysis():
    print(f"Connecting to Neo4j at {NEO4J_URI}...")
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))
    
    node_label = "Paper"
    rel_type = "CITES"
    
    print("\n==================================================")
    print("Neo4j Graph Data Analysis Report")
    print("==================================================\n")
    
    try:
        with driver.session() as session:
            # --- NODE ANALYSIS ---
            print(f"--- Node Analysis (:{node_label}) ---")
            total_nodes = session.run(f"MATCH (n:{node_label}) RETURN count(n) AS c").single()["c"]
            print(f"Total {node_label} nodes: {total_nodes}\n")
            
            node_properties = [
                "paperId", "title", "abstract", "year", 
                "citationCount", "influentialCitationCount", 
                "nodeCost", "pagerank", "s_node"
            ]
            
            for prop in node_properties:
                # Check for NULL, or empty string (often happens with text fields)
                query = f"""
                MATCH (n:{node_label})
                WHERE n.{prop} IS NULL OR toString(n.{prop}) = ''
                RETURN count(n) AS c
                """
                missing_count = session.run(query).single()["c"]
                pct = (missing_count / total_nodes * 100) if total_nodes > 0 else 0
                
                # Highlight in red if there are missing essential fields
                warning = " (WARNING)" if missing_count > 0 and prop in ["paperId", "title", "nodeCost"] else ""
                print(f"  - Missing '{prop}': {missing_count} ({pct:.2f}%){warning}")
                
            # --- EDGE ANALYSIS ---
            print(f"\n--- Edge Analysis ([:{rel_type}]) ---")
            total_edges = session.run(f"MATCH ()-[r:{rel_type}]->() RETURN count(r) AS c").single()["c"]
            print(f"Total {rel_type} edges: {total_edges}\n")
            
            edge_properties = [
                "isInfluential", "intents", "cos_similarity", 
                "edgeCost", "traversalCost", "W_intent", "M_inf", "score"
            ]
            
            for prop in edge_properties:
                # Intents is an array, so check if it's empty
                if prop == "intents":
                    query = f"MATCH ()-[r:{rel_type}]->() WHERE r.{prop} IS NULL OR size(r.{prop}) = 0 RETURN count(r) AS c"
                else:
                    query = f"MATCH ()-[r:{rel_type}]->() WHERE r.{prop} IS NULL RETURN count(r) AS c"
                
                missing_count = session.run(query).single()["c"]
                pct = (missing_count / total_edges * 100) if total_edges > 0 else 0
                
                warning = " (WARNING)" if missing_count > 0 and prop in ["cos_similarity", "edgeCost", "traversalCost"] else ""
                print(f"  - Missing '{prop}': {missing_count} ({pct:.2f}%){warning}")
                
            print("\n==================================================")
            print("Analysis Complete.")
            
    finally:
        driver.close()

if __name__ == "__main__":
    if not NEO4J_PASSWORD:
        print("WARNING: Neo4j password is not set in environment or config. Connection may fail.")
    try:
        run_analysis()
    except Exception as e:
        print(f"\nError connecting to Neo4j or running query:\n{e}")
