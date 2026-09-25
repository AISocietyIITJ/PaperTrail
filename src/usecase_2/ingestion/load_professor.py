import re
import ast
import json
import unicodedata
import pandas as pd
from neo4j import GraphDatabase
import os
from src.config import AURA_URI, AURA_USER, AURA_PASSWORD

from src.logger import logger
 
 
script_dir = os.path.dirname(os.path.abspath(__file__))
proff_path = os.path.join(script_dir, "../../../data/professor_all_with_interests.csv")
alias_path = os.path.join(script_dir, "../../../data/interest_domains_with_aliases.csv")
 
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


def interest_key(text):
    """Create a stable lookup key for equivalent interest spellings."""
    text = clean_text(text)
    text = unicodedata.normalize("NFKC", text)
    text = re.sub(r"[\u2010-\u2015\u2212]", "-", text)
    text = text.casefold()
    return re.sub(r"[^a-z0-9]+", "", text)


def parse_interest_list(value):
    if pd.isna(value) or not value:
        return []
    value = str(value).strip()
    if value.startswith("[") and value.endswith("]"):
        try:
            return ast.literal_eval(value)
        except (ValueError, SyntaxError):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                pass
    return value.split(",")
 
 
def ingest_professors_and_edges(driver, prof_csv, interests_csv):
    logger.info(f"Loading professors from {prof_csv} and interests from {interests_csv}...")
    df_prof = pd.read_csv(prof_csv)
    df_int = pd.read_csv(interests_csv)
    interest_col = "Interest Domain" if "Interest Domain" in df_int.columns else "Interest"
    prof_interest_col = "Interest Domains"
    if prof_interest_col not in df_prof.columns:
        raise ValueError("professor CSV must include 'Interest Domains'; run infer_professor_interests.py first")

    logger.info(
        f"Loaded {len(df_prof)} professors and {len(df_int)} interest rows; "
        f"matching column '{interest_col}' from {os.path.abspath(interests_csv)}"
    )

    df_int["clean_interest"] = df_int[interest_col].apply(clean_text)
    df_int["interest_key"] = df_int[interest_col].apply(interest_key)
    df_int_unique = df_int.drop_duplicates(subset=["interest_key"]).copy()
    if "vector_id" not in df_int_unique.columns:
        df_int_unique["vector_id"] = [f"interest_{i}" for i in range(len(df_int_unique))]
    else:
        missing_vector_id = df_int_unique["vector_id"].isna() | (df_int_unique["vector_id"].astype(str).str.strip() == "")
        df_int_unique.loc[missing_vector_id, "vector_id"] = [
            f"interest_{i}" for i in df_int_unique.index[missing_vector_id]
        ]
 
    interest_to_vector = {}
    for _, row in df_int_unique.iterrows():
        vector_id = str(row["vector_id"])
        interest_to_vector[interest_key(row[interest_col])] = vector_id

        if "Aliases" in df_int_unique.columns and pd.notna(row["Aliases"]):
            for alias in str(row["Aliases"]).split(","):
                alias_key = interest_key(alias)
                if alias_key:
                    interest_to_vector.setdefault(alias_key, vector_id)
 
    prof_batch = []
    unmatched_tokens = set()
    matched_tokens = set()
    for _, row in df_prof.iterrows():
        interest_tokens = [
            clean_text(i) for i in parse_interest_list(row[prof_interest_col]) if clean_text(i)
        ]
        if not interest_tokens:
            continue
 
        matched_vector_ids = list(
            {
                interest_to_vector[interest_key(token)]
                for token in interest_tokens
                if interest_key(token) in interest_to_vector
            }
        )
 
        unmatched_tokens.update(
            token
            for token in interest_tokens
            if interest_key(token) not in interest_to_vector
        )
        matched_tokens.update(
            token
            for token in interest_tokens
            if interest_key(token) in interest_to_vector
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
    logger.info(
        f"Resolved {len(matched_tokens)} unique professor interests to "
        f"{len(set(interest_to_vector.values()))} vector IDs; "
        f"unmatched: {len(unmatched_tokens)}"
    )
 
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
