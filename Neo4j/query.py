from neo4j import GraphDatabase
from config import settings


# URI examples: "neo4j://localhost", "neo4j+s://xxx.databases.neo4j.io"
URI = "neo4j+s://ad728d35.databases.neo4j.io"
AUTH = ("ad728d35", settings.PASSWORD)

with GraphDatabase.driver(URI, auth=AUTH) as driver:
    driver.verify_connectivity()
    print("Connection established.")

    summary = driver.execute_query("""
        LOAD CSV WITH HEADERS FROM 'https://raw.githubusercontent.com/Rishabh-iitj2029/PaperTrail/refs/heads/tasks/Neo4j/airlines.csv' AS airlines
        MERGE (al:Airline {id: airlines.Airline_ID})
        ON CREATE SET
            al.name = airlines.Names,
            al.alias = airlines.Alias,
            al.iata = airlines.IATA,
            al.icao = airlines.ICAO,
            al.call_sign = airlines.Call_Sign,
            al.country = airlines.Country ,                      
            al.active = airlines.Active
        """,
    ).summary
    print("Created {nodes_created} Airport nodes in {time} ms.".format(
        nodes_created=summary.counters.nodes_created,
        time=summary.result_available_after
    ))

    summary = driver.execute_query("""
        LOAD CSV WITH HEADERS FROM 'https://raw.githubusercontent.com/Rishabh-iitj2029/PaperTrail/refs/heads/tasks/Neo4j/routes.csv' AS routes
        WITH routes LIMIT 10000
        MERGE (ap1:Airport {id: routes.Source_airport_ID})
        ON CREATE SET ap1.name = routes.Source_airport
        MERGE (ap2:Airport {id: routes.Destination_airport_ID})
        ON CREATE SET ap2.name = routes.Destination_airport                  
        MATCH (al:Airline {id: routes.Airline_ID})
        MERGE (r:Route {id: routes.Source_airport_ID + "-" + routes.Destination_airport_ID + "-" + routes.Airline_ID})
        ON CREATE SET
            r.codeshare = routes.Codeshare,
            r.stops = routes.Stops,
            r.equipment = routes.Equipment
        
        
        MERGE (ap1)-[:TAKING_OFF]->(r)
        MERGE (r)-[:LANDING]->(ap2)
        MERGE (r)-[:OPERATED_BY]->(al)                              
        """,
    ).summary
    print("Created {nodes_created} nodes and {rels_created} relationships for Routes in {time} ms.".format(
    nodes_created=summary.counters.nodes_created,
    rels_created=summary.counters.relationships_created,
    time=summary.result_available_after
))

    # Match Airport nodes where Airport_ID == routes.Source_airport_ID
    summary = driver.execute_query("""
        LOAD CSV WITH HEADERS FROM 'https://raw.githubusercontent.com/Rishabh-iitj2029/PaperTrail/refs/heads/tasks/Neo4j/airports.csv' AS airports
        MATCH (ap:Airport {id: airports.Airport_ID})
        SET ap.name      = airports.Name,
            ap.city      = airports.City,
            ap.country   = airports.Country,
            ap.iata      = airports.IATA,
            ap.icao      = airports.ICAO,
            ap.latitude  = toFloat(airports.Latitude),
            ap.longitude = toFloat(airports.Longitude),
            ap.altitude  = toInteger(airports.Altitude),
            ap.timezone  = airports.Tz_database_timezone,
            ap.type      = airports.Type
        """,
    ).summary
    print("Set properties on {props_set} Airport nodes in {time} ms.".format(
        props_set=summary.counters.properties_set,
        time=summary.result_available_after
    ))