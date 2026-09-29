import os
import networkx as nx
import math
from itertools import combinations
from dotenv import load_dotenv
from neo4j import GraphDatabase
from pinecone import Pinecone
from sentence_transformers import SentenceTransformer

# Import NEWST logic
from src.usecase_1.newst import reallocate_seeds, newst_heuristic, get_reading_path

from src.config import PINECONE_API_KEY, AURA_URI, AURA_USER, AURA_PASSWORD, yaml_config

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI") or AURA_URI
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME") or os.getenv("NEO4J_USER") or AURA_USER
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD") or AURA_PASSWORD

# Fallback to env var if not in config.yaml
PINECONE_INDEX_NAME = yaml_config.get("embedding", {}).get("pinecone_index", os.getenv("PINECONE_INDEX_NAME", "papertrail-papers"))

# NEWST Constants (from RePaGer experimental results)
ALPHA = 3.0
BETA = 2.0
GAMMA = 5.0
A = 0.7
B = 0.3

def search_pinecone(driver, query_text, top_k=4):
    """
    Embeds the user query using SPECTER2 and searches the Pinecone index.
    Reranks results using Semantic Score + Influence (s_node) tie-breaker.
    """
    print(f"\n[Pinecone] Loading SPECTER2 model and embedding query: '{query_text}'")
    model = SentenceTransformer('allenai/specter2_base')
    query_embedding = model.encode(query_text).tolist()
    
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
            
            result = session.run(
                "MATCH (p:Paper) WHERE p.title = $title RETURN p.paperId AS pid, p.s_node AS s_node LIMIT 1",
                title=title,
            )
            record = result.single()
            
            if record and record["pid"]:
                s_node = record.get("s_node") or 0.0
                
                # Base Score + Influence Tie-breaker
                # Semantic score is ~0.7–1.0; log(s_node+1) is ~0–5.
                # Multiplying by 0.02 gives a max bonus of ~0.1.
                rerank_score = semantic_score + (0.02 * math.log(s_node + 1.0))
                    
                candidates.append((rerank_score, record["pid"], title, semantic_score))
                
    # Sort by the combined Rerank Score
    candidates.sort(key=lambda x: x[0], reverse=True)
    
    target_ids = []
    print("\n[Reranking] Top 4 Seeds selected (Semantic + Influence):")
    for score, pid, title, sem_score in candidates[:top_k]:
        safe_title = title.encode('ascii', 'replace').decode('ascii')
        print(f"  -> {safe_title} (Semantic: {sem_score:.4f}, Reranked: {score:.4f})")
        target_ids.append(pid)
                    
    print(f"\n[Debug] target_ids collected: {target_ids}")
    return target_ids

