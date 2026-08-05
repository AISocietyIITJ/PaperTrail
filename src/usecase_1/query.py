import yaml
import pandas as pd
from neo4j import GraphDatabase
from sentence_transformers import SentenceTransformer

def load_neo4j_driver(config_path="config.yaml"):
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    neo_conf = config["neo4j"]
    driver = GraphDatabase.driver(neo_conf["uri"], auth=(neo_conf["user"], neo_conf["password"]))
    model_name = config["embedding"]["model_name"]
    model = SentenceTransformer(model_name)
    return config, driver, model

def generate_path_neo4j(query_text: str, driver, model, max_hops=4) -> pd.DataFrame:
    """Uses Pinecone Vector Search to find the target paper, then traverses backwards for prerequisites."""
    
    from pinecone import Pinecone
    from src.config import PINECONE_API_KEY
    import yaml

    with open("config.yaml", "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    # 1. Embed query
    query_vector = model.encode([query_text], normalize_embeddings=True)[0].tolist()

    # 2. Search Pinecone for the single closest target paper
    pc = Pinecone(api_key=PINECONE_API_KEY)
    index = pc.Index(config["embedding"]["pinecone_index"])
    search_res = index.query(vector=query_vector, top_k=1, include_metadata=True)
    
    if not search_res.matches:
        return pd.DataFrame()
        
    target_node_idx = int(search_res.matches[0].id)

    # 3. Use Neo4j to trace graph path backwards from the specific node_idx
    cypher_query = """
    MATCH (target:ResearchPaper {node_idx: $target_node_idx})
    
    MATCH p = (ancestor:ResearchPaper)-[rels:PREREQUISITE_OF*1..4]->(target)
    
    WITH ancestor, target, length(p) AS hop_distance, relationships(p) AS edges
    
    UNWIND edges AS edge
    WITH ancestor, target, hop_distance, sum(edge.weight) AS total_path_weight
    
    WITH hop_distance, ancestor, target, total_path_weight
    ORDER BY total_path_weight DESC
    
    WITH hop_distance, collect({node: ancestor, weight: total_path_weight})[0..3] AS top_ancestors
    
    UNWIND top_ancestors AS top_a
    RETURN 
        top_a.node.node_idx AS node_idx,
        top_a.node.title AS title,
        top_a.node.published_date AS published_date,
        hop_distance
    ORDER BY hop_distance DESC, published_date ASC
    """

    with driver.session() as session:
        result = session.run(cypher_query, target_node_idx=target_node_idx)
        records = [record.data() for record in result]

    if not records:
        return pd.DataFrame()

    return pd.DataFrame(records)