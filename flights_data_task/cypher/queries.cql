// ===============================
// Create Constraints
// ===============================

CREATE CONSTRAINT airport_id IF NOT EXISTS
FOR (a:Airport)
REQUIRE a.airport_id IS UNIQUE;

CREATE CONSTRAINT airline_id IF NOT EXISTS
FOR (a:Airline)
REQUIRE a.airline_id IS UNIQUE;


// ===============================
// Import Airports
// ===============================

LOAD CSV WITH HEADERS FROM 'file:///airports.csv' AS row
MERGE (a:Airport {airport_id: toInteger(row.airport_id)})
SET
a.name = row.name,
a.city = row.city,
a.country = row.country,
a.iata = row.iata,
a.icao = row.icao,
a.latitude = toFloat(row.latitude),
a.longitude = toFloat(row.longitude),
a.altitude = toInteger(row.altitude),
a.timezone = toFloat(row.timezone);


// ===============================
// Import Airlines
// ===============================

LOAD CSV WITH HEADERS FROM 'file:///airlines.csv' AS row
MERGE (a:Airline {airline_id: toInteger(row.airline_id)})
SET
a.name = row.name,
a.alias = row.alias,
a.iata = row.iata,
a.icao = row.icao,
a.callsign = row.callsign,
a.country = row.country,
a.active = row.active;


// ===============================
// Import Routes
// ===============================

LOAD CSV WITH HEADERS FROM 'file:///routes.csv' AS row
MATCH (src:Airport {airport_id: toInteger(row.source_airport_id)})
MATCH (dst:Airport {airport_id: toInteger(row.destination_airport_id)})
MERGE (src)-[:ROUTE_TO {
airline: row.airline,
stops: toInteger(row.stops),
equipment: row.equipment,
codeshare: row.codeshare
}]->(dst);


// ===============================
// Basic Queries
// ===============================

// Total Airports
MATCH (a:Airport)
RETURN count(a) AS Total_Airports;

// Total Airlines
MATCH (a:Airline)
RETURN count(a) AS Total_Airlines;

// Total Routes
MATCH ()-[r:ROUTE_TO]->()
RETURN count(r) AS Total_Routes;

// Top 10 busiest airports
MATCH (a:Airport)<-[r:ROUTE_TO]-()
RETURN a.name, a.city, a.country, count(r) AS Flights
ORDER BY Flights DESC
LIMIT 10;

// Airlines from India
MATCH (a:Airline)
WHERE a.country = "India"
RETURN a.name;

// Direct flights from Delhi
MATCH (a:Airport {city:"Delhi"})-[r:ROUTE_TO]->(b:Airport)
RETURN b.name, b.city, b.country
LIMIT 20;


// ===============================
// Graph Data Science
// ===============================

// Create Graph Projection
CALL gds.graph.project(
'flightGraph',
['Airport'],
{
ROUTE_TO: {
orientation: 'NATURAL'
}
}
);

// PageRank
CALL gds.pageRank.stream('flightGraph')
YIELD nodeId, score
RETURN
gds.util.asNode(nodeId).name AS Airport,
gds.util.asNode(nodeId).city AS City,
score
ORDER BY score DESC
LIMIT 10;

// Weakly Connected Components
CALL gds.wcc.stream('flightGraph')
YIELD nodeId, componentId
RETURN componentId, count(*) AS Airports
ORDER BY Airports DESC
LIMIT 10;

// Drop Graph Projection
CALL gds.graph.drop('flightGraph');


6 QUERIES USED : 
1 . Number of airports
MATCH (a:Airport)
RETURN count(a) AS TotalAirports;
2. Number of airlines 
MATCH ()-[r:ROUTE_TO]->()
RETURN count(r) AS TotalRoutes;
3. Number of routes 
MATCH ()-[r:ROUTE_TO]->()
RETURN count(r) AS TotalRoutes;
4. Top 10 airports with the most outgoing routes
MATCH (a:Airport)-[r:ROUTE_TO]->()
RETURN
a.name AS Airport,
count(r) AS OutgoingRoutes
ORDER BY OutgoingRoutes DESC
LIMIT 10;
5. Top 10 countries by number of airports 
MATCH (a:Airport)
RETURN
a.country AS Country,
count(a) AS Airports
ORDER BY Airports DESC
LIMIT 10;
6. Airlines marked active 
MATCH (a:Airline)
WHERE a.active = "Y"
RETURN count(a) AS ActiveAirlines;