from neo4j import GraphDatabase
from config import settings


URI = "neo4j+s://ad728d35.databases.neo4j.io"
AUTH = ("ad728d35", settings.PASSWORD)

def run_gds_pagerank():
    GRAPH_NAME = "airport-hub"

    with GraphDatabase.driver(URI, auth=AUTH) as driver:
        driver.verify_connectivity()
        print("Connection established.")

        projection_query = f"""
        MATCH (ap1:Airport)-[:TAKING_OFF]->(:Route)-[:LANDING]->(ap2:Airport)
        RETURN gds.graph.project(
        '{GRAPH_NAME}',
        ap1,
        ap2,
        {{}},
        {{ memory: '2GB' }}
        ) AS g
        """
        projection_summary = driver.execute_query(projection_query).records[0]
        print(f"Projected graph: {projection_summary}")

        mutate_query = f"""
            CALL gds.pageRank.mutate('{GRAPH_NAME}', {{ mutateProperty: 'pagerank' }})
            YIELD nodePropertiesWritten, ranIterations
            RETURN nodePropertiesWritten, ranIterations
        """
        result = driver.execute_query(mutate_query)

        print(result.records[0])

        result = driver.execute_query(f"""
            CALL gds.graph.nodeProperties.write('{GRAPH_NAME}', ['pagerank'])
            YIELD propertiesWritten
            RETURN propertiesWritten
        """)

        print(result.records[0])

        pagerank_query = """
            MATCH (a:Airport)
            WHERE a.pagerank IS NOT NULL
            RETURN a.name AS AirportName, a.id AS AirportID, a.pagerank AS score
            ORDER BY score DESC
            LIMIT 10
        """
        records, _, _ = driver.execute_query(pagerank_query)
        for record in records:
            print(record.data())

        cleanup_query = f"""
            CALL gds.graph.drop('{GRAPH_NAME}', false)
            YIELD graphName
        """
        driver.execute_query(cleanup_query)

def run_gds_louvain():
    GRAPH_NAME = "airport-hub-networks"

    with GraphDatabase.driver(URI, auth=AUTH) as driver:
        driver.verify_connectivity()
        print("Connection established.")

        projection_query = f"""
        MATCH (ap1:Airport)-[:TAKING_OFF]->(:Route)-[:LANDING]->(ap2:Airport)
        RETURN gds.graph.project(
            '{GRAPH_NAME}',
            ap1,
            ap2,
            {{}},
            {{ memory: '2GB' }}
        ) AS g
        """
        projection_summary = driver.execute_query(projection_query).records[0]
        print(f"Projected graph: {projection_summary}")

        # Run Louvain in mutate mode
        mutate_query = f"""
        CALL gds.louvain.mutate('{GRAPH_NAME}', {{ mutateProperty: 'louvain' }})
        YIELD communityCount, modularity, nodePropertiesWritten
        RETURN communityCount, modularity, nodePropertiesWritten
        """
        result = driver.execute_query(mutate_query)
        print(result.records[0])

        write_query = f"""
        CALL gds.graph.nodeProperties.write('{GRAPH_NAME}', ['louvain'])
        YIELD propertiesWritten
        RETURN propertiesWritten
        """
        result = driver.execute_query(write_query)
        print(result.records[0])

        louvain_query = """
        MATCH (a:Airport)
        WHERE a.louvain IS NOT NULL
        RETURN a.louvain AS community, count(a) AS airportCount,
               collect(a.name)[0..5] AS sampleAirports
        ORDER BY airportCount DESC
        LIMIT 10
        """
        records, _, _ = driver.execute_query(louvain_query)
        for record in records:
            print(record.data())

        cleanup_query = f"""
        CALL gds.graph.drop('{GRAPH_NAME}', false)
        YIELD graphName
        """
        driver.execute_query(cleanup_query)


run_gds_pagerank()
print("===========================================================================================================================")
print("===========================================================================================================================")
run_gds_louvain()
