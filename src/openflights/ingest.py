from pathlib import Path
import pandas as pd
from openflights.db import get_driver

PROCESSED_DIR = Path(__file__).resolve().parents[2] / "data" / "processed"


def create_constraints_and_indexes(session):
    session.run(
        "CREATE CONSTRAINT airport_id_unique IF NOT EXISTS "
        "FOR (a:Airport) REQUIRE a.airport_id IS UNIQUE"
    )
    session.run(
        "CREATE CONSTRAINT airline_id_unique IF NOT EXISTS "
        "FOR (a:Airline) REQUIRE a.airline_id IS UNIQUE"
    )
    session.run(
        "CREATE INDEX airport_country_idx IF NOT EXISTS "
        "FOR (a:Airport) ON (a.country)"
    )
    print("Constraints and indexes created.")


def ingest_airports(session):
    df = pd.read_csv(PROCESSED_DIR / "airports.csv")
    records = df.astype(object).where(pd.notnull(df), None).to_dict("records")
    session.run(
        """
        UNWIND $rows AS row
        MERGE (a:Airport {airport_id: row.airport_id})
        SET a.name = row.name,
            a.city = row.city,
            a.country = row.country,
            a.iata = row.iata,
            a.icao = row.icao,
            a.latitude = row.latitude,
            a.longitude = row.longitude,
            a.altitude = row.altitude,
            a.timezone = row.timezone
        """,
        rows=records,
    )
    print(f"Ingested {len(records)} Airport nodes.")


def ingest_airlines(session):
    df = pd.read_csv(PROCESSED_DIR / "airlines.csv")
    records = df.astype(object).where(pd.notnull(df), None).to_dict("records")
    session.run(
        """
        UNWIND $rows AS row
        MERGE (a:Airline {airline_id: row.airline_id})
        SET a.name = row.name,
            a.iata = row.iata,
            a.icao = row.icao,
            a.country = row.country,
            a.active = row.active
        """,
        rows=records,
    )
    print(f"Ingested {len(records)} Airline nodes.")


def ingest_routes(session):
    df = pd.read_csv(PROCESSED_DIR / "routes.csv")
    records = df.astype(object).where(pd.notnull(df), None).to_dict("records")

    result = session.run(
        """
        UNWIND $rows AS row
        MATCH (src:Airport {airport_id: row.source_airport_id})
        MATCH (dst:Airport {airport_id: row.destination_airport_id})
        MERGE (src)-[r:ROUTE {airline: row.airline}]->(dst)
        SET r.airline_id = row.airline_id,
            r.stops = row.stops,
            r.equipment = row.equipment,
            r.codeshare = row.codeshare
        RETURN count(r) AS created
        """,
        rows=records,
    )
    created = result.single()["created"]
    print(f"Ingested {created} ROUTE relationships (out of {len(records)} rows; "
          f"{len(records) - created} skipped due to missing airport endpoints).")


def main():
    driver = get_driver()
    with driver.session() as session:
        create_constraints_and_indexes(session)
        ingest_airports(session)
        ingest_airlines(session)
        ingest_routes(session)
    driver.close()
    print("Ingestion complete.")


if __name__ == "__main__":
    main()