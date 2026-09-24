import os
import networkx as nx
from itertools import combinations
from dotenv import load_dotenv
from neo4j import GraphDatabase
from pinecone import Pinecone
from sentence_transformers import SentenceTransformer

# Import NEWST logic
from src.usecase_1.newst import reallocate_seeds, newst_heuristic, get_reading_path

from src.config import PINECONE_API_KEY, AURA_URI, AURA_USER, AURA_PASSWORD, yaml_config

from dotenv import load_dotenv
load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI") or AURA_URI
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME") or os.getenv("NEO4J_USER") or AURA_USER
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD") or AURA_PASSWORD

# Fallback to env var if not in config.yaml
PINECONE_INDEX_NAME = yaml_config.get("embedding", {}).get("pinecone_index", os.getenv("PINECONE_INDEX_NAME", "paper-embeddings"))

# NEWST Constants (from RePaGer experimental results)
ALPHA = 3.0
BETA = 2.0
GAMMA = 5.0
A = 0.7
B = 0.3

def search_pinecone(driver, query_text, top_k=4):
    """
    Embeds the user query using SPECTER2 and searches the Pinecone index.
    """
    print(f"\n[Pinecone] Loading SPECTER2 model and embedding query: '{query_text}'")
    # Load the recommended base model for SPECTER2
    model = SentenceTransformer('allenai/specter2_base')
    query_embedding = model.encode(query_text).tolist()
    
    import math
    print(f"[Pinecone] Searching index '{PINECONE_INDEX_NAME}' for top 15 semantic matches...")
    pc = Pinecone(api_key=PINECONE_API_KEY)
    index = pc.Index(PINECONE_INDEX_NAME)
    
    response = index.query(
        vector=query_embedding,
        top_k=15,
        include_metadata=True
    )
    
    candidates = []
    with driver.session() as session:
        for match in response['matches']:
            title = match['metadata'].get('title', 'Unknown Title')
            semantic_score = match['score']
            
            # Fetch paperId and s_node to rerank
            result = session.run("MATCH (p:Paper) WHERE p.title = $title RETURN p.paperId AS pid, p.s_node AS s_node", title=title)
            record = result.single()
            
            if record and record["pid"]:
                s_node = record.get("s_node") or 0.0
                # We use a gentle addition for influence. 
                # Semantic score is ~0.7 to 1.0. 
                # log(s_node + 1) is usually 0 to 5. 
                # Multiplying by 0.02 gives a max bonus of ~0.1, acting as a strong tie-breaker
                # without letting heavily cited but irrelevant papers win.
                rerank_score = semantic_score + (0.02 * math.log(s_node + 1.0))
                candidates.append((rerank_score, record["pid"], title, semantic_score))
                
    # Sort by the new Rerank Score (Influence * Relevance)
    candidates.sort(key=lambda x: x[0], reverse=True)
    
    target_ids = []
    print("\n[Reranking] Top 4 Seeds selected after balancing Relevance & Influence:")
    for score, pid, title, sem_score in candidates[:top_k]:
        safe_title = title.encode('ascii', 'replace').decode('ascii')
        print(f"  -> {safe_title} (Semantic: {sem_score:.2f}, Reranked Score: {score:.2f})")
        target_ids.append(pid)
                    
    print(f"\n[Debug] target_ids collected: {target_ids}")
    return target_ids

