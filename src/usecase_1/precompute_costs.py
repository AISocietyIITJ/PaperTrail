"""Precompute NEWST node, edge, and traversal costs in Neo4j."""

from __future__ import annotations

import argparse
import math
import os
import re
from collections.abc import Iterable

import networkx as nx
import yaml
from neo4j import GraphDatabase
from pinecone import Pinecone

from src.config import AURA_URI, AURA_USER, AURA_PASSWORD, PINECONE_API_KEY
from src.logger import logger

# ---------------------------------------------------------------------------
# Resolve Neo4j connection (prefer NEO4J_* env vars, same as query_pipeline)
# ---------------------------------------------------------------------------
NEO4J_URI = os.getenv("NEO4J_URI") or AURA_URI
NEO4J_USERNAME = (
    os.getenv("NEO4J_USERNAME") or os.getenv("NEO4J_USER") or AURA_USER
)
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD") or AURA_PASSWORD

IDENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


# ── Utility Helpers ──────────────────────────────────────────────────────────


def ident(value: str) -> str:
    """Validate a Neo4j identifier to prevent Cypher injection."""
    if not IDENT.fullmatch(value):
        raise ValueError(f"Unsafe Neo4j identifier: {value!r}")
    return value


def batched(items: list, size: int) -> Iterable[list]:
    """Yield successive chunks of *size* from *items*."""
    for i in range(0, len(items), size):
        yield items[i : i + size]


def load_config(path: str) -> dict:
    """Load YAML configuration file."""
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}

