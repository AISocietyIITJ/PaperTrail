import os
from dotenv import load_dotenv
load_dotenv()
from neo4j import GraphDatabase
from src.config import AURA_URI, AURA_USER, AURA_PASSWORD

URI = os.getenv("NEO4J_URI") or AURA_URI
USER = os.getenv("NEO4J_USERNAME") or os.getenv("NEO4J_USER") or AURA_USER
PWD = os.getenv("NEO4J_PASSWORD") or AURA_PASSWORD

driver = GraphDatabase.driver(URI, auth=(USER, PWD))
with driver.session() as session:
    res = session.run("MATCH (p:Paper {paperId: 'e1c6aeffc3259fe02041906f41563f65c5509c6b'}) RETURN p").single()
    if res:
        props = dict(res["p"])
        print(f"Node properties:")
        for k, v in props.items():
            print(f"{k}: {v}")
    else:
        print("Node not found")
driver.close()
