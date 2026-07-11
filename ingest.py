import pandas as pd
from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

load_dotenv()
URI = os.getenv("NEO4J_URI")
AUTH = (os.getenv("NEO4J_USERNAME"), os.getenv("NEO4J_PASSWORD"))

airports = pd.read_csv("data/clean_airports.csv", keep_default_na=False)
airlines = pd.read_csv("data/clean_airlines.csv", keep_default_na=False)
routes = pd.read_csv("data/clean_routes.csv", keep_default_na=False)


def rules(driver):
    driver.execute_query(
        """CREATE CONSTRAINT airport_id_unique IF NOT EXISTS FOR (a:Airport) REQUIRE a.airport_id IS UNIQUE"""
    )
    driver.execute_query(
        """CREATE CONSTRAINT airline_id_unique IF NOT EXISTS FOR (al:Airline) REQUIRE al.airline_id IS UNIQUE"""
    )
    driver.execute_query(
        """CREATE INDEX airport_country_index IF NOT EXISTS FOR (a:Airport) ON (a.country)"""
    )


def ingest_airports(driver):
    batch_size = 2000
    total_rows = len(airports)
    query = """
    UNWIND $records AS row
    MERGE (a:Airport {airport_id: toInteger(row.airport_id)})
    SET a.name = row.name, a.city = row.city, a.country = row.country,
    a.iata = row.iata, a.latitude = toFloat(row.latitude), a.longitude = toFloat(row.longitude)
    """
    for i in range(0, total_rows, batch_size):
        batch = airports.iloc[i : i + batch_size]
        airports_records = batch.to_dict("records")

        driver.execute_query(query, records=airports_records)


def ingest_airlines(driver):
    batch_size = 2000
    total_rows = len(airlines)
    query = """
    UNWIND $records AS row
    MERGE (a:Airline {airline_id: toInteger(row.airline_id)})
    SET a.name = row.name, a.iata = row.iata, a.icao = row.icao, a.country = row.country, a.active = row.active
    """
    for i in range(0, total_rows, batch_size):
        batch = airlines.iloc[i : i + batch_size]
        airlines_records = batch.to_dict("records")

        driver.execute_query(query, records=airlines_records)


def ingest_routes(driver):
    batch_size = 2000
    total_rows = len(routes)
    query = """
    UNWIND $records AS row
    MATCH (source:Airport {airport_id: toInteger(row.source_airport_id)})
    MATCH (dest:Airport {airport_id: toInteger(row.destination_airport_id)})
    MERGE (source)-[r:ROUTES_TO {airline_id: toInteger(row.airline_id)}]->(dest)
    SET r.stops = toInteger(row.stops), r.equipment = row.equipment
    """
    for i in range(0, total_rows, batch_size):
        batch = routes.iloc[i : i + batch_size]
        routes_records = batch.to_dict("records")

        driver.execute_query(query, records=routes_records)


def main():
    driver = GraphDatabase.driver(URI, auth=AUTH)

    rules(driver)
    ingest_airports(driver)
    ingest_airlines(driver)
    ingest_routes(driver)

    driver.close()


if __name__ == "__main__":
    main()
