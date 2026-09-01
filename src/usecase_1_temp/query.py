import yaml
import pandas as pd
from neo4j import GraphDatabase
from sentence_transformers import SentenceTransformer
from pinecone import Pinecone
from src.config import PINECONE_API_KEY, AURA_URI, AURA_USER, AURA_PASSWORD
# Adjust this import to match where you placed logger.py relative to this file
from src.logger import logger
 
_embedding_model = None
 
def load_neo4j_driver(config_path="config.yaml"):
    global _embedding_model
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    neo_conf = config.get("neo4j", {})
    uri = AURA_URI or neo_conf.get("uri")
    user = AURA_USER or neo_conf.get("user")
    password = AURA_PASSWORD or neo_conf.get("password")
    
    logger.info(f"Connecting to Neo4j AuraDB ({uri})...")
    driver = GraphDatabase.driver(uri, auth=(user, password))
    
    if _embedding_model is None:
        model_name = config["embedding"]["model_name"]
        logger.info(f"Loading embedding model: {model_name}...")
        _embedding_model = SentenceTransformer(model_name)
        
    return config, driver, _embedding_model
 
def generate_path_neo4j(query_text: str, driver, model, max_hops=4) -> dict:
    """Uses Pinecone Vector Search to find a matching target paper in Neo4j, then traverses graph for prerequisites."""
    with open("config.yaml", "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
 
    # 1. Embed query
    logger.info(f"Embedding query: '{query_text}'...")
    query_vector = model.encode([query_text], normalize_embeddings=True)[0].tolist()
 
    # 2. Search Pinecone for candidate target papers
    pc = Pinecone(api_key=PINECONE_API_KEY)
    index = pc.Index(config["embedding"]["pinecone_index"])
    logger.debug("Querying Pinecone for top 50 candidate target papers...")
    search_res = index.query(vector=query_vector, top_k=50, include_metadata=False)
    
    if not search_res.matches:
        logger.warning(f"No Pinecone matches found for query '{query_text}'.")
        return {"target_node_idx": None, "nodes": [], "edges": []}
        
    candidate_ids = []
    for match in search_res.matches:
        try:
            candidate_ids.append(int(match.id))
        except ValueError:
            logger.debug(f"Skipping non-integer Pinecone match id: {match.id}")
            continue
 
    logger.debug(f"{len(candidate_ids)} candidate node ids to check against Neo4j.")
 
    target_node = None
 
    with driver.session() as session:
        # Find the first candidate match that exists in Neo4j
        best_candidate = None
        fallback_candidate = None
 
        for cid in candidate_ids:
            res = session.run(
                "MATCH (target:ResearchPaper {node_idx: $idx}) "
                "OPTIONAL MATCH (ancestor:ResearchPaper)-[:PREREQUISITE_OF]->(target) "
                "RETURN target.node_idx AS node_idx, target.title AS title, "
                "target.published_date AS published_date, target.abstract AS abstract, "
                "target.arxiv_id AS arxiv_id, count(ancestor) AS prereq_count",
                idx=cid
            ).single()
 
            if res and res["node_idx"] is not None:
                if res["prereq_count"] > 0:
                    best_candidate = res.data()
                    break
                elif fallback_candidate is None:
                    fallback_candidate = res.data()
 
        target_node = best_candidate or fallback_candidate
 
        if target_node:
            logger.debug(f"Matched target via Pinecone candidates: node_idx={target_node['node_idx']}.")
 
        if not target_node:
            logger.info(f"No Pinecone candidate matched in Neo4j; falling back to keyword search for '{query_text}'.")
            # Fallback: keyword search in Neo4j
            title_res = session.run(
                "MATCH (target:ResearchPaper) "
                "WHERE toLower(target.title) CONTAINS toLower($query) "
                "OPTIONAL MATCH (ancestor:ResearchPaper)-[:PREREQUISITE_OF]->(target) "
                "RETURN target.node_idx AS node_idx, target.title AS title, "
                "target.published_date AS published_date, target.abstract AS abstract, "
                "target.arxiv_id AS arxiv_id, count(ancestor) AS prereq_count "
                "ORDER BY prereq_count DESC LIMIT 1",
                query=query_text
            ).single()
            
            if title_res:
                target_node = title_res.data()
                logger.debug(f"Matched target via keyword search: node_idx={target_node['node_idx']}.")
            else:
                logger.warning(f"Keyword search found no match for '{query_text}'; falling back to most-connected paper.")
                any_res = session.run(
                    "MATCH (target:ResearchPaper) "
                    "OPTIONAL MATCH (ancestor:ResearchPaper)-[:PREREQUISITE_OF]->(target) "
                    "RETURN target.node_idx AS node_idx, target.title AS title, "
                    "target.published_date AS published_date, target.abstract AS abstract, "
                    "target.arxiv_id AS arxiv_id, count(ancestor) AS prereq_count "
                    "ORDER BY prereq_count DESC LIMIT 1"
                ).single()
                if any_res:
                    target_node = any_res.data()
 
        if not target_node:
            logger.warning(f"No target paper could be resolved for query '{query_text}'.")
            return {"target_node_idx": None, "nodes": [], "edges": []}
 
        target_node_idx = target_node["node_idx"]
        logger.info(f"Resolved target paper: node_idx={target_node_idx}, title='{target_node['title']}'.")
 
        # Trace prerequisite ancestors and paths
        ancestors_cypher = """
        MATCH (target:ResearchPaper {node_idx: $target_node_idx})
        MATCH p = (ancestor:ResearchPaper)-[rels:PREREQUISITE_OF*1..4]->(target)
        WITH ancestor, target, length(p) AS hop_distance, relationships(p) AS edges
        UNWIND edges AS edge
        WITH ancestor, target, hop_distance, sum(coalesce(edge.weight, 0.8)) AS total_path_weight
        ORDER BY total_path_weight DESC
        WITH hop_distance, collect({node: ancestor, weight: total_path_weight})[0..3] AS top_ancestors
        UNWIND top_ancestors AS top_a
        RETURN DISTINCT
            top_a.node.node_idx AS node_idx,
            top_a.node.title AS title,
            top_a.node.published_date AS published_date,
            top_a.node.abstract AS abstract,
            top_a.node.arxiv_id AS arxiv_id,
            hop_distance
        ORDER BY hop_distance DESC, published_date ASC
        """
 
        ancestor_records = [r.data() for r in session.run(ancestors_cypher, target_node_idx=target_node_idx)]
        logger.debug(f"Found {len(ancestor_records)} ancestor records within {max_hops} hops.")
 
        # Combine target node (hop_distance = 0) with ancestors
        all_nodes = [{
            "node_idx": target_node["node_idx"],
            "title": target_node["title"],
            "published_date": target_node["published_date"],
            "abstract": target_node["abstract"],
            "arxiv_id": target_node["arxiv_id"],
            "hop_distance": 0
        }]
        
        for a in ancestor_records:
            if a["node_idx"] != target_node_idx:
                all_nodes.append(a)
 
        # Fetch actual edges between these nodes in Neo4j
        node_indices = [n["node_idx"] for n in all_nodes]
        edges_cypher = """
        MATCH (src:ResearchPaper)-[r:PREREQUISITE_OF]->(dst:ResearchPaper)
        WHERE src.node_idx IN $node_indices AND dst.node_idx IN $node_indices
        RETURN DISTINCT
            src.node_idx AS src,
            dst.node_idx AS dst,
            coalesce(r.weight, 0.8) AS similarity,
            coalesce(r.reason, 'prerequisite') AS reason
        """
        edge_records = [r.data() for r in session.run(edges_cypher, node_indices=node_indices)]
        logger.info(f"Reading path resolved: {len(all_nodes)} nodes, {len(edge_records)} edges.")
 
        return {
            "target_node_idx": target_node_idx,
            "nodes": all_nodes,
            "edges": edge_records
        }