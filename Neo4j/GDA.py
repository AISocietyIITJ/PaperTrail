from neo4j import GraphDatabase
from config import settings


URI = "neo4j+s://ad728d35.databases.neo4j.io"
AUTH = ("ad728d35", settings.PASSWORD)

with GraphDatabase.driver(URI, auth=AUTH) as driver:
    driver.verify_connectivity()
    print("Connection established.")

    records, summary, keys = driver.execute_query("""
        MATCH (ap1:Airport)-[:TAKING_OFF]->(r:Route)-[:OPERATED_BY]->(al:Airline)
        WHERE al.country = "United States"
        RETURN ap1
        LIMIT 5
        """,
        database_="ad728d35",
    )

    for record in records:
        print(record)

    # 1. finding which airport is biggesst transit hub
    records, summary, keys = driver.execute_query("""
        MATCH (ap:Airport)
        OPTIONAL MATCH (ap)-[:TAKING_OFF]->(r1:Route)
        OPTIONAL MATCH (r2:Route)-[:LANDING]->(ap)
        RETURN ap.name AS Airport_Name,
               ap.id AS Airport_ID,
               count(DISTINCT r1) AS OutTraffic,
               count(DISTINCT r2) AS InTraffic,
               count(DISTINCT r1) + count(DISTINCT r2) AS Total_Traffic
        ORDER BY Total_Traffic DESC
        LIMIT 10
        """,
        database_="ad728d35",
    )

    for record in records:
        print(record.data())
    
    # 2. Maximum routes operating airlines
    records, summary, keys = driver.execute_query("""
        MATCH (al:Airline)<-[:OPERATED_BY]-(r:Route)
        RETURN al.id AS Airline_ID,
               al.name AS Airline_name,
               al.alias AS alias,
               count(r) AS Total_Routes_operated
        ORDER BY Total_Routes_operated DESC
        LIMIT 10
        """,
        database_="ad728d35",
    )

    for record in records:
        print(record.data())
    


    