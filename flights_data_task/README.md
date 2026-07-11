# OpenFlights Graph Pipeline 

DATASET :-

This project uses the OpenFlights dataset consisting of three raw `.dat` files:

- airports.dat – Information about airports
- airlines.dat – Information about airlines
- routes.dat – Flight routes between airports

Since the files do not contain column headers, headers were identified using the official OpenFlights documentation before preprocessing

SCHEMA DIAGRAM :-

                +----------------------+
                |      Airline         |
                +----------------------+
                | airlineId            |
                | name                 |
                | country              |
                | iata                 |
                | icao                 |
                | active               |
                +----------------------+

                         (Referenced by airlineId)

+----------------------+        ROUTE         +----------------------+
|      Airport         | ------------------> |      Airport         |
+----------------------+                     +----------------------+
| airportId            |                     | airportId            |
| name                 |                     | name                 |
| city                 |                     | city                 |
| country              |                     | country              |
| iata                 |                     | iata                 |
| icao                 |                     | icao                 |
| latitude             |                     | latitude             |
| longitude            |                     | longitude            |
+----------------------+                     +----------------------+

ROUTE properties:
• airlineId
• airlineCode
• stops
• equipment
• codeshare

 Graph Schema:

 Nodes:

**Airport**
- airport_id (unique)
- name
- city
- country
- iata
- icao
- latitude
- longitude

**Airline**
- airline_id (unique)
- name
- iata
- icao
- country
- active

 Relationships:

(:Airport)-[:ROUTE_TO]->(:Airport)

Properties:
- airline
- airline_id
- stops
- equipment
- codeshare

Airline nodes are imported separately. Flight routes are modeled directly as ROUTE_TO relationships between Airport nodes and store airline information as relationship properties

Data Preprocessing and Import :-

Preprocessing:

The original OpenFlights dataset is provided as raw `.dat` files without column names.

A preprocessing script (`scripts/preprocess.py`) was written to:

- Assign meaningful column names to each dataset.
- Load the files using Pandas.
- Check for missing values.
- Verify data types.
- Export cleaned CSV files for Neo4j import.

Generated files:

- cleaned/airports.csv
- cleaned/airlines.csv
- cleaned/routes.csv


 Import into Neo4j:

The cleaned CSV files were imported into Neo4j using Cypher's `LOAD CSV` command.

Airport nodes were created first:

```cypher
LOAD CSV WITH HEADERS FROM 'file:///airports.csv' AS row
MERGE (a:Airport {airport_id: toInteger(row.airport_id)})
SET
a.name = row.name,
a.city = row.city,
a.country = row.country,
a.iata = row.iata,
a.icao = row.icao,
a.latitude = toFloat(row.latitude),
a.longitude = toFloat(row.longitude);
```
Uniqueness Constraint:

Prevents duplicate airport nodes.
Ensures each airport is represented exactly once.
Makes data consistent.

Index:

Speeds up searches by airport name.
Improves query performance for lookups.
Helpful when working with thousands of airports.

 Cypher Queries :

The following Cypher queries were executed to explore the graph:

- Count total airports
- Count total airlines
- Count total flight routes
- Find the top 10 busiest airports by outgoing routes
- Find the top 10 countries with the most airports
- List all active airlines

ALGORITHMS: 

1. PageRank : PageRank identifies the most influential airports in the global flight network. Airports with the highest PageRank are well connected and receive routes from other important airports.
2. Weakly Connected Components : Weakly Connected Components identify clusters of airports that are connected through flight routes. The largest component represents the main global flight network.

Before running Graph Data Science algorithms, an in-memory graph projection named `flightGraph` was created using Airport nodes and ROUTE_TO relationships.

 Handling Missing and Broken Data :

During preprocessing, missing values represented by `\N` were converted to null values.

Routes referencing airports that were not present in the airports dataset were removed before import.

This ensured that all ROUTE_TO relationships connected valid Airport nodes and prevented invalid graph relationships.

FINAL STRUCTURE :

graph_task/
│
├── cleaned/
│   ├── airports.csv
│   ├── airlines.csv
│   └── routes.csv
│
├── cypher/
│   └── queries.cql
│
├── data/
│   ├── airports.dat
│   ├── airlines.dat
│   └── routes.dat
│
├── scripts/
│   ├── preprocess.py
│   └── run_cypher_queries.py
│
├── README.md
├── requirements.txt
└── .gitignore