"""Fetch papers from Neo4j and embed+upsert to Pinecone via SPECTER2."""

import pandas as pd
from neo4j import GraphDatabase

import os
from dotenv import load_dotenv

load_dotenv()
from src.config import NEO4J_URI_2000,NEO4J_USERNAME_2000,NEO4J_PASSWORD_2000

# NEO4J_URI = os.getenv("NEO4J_URI") or AURA_URI
# NEO4J_USERNAME = os.getenv("NEO4J_USERNAME") or os.getenv("NEO4J_USER") or AURA_USER
# NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD") or AURA_PASSWORD

NEO4J_URI = str(NEO4J_URI_2000)
NEO4J_USERNAME = str(NEO4J_USERNAME_2000)
NEO4J_PASSWORD = str(NEO4J_PASSWORD_2000)
from src.usecase_1.embed import embed_corpus
from src.logger import logger

MODEL_NAME = "allenai/specter2_base"
INDEX_NAME = "papertrail-papers-2000"

QUERY = "MATCH (p:Paper) RETURN p.paperId AS paperId, p.title AS title, p.abstract AS abstract"


def fetch_papers() -> pd.DataFrame:
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))
    with driver.session() as session:
        result = session.run(QUERY)
        records = [dict(r) for r in result]
    driver.close()
    logger.info(f"Fetched {len(records)} papers from Neo4j.")
    return pd.DataFrame(records)


if __name__ == "__main__":
    df = fetch_papers()
    embed_corpus(df, model_name=MODEL_NAME, index_name=INDEX_NAME)      