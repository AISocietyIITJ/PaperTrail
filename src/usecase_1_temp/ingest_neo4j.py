"""Neo4j Graph and Vector Index Ingestion."""
 
import numpy as np
import pandas as pd
import yaml
from neo4j import GraphDatabase
from src.config import AURA_URI, AURA_USER, AURA_PASSWORD

from src.logger import logger
 
def load_config(config_path="config.yaml"):
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)
 
def ingest_to_neo4j(config_path="config.yaml"):
    config = load_config(config_path)
    neo_conf = config.get("neo4j", {})
    uri = AURA_URI or neo_conf.get("uri")
    user = AURA_USER or neo_conf.get("user")
    password = AURA_PASSWORD or neo_conf.get("password")
    
    # Load Local Processed Artifacts
    interim_path = config["paths"]["interim_data"]
    directed_path = config["paths"]["directed_edges"]
 
    logger.info("Loading Parquet data...")
    df_papers = pd.read_parquet(interim_path)
    df_edges = pd.read_parquet(directed_path)
 
    logger.info(f"Connecting to Neo4j AuraDB ({uri})...")
    driver = GraphDatabase.driver(uri, auth=(user, password))
 
    with driver.session() as session:
        logger.info("Setting up Neo4j constraints and Vector Index...")
        session.run("CREATE CONSTRAINT unique_paper_idx IF NOT EXISTS FOR (p:ResearchPaper) REQUIRE p.node_idx IS UNIQUE;")
        
 
        
        # Create Standard Index on published_date for fast chronological sorting
        session.run("CREATE INDEX paper_published_date IF NOT EXISTS FOR (p:ResearchPaper) ON (p.published_date);")
 
        logger.info(f"Ingesting {len(df_papers)} ResearchPaper nodes...")
        batch_size = 1000
        for i in range(0, len(df_papers), batch_size):
            batch_df = df_papers.iloc[i:i+batch_size]
 
            payload = []
            for _, row in batch_df.iterrows():
                payload.append({
                    "node_idx": int(row["node_idx"]),
                    "title": str(row["title"]),
                    "published_date": str(row["published_date"]).split("T")[0],
                    "arxiv_id": str(row.get("arxiv_base_id", "")),
                    "abstract": str(row.get("abstract", ""))
                })
 
            session.run("""
            UNWIND $batch AS row
            MERGE (p:ResearchPaper {node_idx: row.node_idx})
            SET p.title = row.title,
                p.published_date = row.published_date,
                p.arxiv_id = row.arxiv_id,
                p.abstract = row.abstract
            """, batch=payload)
            logger.debug(f"Pushed nodes {i} to {min(i+batch_size, len(df_papers))}")
 
        logger.info(f"Ingesting {len(df_edges)} PREREQUISITE_OF edges...")
        for i in range(0, len(df_edges), batch_size):
            batch_edges = df_edges.iloc[i:i+batch_size].to_dict(orient="records")
            session.run("""
            UNWIND $batch AS row
            MATCH (src:ResearchPaper {node_idx: row.src})
            MATCH (dst:ResearchPaper {node_idx: row.dst})
            MERGE (src)-[r:PREREQUISITE_OF]->(dst)
            SET r.weight = toFloat(row.similarity),
                r.reason = row.reason
            """, batch=batch_edges)
            logger.debug(f"Pushed edges {i} to {min(i+batch_size, len(df_edges))}")
 
    driver.close()
    logger.info("Successfully ingested all nodes and edges into Neo4j!")
 
if __name__ == "__main__":
    ingest_to_neo4j()
