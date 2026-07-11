from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

load_dotenv()
URI = os.getenv("NEO4J_URI")
AUTH = (os.getenv("NEO4J_USERNAME"), os.getenv("NEO4J_PASSWORD"))


def run_query(driver, query, query_name, **kwargs):
    records, _, _ = driver.execute_query(query, **kwargs)
    print(f"Result for query {query_name}: ")
    for record in records:
        print(record.data())


def run_aggregation_country(driver):
    query = """
    MATCH (a:Airport)
    RETURN a.country AS Country, count(a) AS TotalAirports
    ORDER BY TotalAirports DESC 
    LIMIT 5
    """
    run_query(driver, query, "run_aggregation_country")


def run_aggregation_airlines(driver):
    query = """
    MATCH (:Airport)-[r:ROUTES_TO]->(:Airport)
    MATCH (al:Airline {airline_id: toInteger(r.airline_id)})
    RETURN al.name AS AirlineName, count(r) AS TotalRoutesUsed
    ORDER BY TotalRoutesUsed DESC
    LIMIT 5
    """
    run_query(driver, query, "run_aggregation_airlines")


def run_shortest_path(driver):
    query = """
    MATCH path = shortestPath((start:Airport {city: 'Sydney'})-[:ROUTES_TO*..5]->(end:Airport {city: 'London'}))
    RETURN length(path) AS Number_of_Flights_Needed
    """
    run_query(driver, query, "run_shortest_path")


def run_lookup(driver):
    query = """
    MATCH (a:Airport {iata: $iata_code})
    RETURN a.airport_id AS ID, 
       a.name AS AirportName, 
       a.city AS City, 
       a.country AS Country, 
       a.latitude AS Lat, 
       a.longitude AS Lon
       """
    run_query(driver, query, "run_lookup", iata_code="JFK")


def run_path(driver):
    query = """
    MATCH (start:Airport {city: $origin_city})-[:ROUTES_TO]->(layover:Airport)-[:ROUTES_TO]->(end:Airport {city: $destination_city})
    WHERE start <> end
    RETURN layover.name AS LayoverAirport, layover.city AS LayoverCity
    LIMIT 5
    """
    run_query(
        driver, query, "run_path", origin_city="Ahmedabad", destination_city="Osaka"
    )


def main():
    driver = GraphDatabase.driver(URI, auth=AUTH)

    run_path(driver)
    run_lookup(driver)
    run_aggregation_airlines(driver)
    run_aggregation_country(driver)
    run_shortest_path(driver)

    driver.close()


if __name__ == "__main__":
    main()
