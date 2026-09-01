from neo4j import GraphDatabase
from src.config import AURA_URI, AURA_USER, AURA_PASSWORD

from src.logger import logger 

driver = GraphDatabase.driver(AURA_URI, auth=(AURA_USER, AURA_PASSWORD))

verification_query1 = """
MATCH (p:Professor) WITH count(p) AS total_profs
MATCH (r:ResearchTopic) WITH total_profs, count(r) AS total_topics
MATCH ()-[rel:WORKS_IN]->()
RETURN total_profs, total_topics, count(rel) AS total_edges;
"""
verification_query2 = """
MATCH (r:ResearchTopic)
WHERE NOT (r)<-[:WORKS_IN]-(:Professor)
RETURN count(r) AS UnconnectedTopics;
"""


with driver.session() as session:
    result1 = session.run(verification_query1).single()
    logger.info("--- Neo4j Ingestion Summary ---")
    logger.info(f"Total Professors: {result1['total_profs']}")
    logger.info(f"Total Research Topics: {result1['total_topics']}")
    logger.info(f"Total [:WORKS_IN] Edges: {result1['total_edges']}")
    result2 = session.run(verification_query2).single()
    logger.info(f"Number of unconnected nodes {result2['UnconnectedTopics']}")

driver.close()