def extract_subgraph(driver, target_ids):
    """
    Walks backward 2 hops from the target papers to extract their prerequisites.
    """
    print("\n[Neo4j] Extracting 2-hop prerequisite subgraph...")
    
    # CITES*0..2 means it will grab the seeds themselves (0 hops) 
    # plus everything they cite up to 2 layers deep.
    query = """
    MATCH path = (seed:Paper)-[:CITES*0..2]->(prereq:Paper)
    WHERE seed.paperId IN $target_ids
    AND (prereq.citationCount >= 50 OR prereq.paperId IN $target_ids)
    RETURN nodes(path) AS nodes, relationships(path) AS edges
    """
    
    G = nx.DiGraph()
    
    with driver.session() as session:
        # Debug: Check if the nodes actually exist in Neo4j
        total_res = session.run("MATCH (p:Paper) RETURN count(p) as c")
        total_nodes = total_res.single()['c']
        print(f"[Debug] Total Paper nodes in Neo4j database: {total_nodes}")
        
        debug_res = session.run("MATCH (p:Paper) WHERE p.paperId IN $t RETURN count(p) as c", t=target_ids)
        print(f"[Debug] Found {debug_res.single()['c']} out of {len(target_ids)} seed nodes in Neo4j.")
        
        result = session.run(query, target_ids=target_ids)
        for record in result:
            for node in record["nodes"]:
                n_id = node["paperId"]
                if not G.has_node(n_id):
                    G.add_node(
                        n_id,
                        title=node.get("title", "Unknown Title"),
                        year=node.get("year", 0) or 0,
                        citationCount=node.get("citationCount", 0) or 0,
                        nodeCost=node.get("nodeCost"),
                    )
            
            for edge in record["edges"]:
                start_node = edge.start_node["paperId"]
                end_node = edge.end_node["paperId"]
                # Neo4j -[:CITES]-> means start_node CITES end_node
                G.add_edge(
                    start_node, end_node,
                    edgeCost=edge.get("edgeCost"),
                    traversalCost=edge.get("traversalCost"),
                )
                
    print(f"  -> Subgraph extracted: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
    return G

def compute_graph_weights(G):
    """
    Computes node and edge weights exactly as described in the RePaGer paper,
    using subgraph_centrality to find local importance.
    """
    print("[Weighting] Computing node and edge costs...")
    
    if G.number_of_nodes() == 0:
        return

    # ── Check for precomputed NEWST costs from Neo4j ──────────────────────
    has_node_costs = any(
        G.nodes[n].get("nodeCost") is not None for n in G.nodes()
    )
    has_edge_costs = (
        G.number_of_edges() > 0
        and any(G.edges[u, v].get("edgeCost") is not None for u, v in G.edges())
    )

    if has_node_costs and has_edge_costs:
        print("  -> Using precomputed NEWST costs from Neo4j.")
        for n in G.nodes():
            G.nodes[n]['weight'] = G.nodes[n].get('nodeCost') or (GAMMA / 0.0001)
        for u, v in G.edges():
            G.edges[u, v]['weight'] = G.edges[u, v].get('edgeCost') or (ALPHA / 0.0001)
        return

    print("  -> No precomputed costs found. Computing locally (run precompute_costs.py for better results).")

    # --- Node Weights ---
    # 1. Subgraph Centrality (in-degree within THIS specific graph)
    centrality = {n: G.in_degree(n) for n in G.nodes()}
    max_cent = max(centrality.values()) if centrality else 1
    if max_cent == 0: max_cent = 1
    
    # 2. Global Citations
    citations = {n: G.nodes[n].get("citationCount", 0) for n in G.nodes()}
    max_cit = max(citations.values()) if citations else 1
    if max_cit == 0: max_cit = 1
    
    for n in G.nodes():
        cent_norm = centrality[n] / max_cent
        cit_norm = citations[n] / max_cit
        
        denom = (A * cent_norm) + (B * cit_norm)
        # Prevent divide-by-zero for totally unreferenced nodes
        if denom == 0:
            denom = 0.0001
            
        G.nodes[n]['weight'] = GAMMA / denom

    # --- Edge Weights ---
    # Co-citation frequency: how many papers cite BOTH u and v.
    co_citation = {}
    for node in G.nodes():
        refs = list(G.successors(node))
        for r1, r2 in combinations(refs, 2):
            pair = (min(r1, r2), max(r1, r2))
            co_citation[pair] = co_citation.get(pair, 0) + 1
            
    for u, v in G.edges():
        pair = (min(u, v), max(u, v))
        co_count = co_citation.get(pair, 0)
        
        # If co_count is 0, we give a base value (e.g. 0.5) so cost becomes high but not infinite
        co_count = max(0.5, co_count)
        
        edge_weight = ALPHA / (co_count ** BETA)
        G.edges[u, v]['weight'] = edge_weight

def format_output(reading_path_ids, G):
    """
    Takes the ordered topological sort IDs and prints a nice timeline,
    and returns it as a list of dicts.
    """
    print("\n" + "="*80)
    print("--- STRUCTURED READING PATH GENERATED ---")
    print("="*80)
    
    structured_path = []
    
    for i, pid in enumerate(reading_path_ids, 1):
        paper = G.nodes[pid]
        year = paper.get("year", "N/A")
        title = paper.get("title", "Unknown Title")
        citations = paper.get("citationCount", 0)
        
        safe_title = title.encode('ascii', 'replace').decode('ascii')
        print(f"Step {i:02d} | [{year}] {safe_title}")
        print(f"         |- (Global Citations: {citations:,})")
        
        structured_path.append({
            "step": i,
            "year": year,
            "title": title,
            "citations": citations,
            "paperId": pid,
            "abstract": paper.get("abstract", "")
        })
    
    print("="*80 + "\n")
    return structured_path

def generate_reading_path(query_text):
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))
    
    try:
        # 1. Get targets from Pinecone (Vector Search)
        target_ids = search_pinecone(driver, query_text, top_k=4)
        
        if not target_ids:
            print("No initial seeds found. Try a different query.")
            return []
            
        # 2. Extract Subgraph
        G = extract_subgraph(driver, target_ids)
        
        if G.number_of_nodes() == 0:
            print("Subgraph is empty. Graph traversal failed.")
            return []
            
        # 3. Compute all edge/node weights
        compute_graph_weights(G)
        
        # 4. Reallocate seeds (find compulsory terminals)
        print("[NEWST] Reallocating seeds to find compulsory prerequisites...")
        initial_seeds_dict = [{'paperId': pid} for pid in target_ids]
        compulsory_nodes = reallocate_seeds(G, initial_seeds_dict, co_occurrence_threshold=2)
        print(f"  -> Found {len(compulsory_nodes)} compulsory terminal nodes.")
        
        # 5. NEWST Algorithm
        print("[NEWST] Running Steiner Tree heuristic...")
        mst = newst_heuristic(G, compulsory_nodes)
        
        if mst.number_of_nodes() == 0:
            print("Warning: NEWST returned an empty tree.")
            return []
            
        # 6. Topological Sort for Reading Order
        print("[NEWST] Extracting reading path topological order...")
        reading_path_ids = get_reading_path(G, mst)
        
        # Reverse the path so foundational prerequisites (older papers) come first
        reading_path_ids.reverse()
        
        # 7. Print to user and return
        return format_output(reading_path_ids, G)
        
    finally:
        driver.close()

if __name__ == "__main__":
    import sys
    query = sys.argv[1] if len(sys.argv) > 1 else "Attention is All you Need"
    generate_reading_path(query)
