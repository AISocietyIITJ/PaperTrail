from neo4j import GraphDatabase
import pandas as pd
import os
from dotenv import load_dotenv

load_dotenv()
URI=os.getenv("URI")
NEO4J_USERNAME=os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD=os.getenv("NEO4J_PASSWORD")


airport_df=pd.read_csv('airport_fin.csv')
airline_df=pd.read_csv('airline_fin.csv')
routes_df=pd.read_csv('routes_fin.csv')

test_airport= airport_df.to_dict(orient="records")
test_airline= airline_df.to_dict(orient="records")
test_routes= routes_df.to_dict(orient="records")


data_ingest_query_airport= """
UNWIND $airport_batch AS item 
MERGE (ap:Airport{`Airport ID`: item.`Airport ID`}) 
SET 
ap.name = item.Name, 
ap.city = item.City, 
ap.country= item.Country, 
ap.iata = item.IATA, 
ap.icao = item.ICAO, 
ap.latitude = item.Latitude, 
ap.longitude = item.Longitude, 
ap.altitude = item.Altitude, 
ap.timezone = item.Timezone, 
ap.dst = item.DST, 
ap.tz=item.`Tz database timezone`, 
ap.type = item.Type, 
ap.source = item.Source
    """



data_ingest_query_airline= """UNWIND $airline_batch AS item 
MERGE (al:Airline {`Airline ID`: item.`Airline ID`}) 
ON CREATE SET 
al.name = item.Name, 
al.alias = item.Alias, 
al.country= item.Country, 
al.iata = item.IATA, 
al.icao = item.ICAO, 
al.callsign = item.Callsign,
al.active= item.Active"""


ap_ap_relation_with_routes= """
UNWIND $routes_batch AS item
MATCH(src:Airport {`Airport ID`: item.`Source Airport ID`})
MATCH(dst:Airport {`Airport ID`: item.`Destination Airport ID`})

MERGE (src)-[r1:CONNECTED_TO]->(dst)
ON CREATE SET
r1.codeshare = item.Codeshare,
r1.stops= toInteger(item.Stops),
r1.equipment= item.Equipment
r1.airline= item.Airline,
r1.airline_id=item.`Airline ID`
"""

al_ap_relation= """
UNWIND $routes_batch AS item
MATCH(al:Airline {`Airline ID`:item.`Airline ID`})
MATCH(ap:Airport {`Airport ID`: item.`Source Airport ID`})

MERGE (al)-[r2:OPERATE_AT]->(ap)
"""


with GraphDatabase.driver(URI, auth=(NEO4J_USERNAME,NEO4J_PASSWORD)) as driver:
    driver.verify_connectivity()

    with driver.session() as session:
        session.run("CREATE CONSTRAINT airport_id_uniq FOR (ap:Airport) REQUIRE ap.`Airport ID` IS UNIQUE")
        session.run("CREATE CONSTRAINT airline_id_uniq FOR (al:Airline) REQUIRE al.`Airline ID` IS UNIQUE")
        session.execute_write(lambda q: q.run(data_ingest_query_airport, airport_batch=test_airport,database="neo4j"))
        session.execute_write(lambda q: q.run(data_ingest_query_airline, airline_batch=test_airline,database="neo4j"))
        session.execute_write(lambda q: q.run(ap_ap_relation_with_routes, routes_batch=test_routes,database="neo4j"))
        session.execute_write(lambda q: q.run(al_ap_relation,routes_batch=test_routes,database="neo4j"))