def cosine(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two vectors."""
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb) if na and nb else 0.0

# ── Stage 1: PageRank (NetworkX — no GDS plugin required) ────────────────────


def write_pagerank(
    driver, node_label: str, rel_type: str, batch_size: int = 500
) -> int:
    """Compute PageRank via NetworkX and write scores back to Neo4j.

    This avoids the Neo4j GDS plugin requirement by pulling the graph
    into memory, running networkx.pagerank(), and batch-writing results.
    For ~7K nodes this completes in seconds.
    """
    # 1. Pull all edges from Neo4j into a NetworkX DiGraph
    query = f"""
    MATCH (src:{node_label})-[:{rel_type}]->(dst:{node_label})
    RETURN elementId(src) AS src_eid, elementId(dst) AS dst_eid
    """
    G = nx.DiGraph()
    with driver.session() as session:
        for record in session.run(query):
            G.add_edge(record["src_eid"], record["dst_eid"])

        # Also add isolated nodes (no edges) so they get a pagerank score
        iso_query = f"""
        MATCH (p:{node_label})
        WHERE NOT (p)-[:{rel_type}]-() AND NOT (p)<-[:{rel_type}]-()
        RETURN elementId(p) AS eid
        """
        for record in session.run(iso_query):
            G.add_node(record["eid"])

    if G.number_of_nodes() == 0:
        logger.warning("No nodes found for PageRank computation.")
        return 0

    logger.info(
        "Running NetworkX PageRank on {} nodes, {} edges...",
        G.number_of_nodes(),
        G.number_of_edges(),
    )

    # 2. Compute PageRank (same params as GDS: 20 iterations, damping 0.85)
    scores = nx.pagerank(G, alpha=0.85, max_iter=20, tol=1e-06)

    # 3. Write scores back to Neo4j in batches
    updates = [{"eid": eid, "pagerank": score} for eid, score in scores.items()]
    with driver.session() as session:
        for batch in batched(updates, batch_size):
            session.run(
                """
                UNWIND $batch AS row
                MATCH (p)
                WHERE elementId(p) = row.eid
                SET p.pagerank = row.pagerank
                """,
                batch=batch,
            ).consume()

    return len(updates)


# ── Stage 2: Node Costs ──────────────────────────────────────────────────────


def write_node_costs(driver, node_label: str) -> None:
    """Compute S_node and nodeCost for every node."""
    query = f"""
    MATCH (p:{node_label})
    WITH min(coalesce(p.pagerank, 0.0)) AS minPr,
         max(coalesce(p.pagerank, 0.0)) AS maxPr
    MATCH (p:{node_label})
    WITH p,
         CASE
           WHEN maxPr = minPr THEN 0.0
           ELSE (coalesce(p.pagerank, 0.0) - minPr) / (maxPr - minPr)
         END AS prGlobal
    WITH p, prGlobal,
         (0.4 * prGlobal)
         + (0.2 * log(coalesce(p.citationCount, 0) + 1))
         + (0.4 * log(coalesce(p.influentialCitationCount, 0) + 1)) AS sNode
    SET p.pagerank_normalized = prGlobal,
        p.s_node = sNode,
        p.nodeCost = 5.0 / (CASE WHEN sNode = 0 THEN 0.00001 ELSE sNode END)
    """
    with driver.session() as session:
        session.run(query).consume()


# ── Stage 3: Cosine Similarity Injection (Pinecone) ──────────────────────────

def build_pinecone_mapping(index) -> dict[str, str]:
    """Builds a mapping of paperId -> Pinecone vector ID by querying Pinecone."""
    logger.info("Building Pinecone paperId mapping (this takes ~30s)...")
    stats = index.describe_index_stats()
    total = stats.total_vector_count
    mapping = {}
    
    # Fetch in batches of 1000
    for i in range(0, total, 1000):
        ids = [str(x) for x in range(i, min(i + 1000, total))]
        res = index.fetch(ids=ids)
        for v_id, vec in res.vectors.items():
            if vec.metadata and "paperId" in vec.metadata:
                mapping[vec.metadata["paperId"]] = v_id
    
    logger.info(f"Mapped {len(mapping)} paperIds to Pinecone IDs.")
    return mapping

def fetch_edges(
    driver, node_label: str, rel_type: str, id_property: str, only_missing: bool
) -> list[dict]:
    where = "WHERE r.cos_similarity IS NULL" if only_missing else ""
    query = f"""
    MATCH (src:{node_label})-[r:{rel_type}]->(dst:{node_label})
    {where}
    RETURN elementId(r) AS rel_id,
           src.{id_property} AS src_id,
           dst.{id_property} AS dst_id
    """
    with driver.session() as session:
        return [record.data() for record in session.run(query)]

def fetch_vectors(
    index, ids: list[str], batch_size: int
) -> dict[str, list[float]]:
    vectors: dict[str, list[float]] = {}
    for batch in batched(ids, batch_size):
        response = index.fetch(ids=batch)
        for vector_id, vector in response.vectors.items():
            vectors[vector_id] = vector.values
    return vectors

def inject_cosine_similarities(
    driver,
    index,
    node_label: str,
    rel_type: str,
    id_property: str,
    batch_size: int,
    only_missing: bool,
) -> int:
    edges = fetch_edges(driver, node_label, rel_type, id_property, only_missing)
    if not edges:
        logger.info("No edges to process for cosine similarity.")
        return 0

    mapping = build_pinecone_mapping(index)

    # Collect all needed pinecone IDs
    pinecone_ids = set()
    for edge in edges:
        s_id = str(edge["src_id"])
        d_id = str(edge["dst_id"])
        if s_id in mapping:
            pinecone_ids.add(mapping[s_id])
        if d_id in mapping:
            pinecone_ids.add(mapping[d_id])

    logger.info(f"Fetching {len(pinecone_ids)} vectors from Pinecone...")
    vectors = fetch_vectors(index, list(pinecone_ids), batch_size=1000)

    updates = []
    for edge in edges:
        s_id = str(edge["src_id"])
        d_id = str(edge["dst_id"])
        
        if s_id not in mapping or d_id not in mapping:
            continue
            
        pc_src = mapping[s_id]
        pc_dst = mapping[d_id]
        
        if pc_src not in vectors or pc_dst not in vectors:
            continue
            
        updates.append(
            {
                "rel_id": edge["rel_id"],
                "cos_similarity": cosine(vectors[pc_src], vectors[pc_dst]),
            }
        )

    if not updates:
        return 0

    with driver.session() as session:
        for batch in batched(updates, batch_size):
            session.run(
                """
                UNWIND $batch AS row
                MATCH ()-[r]->()
                WHERE elementId(r) = row.rel_id
                SET r.cos_similarity = row.cos_similarity
                """,
                batch=batch,
            )
    return len(updates)

# ── Stage 4: Edge Costs ──────────────────────────────────────────────────────


def write_edge_costs(driver, node_label: str, rel_type: str) -> None:
    """Compute W_intent, M_inf, and final edgeCost for every edge."""
    query = f"""
    MATCH (:{node_label})-[r:{rel_type}]->(:{node_label})
    WITH r,
         [intent IN coalesce(r.intents, []) | toLower(toString(intent))] AS intents
    WITH r,
         CASE
           WHEN 'methodology' IN intents THEN 3.0
           WHEN 'result' IN intents THEN 2.0
           ELSE 1.0
         END AS wIntent,
         CASE WHEN coalesce(r.isInfluential, false) THEN 2.0 ELSE 1.0 END AS mInf
    WITH r, wIntent, mInf,
         coalesce(r.cos_similarity, 0.5) * wIntent * mInf AS score
    SET r.W_intent = wIntent,
        r.M_inf = mInf,
        r.score = score,
        r.edgeCost = 3.0 / ((CASE WHEN score = 0 THEN 0.00001 ELSE score END) ^ 2.0)
    """
    with driver.session() as session:
        session.run(query).consume()


# ── Stage 5: Traversal Costs ─────────────────────────────────────────────────


def write_traversal_costs(driver, node_label: str, rel_type: str) -> None:
    """Set traversalCost = edgeCost + target nodeCost on every relationship."""
    query = f"""
    MATCH (:{node_label})-[r:{rel_type}]->(targetNode:{node_label})
    SET r.traversalCost = coalesce(r.edgeCost, 0.0) + coalesce(targetNode.nodeCost, 0.0)
    """
    with driver.session() as session:
        session.run(query).consume()


# ── Programmatic Entry Point ─────────────────────────────────────────────────


def run_precompute(
    config_path: str = "config.yaml",
    node_label: str = "Paper",
    rel_type: str = "CITES",
    id_property: str = "paperId",
    pinecone_index: str | None = None,
    batch_size: int = 500,
    all_relationships: bool = False,
    skip_pagerank: bool = False,
    skip_cosine: bool = False,
) -> None:
    """Run the full NEWST cost precomputation pipeline."""
    config = load_config(config_path)
    node_label = ident(node_label)
    rel_type = ident(rel_type)
    id_property = ident(id_property)
    index_name = pinecone_index or config.get("embedding", {}).get(
        "pinecone_index", "papertrail-papers"
    )

    logger.info(
        "Connecting to Neo4j at {} (label={}, rel={})...",
        NEO4J_URI,
        node_label,
        rel_type,
    )
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))
    try:
        # ── Stage 1: PageRank (via NetworkX) ──────────────────────────────
        if not skip_pagerank:
            logger.info("Stage 1/5: Computing PageRank via NetworkX...")
            pr_count = write_pagerank(
                driver, node_label, rel_type, batch_size=batch_size
            )
            logger.info("PageRank written to {} nodes.", pr_count)
        else:
            logger.info("Stage 1/5: Skipping PageRank (--skip-pagerank).")

        # ── Stage 2: Node Costs ───────────────────────────────────────────
        logger.info("Stage 2/5: Writing nodeCost...")
        write_node_costs(driver, node_label)
        logger.info("nodeCost written successfully.")

        # ── Stage 3: Cosine Similarities ──────────────────────────────────
        if not skip_cosine:
            logger.info(
                f"Stage 3/5: Injecting cosine similarities from Pinecone index '{index_name}'..."
            )
            pc = Pinecone(api_key=PINECONE_API_KEY)
            written = inject_cosine_similarities(
                driver=driver,
                index=pc.Index(index_name),
                node_label=node_label,
                rel_type=rel_type,
                id_property=id_property,
                batch_size=batch_size,
                only_missing=not all_relationships,
            )
            logger.info("Updated {} edges with cos_similarity.", written)
        else:
            logger.info("Stage 3/5: Skipping Cosine Similarities.")

        # ── Stage 4: Edge Costs ───────────────────────────────────────────
        logger.info("Stage 4/5: Writing edgeCost...")
        write_edge_costs(driver, node_label, rel_type)
        logger.info("edgeCost written successfully.")

        # ── Stage 5: Traversal Costs ──────────────────────────────────────
        logger.info("Stage 5/5: Writing traversalCost...")
        write_traversal_costs(driver, node_label, rel_type)
        logger.info("traversalCost written successfully.")

        logger.info("=== NEWST cost precomputation complete ===")
    finally:
        driver.close()


# ── CLI ───────────────────────────────────────────────────────────────────────


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Precompute static NEWST costs in Neo4j."
    )
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--node-label", default="Paper")
    parser.add_argument("--relationship-type", default="CITES")
    parser.add_argument("--id-property", default="paperId")
    parser.add_argument("--pinecone-index")
    parser.add_argument("--batch-size", type=int, default=500)
    parser.add_argument(
        "--all-relationships",
        action="store_true",
        help="Recompute cosine similarity even when already present.",
    )
    parser.add_argument("--skip-pagerank", action="store_true")
    parser.add_argument("--skip-cosine", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    run_precompute(
        config_path=args.config,
        node_label=args.node_label,
        rel_type=args.relationship_type,
        id_property=args.id_property,
        pinecone_index=args.pinecone_index,
        batch_size=args.batch_size,
        all_relationships=args.all_relationships,
        skip_pagerank=args.skip_pagerank,
        skip_cosine=args.skip_cosine,
    )


if __name__ == "__main__":
    main()