def extract_subgraph(driver, target_ids):
    """
    Walks backward 2 hops from the target papers to extract their prerequisites.
    Quality Control: only keeps nodes with citationCount >= 50 (or seed nodes).
    """
    print("\n[Neo4j] Extracting 2-hop prerequisite subgraph...")
    
    # We fetch all paths first, then filter nodes in Python.
    # This avoids the Neo4j bug where the citationCount filter only applies
    # to the endpoint of the path, letting junk intermediate nodes through.
    query = """
    MATCH path = (seed:Paper)-[:CITES*0..2]->(prereq:Paper)
    WHERE seed.paperId IN $target_ids
    WITH nodes(path) AS ns, relationships(path) AS rs
    RETURN [n IN ns | {paperId: n.paperId, title: n.title, year: n.year,
                       citationCount: n.citationCount, influentialCitationCount: n.influentialCitationCount, nodeCost: n.nodeCost}] AS nodes,
           [r IN rs | {start: startNode(r).paperId, end: endNode(r).paperId,
                       edgeCost: r.edgeCost, traversalCost: r.traversalCost}] AS edges
    """
    
    G = nx.DiGraph()
    seed_set = set(target_ids)
    
    with driver.session() as session:
        result = session.run(query, target_ids=target_ids)
        for record in result:
            for node in record["nodes"]:
                n_id = node["paperId"]
                if n_id is None:
                    continue
                if not G.has_node(n_id):
                    # Use the year field directly (already returned as int from Neo4j)
                    year = node.get("year") or 0
                    if not isinstance(year, int):
                        try:
                            year = int(year)
                        except (ValueError, TypeError):
                            year = 0
                    
                    citation_count = node.get("citationCount") or 0
                    influential_count = node.get("influentialCitationCount") or 0
                    
                    # Quality Control: skip low-citation papers unless they are seeds
                    if citation_count < 500 and influential_count < 50 and n_id not in seed_set:
                        continue
                    
                    G.add_node(
                        n_id,
                        title=node.get("title", "Unknown Title"),
                        year=year,
                        citationCount=citation_count,
                        influentialCitationCount=influential_count,
                        nodeCost=node.get("nodeCost"),
                    )
            
            for edge in record["edges"]:
                start_node = edge["start"]
                end_node = edge["end"]
                # Only add edges between nodes that passed the quality filter
                if start_node is not None and end_node is not None:
                    if G.has_node(start_node) and G.has_node(end_node):
                        G.add_edge(
                            start_node, end_node,
                            edgeCost=edge.get("edgeCost"),
                            traversalCost=edge.get("traversalCost"),
                        )
                
    print(f"  -> Subgraph extracted: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
    return G

def compute_graph_weights(G):
    """
    Computes node and edge weights exactly as described in the RePaGer paper.
    """
    print("[Weighting] Computing node and edge costs...")
    
    if G.number_of_nodes() == 0:
        return

    has_node_costs = any(G.nodes[n].get("nodeCost") is not None for n in G.nodes())
    has_edge_costs = (
        G.number_of_edges() > 0
        and any(G.edges[u, v].get("edgeCost") is not None for u, v in G.edges())
    )

    if has_node_costs and has_edge_costs:
        print("  -> Using precomputed NEWST costs from Neo4j.")
        for n in G.nodes():
            nc = G.nodes[n].get('nodeCost')
            # Use a sensible fallback (median-ish cost) instead of extreme 50000
            G.nodes[n]['weight'] = nc if nc is not None else 10.0
        for u, v in G.edges():
            ec = G.edges[u, v].get('edgeCost')
            G.edges[u, v]['weight'] = ec if ec is not None else 12.0
        return

    print("  -> No precomputed costs found. Computing locally.")
    centrality = {n: G.in_degree(n) for n in G.nodes()}
    max_cent = max(centrality.values()) if centrality else 1
    if max_cent == 0:
        max_cent = 1
    
    citations = {n: G.nodes[n].get("citationCount", 0) for n in G.nodes()}
    max_cit = max(citations.values()) if citations else 1
    if max_cit == 0:
        max_cit = 1
    
    for n in G.nodes():
        cent_norm = centrality[n] / max_cent
        cit_norm = citations[n] / max_cit
        denom = (A * cent_norm) + (B * cit_norm)
        if denom == 0:
            denom = 0.0001
        G.nodes[n]['weight'] = GAMMA / denom

    co_citation = {}
    for node in G.nodes():
        refs = list(G.successors(node))
        for r1, r2 in combinations(refs, 2):
            pair = (min(r1, r2), max(r1, r2))
            co_citation[pair] = co_citation.get(pair, 0) + 1
            
    for u, v in G.edges():
        pair = (min(u, v), max(u, v))
        co_count = co_citation.get(pair, 0)
        co_count = max(0.5, co_count)
        G.edges[u, v]['weight'] = ALPHA / (co_count ** BETA)

def format_output(reading_path_ids, G, DAG):
    print("\n" + "="*80)
    print("--- TOPOLOGICAL READING PATH GENERATED ---")
    print("="*80)
    
    structured_path = []
    
    for i, pid in enumerate(reading_path_ids, 1):
        if pid not in G.nodes:
            continue
        paper = G.nodes[pid]
        year = paper.get("year", "N/A")
        title = paper.get("title", "Unknown Title")
        citations = paper.get("citationCount", 0)
        
        safe_title = title.encode('ascii', 'replace').decode('ascii')
        print(f"Step {i:02d} | [{year}] {safe_title}")
        print(f"         |- (Global Citations: {citations:,})")
        
        prereqs = []
        if DAG is not None and DAG.has_node(pid):
            # In our graph, edges are citer -> cited. So successors are the prerequisites.
            for prereq_id in DAG.successors(pid):
                prereq_title = G.nodes[prereq_id].get("title", "Unknown")
                prereqs.append({"paperId": prereq_id, "title": prereq_title})
                
        if prereqs:
            print("         |- Directly builds upon:")
            for p in prereqs:
                safe_p_title = p["title"].encode('ascii', 'replace').decode('ascii')
                print(f"            * {safe_p_title}")
        
        structured_path.append({
            "step": i,
            "year": year,
            "title": title,
            "citations": citations,
            "paperId": pid,
            "prerequisites": prereqs
        })
    
    print("="*80 + "\n")
    return structured_path

def generate_reading_path(query_text):
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))
    
    try:
        target_ids = search_pinecone(driver, query_text, top_k=4)
        if not target_ids:
            print("No initial seeds found. Try a different query.")
            return []
            
        G = extract_subgraph(driver, target_ids)
        if G.number_of_nodes() == 0:
            print("Subgraph is empty. Graph traversal failed.")
            return []
            
        compute_graph_weights(G)
        
        print("[NEWST] Reallocating seeds to find compulsory prerequisites...")
        initial_seeds_dict = [{'paperId': pid} for pid in target_ids]
        compulsory_nodes = reallocate_seeds(G, initial_seeds_dict, co_occurrence_threshold=2)
        print(f"  -> Found {len(compulsory_nodes)} compulsory terminal nodes.")
        
        print("[NEWST] Running Steiner Tree heuristic...")
        final_mst = newst_heuristic(G, set(compulsory_nodes))
        
        print("[NEWST] Extracting reading path topological order...")
        reading_path_ids, DAG = get_reading_path(G, final_mst)
        
        reading_path_ids.reverse()
        return format_output(reading_path_ids, G, DAG)
        
    finally:
        driver.close()

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
        generate_reading_path(query)
    else:
        print("Please provide a query string.")