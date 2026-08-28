import re
import pandas as pd
from neo4j import GraphDatabase
import os
from src.config import AURA_URI, AURA_USER, AURA_PASSWORD

from src.logger import logger
 
 
script_dir = os.path.dirname(os.path.abspath(__file__))
proff_path = os.path.join(script_dir, "../../../data/professor_updated1.csv")
alias_path = os.path.join(script_dir, "../../../data/interests_with_aliases.csv")
 
BATCH_SIZE = 500
 
def setup_constraints(driver):
    queries = [
        "CREATE CONSTRAINT professor_url_unique IF NOT EXISTS FOR (p:Professor) REQUIRE p.profile_url IS UNIQUE;",
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
 
 
def ingest_professors_and_edges(driver, prof_csv, interests_csv):
    logger.info(f"Loading professors from {prof_csv} and interests from {interests_csv}...")
    df_prof = pd.read_csv(prof_csv)
    df_int = pd.read_csv(interests_csv)
 
    df_int["clean_interest"] = df_int["Interest"].apply(clean_text)
    df_int_unique = df_int.drop_duplicates(subset=["clean_interest"]).copy()
 
    interest_to_vector = dict(
        zip(df_int_unique["clean_interest"], df_int_unique["vector_id"])
    )
 
    interest_to_vector_id = {
        clean_text(row["Interest"]): str(row["vector_id"])
        for _, row in df_int.iterrows()
    }
 
    prof_batch = []
    unmatched_tokens = set()
    for _, row in df_prof.iterrows():
        raw_interests = (
            str(row["Interests"]) if pd.notna(row["Interests"]) else ""
        )
        interest_tokens = [
            clean_text(i) for i in raw_interests.split(",") if clean_text(i)
        ]
 
        matched_vector_ids = list(
            {
                interest_to_vector[token]
                for token in interest_tokens
                if token in interest_to_vector
            }
        )
 
        unmatched_tokens.update(
            token for token in interest_tokens if token not in interest_to_vector
        )
 
        prof_batch.append(
            {
                "name": clean_text(row["Name"]), 
                "affiliation": clean_text(
                    row["Affiliation"]
                ), 
                "profile_url": str(
                    row["Profile URL"]
                ),
                "cited_by": (
                    int(row["Cited By"]) if pd.notna(row["Cited By"]) else 0
                ),
                "h_index": (
                    int(row["h-index"]) if pd.notna(row["h-index"]) else 0
                ),
                "i10_index": (
                    int(row["i10-index"]) if pd.notna(row["i10-index"]) else 0
                ),
                "interest_vector_ids": matched_vector_ids,
            }
        )
 
    if unmatched_tokens:
        logger.warning(f"{len(unmatched_tokens)} interest tokens had no matching vector_id and were skipped, "
                        f"e.g. {list(unmatched_tokens)[:10]}")
 
    prof_query = """
    UNWIND $batch AS row
    MERGE (p:Professor {profile_url: row.profile_url})
    ON CREATE SET
        p.name = row.name,
        p.affiliation = row.affiliation,
        p.cited_by = row.cited_by,
        p.h_index = row.h_index,
        p.i10_index = row.i10_index
    ON MATCH SET
        p.name = row.name,
        p.affiliation = row.affiliation,
        p.cited_by = row.cited_by,
        p.h_index = row.h_index,
        p.i10_index = row.i10_index
 
    WITH p, row
    UNWIND row.interest_vector_ids AS target_vector_id
    MATCH (r:ResearchTopic {vector_id: target_vector_id})
    MERGE (p)-[:WORKS_IN]->(r);
    """
 
    with driver.session() as session:
        for i in range(0, len(prof_batch), BATCH_SIZE):
            chunk = prof_batch[i : i + BATCH_SIZE]
            session.run(prof_query, batch=chunk)
            logger.debug(f"Ingested professor batch {i} to {min(i + BATCH_SIZE, len(prof_batch))}")
 
    logger.info(f"[OK] Ingested {len(prof_batch)} Professor nodes and created edges")
 
 
def ingest_proff_connect_edges():
    driver = GraphDatabase.driver(
        AURA_URI, auth=(AURA_USER, AURA_PASSWORD)
    )
 
    try:
        logger.info("Connecting to Neo4j AuraDB")
        setup_constraints(driver)
        ingest_professors_and_edges(
            driver,
            prof_csv=proff_path,
            interests_csv=alias_path,
        )
 
        logger.info("[OK] Graph ingestion complete")
 
    finally:
        driver.close()
 
# ingest_proff_connect_edges()
