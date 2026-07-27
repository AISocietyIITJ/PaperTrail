from neo4j import GraphDatabase

URI = "bolt://localhost:7687"
USERNAME = "neo4j"
PASSWORD = "Krishna1234*"

driver = GraphDatabase.driver(URI, auth=(USERNAME, PASSWORD))


def run_query(query):
    with driver.session() as session:
        result = session.run(query)
        return [record.data() for record in result]


query = """
MATCH (a:Airport)
RETURN a.name AS Airport, a.city AS City
LIMIT 10
"""

results = run_query(query)

print("First 10 Airports:\n")

for row in results:
    print(row)

driver.close()