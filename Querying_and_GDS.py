from neo4j import GraphDatabase
from neo4j.exceptions import ClientError
URI="neo4j://127.0.0.1:7687"
NEO4J_USERNAME="neo4j"
NEO4J_PASSWORD="Task2@iitj"

query1 = """
MATCH (ap:Airport)-[r:CONNECTED_TO]->(:Airport)
WHERE r.airline IS NOT NULL
WITH ap, r.airline as airlineCode
MATCH (al:Airline)
WHERE al.IATA = airlineCode
RETURN ap.name AS Name,
       ap.`Airport ID` as `Airport ID`,
       count(DISTINCT al.name) as Operating_Airlines
ORDER BY Operating_Airlines DESC
LIMIT 10
"""

query2 = """
MATCH (ap:Airport) -[r:CONNECTED_TO]->(:Airport)
WHERE toInteger(r.stops)>=1
RETURN count(r) as Total_Stops,
       count(DISTINCT ap) as Airports_with_multi_stops
"""

query3 = """
MATCH (al:Airline) -[r:OPERATE_AT]->(ap:Airport)
RETURN al.name as Airline_Name,
       count(DISTINCT ap) as Airports_operating_airline
ORDER BY Airports_operating_airline DESC
LIMIT 10
"""

Projection_query = """
CALL gds.graph.project.cypher(
  'My_Graph',
  'MATCH (a:Airport) RETURN id(a) AS id, ["Airport"] AS labels',
  'MATCH (s:Airport)-[:CONNECTED_TO]->(t:Airport) RETURN id(s) AS source, id(t) AS target'
)
YIELD graphName, nodeCount, relationshipCount
"""


Pagerank_query = """
CALL gds.pageRank.stream('My_Graph')
YIELD nodeId, score
RETURN gds.util.asNode(nodeId).name AS Airport_Name, score AS Score
ORDER BY Score DESC
LIMIT 10
"""

WCC_query = """
CALL gds.wcc.stream('My_Graph')
YIELD nodeId, componentId
MATCH (a) WHERE id(a) = nodeId
RETURN a.name AS Airport_Name, componentId AS ComponentID
ORDER BY ComponentID
LIMIT 10
"""


drop_query = """
CALL gds.graph.drop('My_Graph', false) YIELD graphName
"""

WCC_query = """
CALL gds.wcc.stream('My_Graph')
YIELD nodeId, componentId
RETURN gds.util.asNode(nodeId).name AS Airport_Name,
       componentId AS ComponentID
ORDER BY ComponentID
LIMIT 10
"""


with GraphDatabase.driver(URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD)) as driver:
    driver.verify_connectivity()
    
    with driver.session(database="neo4j") as session:
       
       
       session.execute_write(lambda tx: tx.run(drop_query).consume())


       res1 = session.execute_read(lambda tx: list(tx.run(query1)))
       for rec in res1:
           print(f"Airport: {rec['Name']} | Operating Airlines: {rec['Operating_Airlines']}")

       
       res2 = session.execute_read(lambda tx: list(tx.run(query2)))
       for rec in res2:
           print(f"Airports with multi-stops: {rec['Airports_with_multi_stops']}")

     
       res3 = session.execute_read(lambda tx: list(tx.run(query3)))
       for rec in res3:
           print(f"Airline: {rec['Airline_Name']} | Airports Operating: {rec['Airports_operating_airline']}")

      
       p_res = session.execute_write(lambda tx: tx.run(Projection_query).single())
       print(f" Projected Graph: '{p_res['graphName']}' with {p_res['nodeCount']} nodes.")

       def run_pagerank(tx):
           result = tx.run(Pagerank_query)
           print("TOP 10 PAGERANK RESULTS")
           for record in result:
               print(f"Name: {record['Airport_Name']} | Score: {record['Score']:.4f}")
       
       session.execute_read(run_pagerank)

       def run_wcc(tx):
           result = tx.run(WCC_query)
           print(" TOP 10 WCC RESULTS")
           for record in result:
               print(f"Name: {record['Airport_Name']} | Component ID: {record['ComponentID']}")
       
       session.execute_read(run_wcc)
       
       session.execute_write(lambda tx: tx.run(drop_query).consume())



       
