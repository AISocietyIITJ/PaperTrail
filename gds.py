from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

load_dotenv()
URI = os.getenv("NEO4J_URI")
AUTH = (os.getenv("NEO4J_USERNAME"), os.getenv("NEO4J_PASSWORD"))


def PageRank(driver):
    query = """
    CALL gds.pageRank.stream('flightNetwork')
    YIELD nodeId, score
    WITH gds.util.asNode(nodeId) AS airport, score
    RETURN airport.iata AS IATA, airport.name AS AirportName, score
    ORDER BY score DESC
    LIMIT 5
    """
    records, _, _ = driver.execute_query(query)
    for record in records:
        print(record.data())


def Louvain(driver):
    query = """
    CALL gds.louvain.stream('flightNetwork')
    YIELD nodeId, communityId
    WITH gds.util.asNode(nodeId) AS airport, communityId
    RETURN communityId AS FlightRegion, count(*) AS TotalAirports
    ORDER BY TotalAirports DESC
    LIMIT 5
    """
    records, _, _ = driver.execute_query(query)
    for record in records:
        print(record.data())


def main():
    driver = GraphDatabase.driver(URI, auth=AUTH)

    try:
        driver.execute_query(
            "CALL gds.graph.project('flightNetwork', 'Airport', 'ROUTES_TO', {memory: '4GB'})"
        )
        PageRank(driver)
        Louvain(driver)

    finally:
        driver.execute_query(
            "CALL gds.graph.drop('flightNetwork', false) YIELD graphName"
        )
        driver.close()


if __name__ == "__main__":
    main()
