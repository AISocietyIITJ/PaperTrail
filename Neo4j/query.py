from neo4j import GraphDatabase
from config import settings


# URI examples: "neo4j://localhost", "neo4j+s://xxx.databases.neo4j.io"
URI = "neo4j+s://ad728d35.databases.neo4j.io"
AUTH = ("ad728d35", settings.PASSWORD)

with GraphDatabase.driver(URI, auth=AUTH) as driver:
    driver.verify_connectivity()
    print("Connection established.")

    summary = driver.execute_query("""
        LOAD CSV WITH HEADERS FROM 'https://raw.githubusercontent.com/Rishabh-iitj2029/PaperTrail/refs/heads/tasks/Neo4j/routes.csv' AS routes
        WITH routes LIMIT 5
        MERGE(r:Route {stops: routes.Stops})
        MERGE(ap1:Airport {id: routes.Source_airport_ID}) 
        
        
        """,
    ).summary
    print("Created {nodes_created} nodes in {time} ms.".format(
        nodes_created=summary.counters.nodes_created,
        time=summary.result_available_after
    ))

    