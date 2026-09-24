import re
import pandas as pd
from neo4j import GraphDatabase
import os
from src.config import AURA_URI, AURA_USER, AURA_PASSWORD

from src.logger import logger
 
 
script_dir = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(script_dir, "../../../data/interests_with_aliases.csv")
 
 
 
BATCH_SIZE = 500
 
 
 
def setup_constraints(driver):
    queries = [
        "CREATE CONSTRAINT research_vector_id_unique IF NOT EXISTS FOR (r:ResearchTopic) REQUIRE r.vector_id IS UNIQUE;",
    ]
    with driver.session() as session:
        for q in queries:
            session.run(q)
    logger.info("[OK] Constraints set up")
 
def clean_text(text):
    if not isinstance(text, str):
        return ""
    text = text.replace("\xa0", " ").strip()
    return re.sub(r"[\.\…]+$", "", text).strip().lower()
 
 
def ingest_research_topics(driver, interests_csv):
    logger.info(f"Loading research topics from {interests_csv}...")
    df_int = pd.read_csv(interests_csv)
 
    df_int["clean_interest"] = df_int["Interest"].apply(clean_text)
 
    df_int_unique = df_int.drop_duplicates(subset=["clean_interest"]).copy()
    if len(df_int_unique) != len(df_int):
        logger.debug(f"Dropped {len(df_int) - len(df_int_unique)} duplicate-interest rows before ingestion.")
 
    topic_batch = []
    for _, row in df_int_unique.iterrows():
        raw_aliases = (
            str(row["Aliases"]) if pd.notna(row["Aliases"]) else ""
        )
        cleaned_aliases = ", ".join(
            [clean_text(a) for a in raw_aliases.split(",") if clean_text(a)]
        )
 
        topic_batch.append(
            {
                "vector_id": str(row["vector_id"]),
                "name": clean_text(row["Interest"]),
                "aliases": cleaned_aliases, 
            }
        )
 
 
    topic_query = """
    UNWIND $batch AS row
    MERGE (r:ResearchTopic {vector_id: row.vector_id})
    ON CREATE SET
        r.name = row.name,
        r.aliases = row.aliases
    ON MATCH SET
        r.name = row.name,
        r.aliases = row.aliases;
    """
 
    with driver.session() as session:
        for i in range(0, len(topic_batch), BATCH_SIZE):
            chunk = topic_batch[i : i + BATCH_SIZE]
            session.run(topic_query, batch=chunk)
            logger.debug(f"Ingested topic batch {i} to {min(i + BATCH_SIZE, len(topic_batch))}")
 
    logger.info(f"[OK] Ingested {len(topic_batch)} ResearchTopic nodes")
 
 
 
def ingest_research_node():
    driver = GraphDatabase.driver(
        AURA_URI, auth=(AURA_USER, AURA_PASSWORD)
    )
 
    try:
        logger.info("Connecting to Neo4j AuraDB")
        setup_constraints(driver)
        ingest_research_topics(
            driver, interests_csv=file_path
        )
    finally:
        driver.close()
 
# ingest_research_node()
