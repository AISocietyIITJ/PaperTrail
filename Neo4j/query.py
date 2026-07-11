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
        MERGE (ap1:Airport {id: routes.Source_airport_ID, name: routes.Source_airport})
        MERGE (r:Route {codeshare: routes.Codeshare, Stops: routes.Stops, Equiment:routes.Equipment})
        MERGE (ap2:Airport {id: routes.Destination_airport_ID, name: routes.Destination_airport})
        MERGE (ap1-[:Taking_Off {Airline_id: routes.Airline_ID}]->r-[:Landing {Airline_id: routes.Airline_ID}]->ap2) 
        """,
    ).summary
    print("Created {nodes_created} Airport nodes in {time} ms.".format(
        nodes_created=summary.counters.nodes_created,
        time=summary.result_available_after
    ))

    # # Match Airport nodes where Airport_ID == routes.Source_airport_ID
    # summary = driver.execute_query("""
    #     LOAD CSV WITH HEADERS FROM 'https://raw.githubusercontent.com/Rishabh-iitj2029/PaperTrail/refs/heads/tasks/Neo4j/airports.csv' AS airports
    #     MATCH (ap:Airport {id: airports.Airport_ID})
    #     SET ap.name      = airports.Name,
    #         ap.city      = airports.City,
    #         ap.country   = airports.Country,
    #         ap.iata      = airports.IATA,
    #         ap.icao      = airports.ICAO,
    #         ap.latitude  = toFloat(airports.Latitude),
    #         ap.longitude = toFloat(airports.Longitude),
    #         ap.altitude  = toInteger(airports.Altitude),
    #         ap.timezone  = airports.Tz_database_timezone,
    #         ap.type      = airports.Type
    #     """,
    # ).summary
    # print("Set properties on {props_set} Airport nodes in {time} ms.".format(
    #     props_set=summary.counters.properties_set,
    #     time=summary.result_available_after
    # ))