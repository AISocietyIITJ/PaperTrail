# Airline Routes Graph with Neo4j

This directory builds and analyses an airline-route graph in Neo4j. It uses the
[OpenFlights dataset](https://openflights.org/data.html) to model airports,
airlines, and individual routes, then runs Cypher and Neo4j Graph Data Science
(GDS) analyses.

## Graph model(Schema)

```text
(:Airport)-[:TAKING_OFF]->(:Route)-[:LANDING]->(:Airport)
                             |
                       [:OPERATED_BY]
                             v
                         (:Airline)
```

- `Airport`: ID, name, location, IATA/ICAO codes, and geographic metadata.
- `Airline`: ID, name, codes, country, and active status.
- `Route`: a route operated by an airline, including codeshare, stops, and
  equipment. Its ID combines source airport, destination airport, and airline.

The included CSV files are prepared copies of the OpenFlights `airports.dat`,
`airlines.dat`, and `routes.dat` datasets. Missing values are normalized to
`Unknown`.

## Schema design justification

![alt text](<schema.png>)

Using a `Route` node rather than a direct
`Airport-[:FLIES_TO]->Airport` relationship is intentional. The Route node gives the info about the Stops mades during the journey and at the same time it allows to connect to the node `Airlines` to get info about operating airline for the given journey.

## Prerequisites

- Python 3.10+ recommended
- A Neo4j database; the Graph Data Science plugin is additionally required for
  `GDS.py`
- The Python packages `neo4j`, `pandas`, and `python-dotenv`

Install the missing project dependencies if needed:

```bash
pip install neo4j pandas python-dotenv
```

Create a `.env` file in the repository root (or in this directory when running
the scripts from here):

```dotenv
PASSWORD=your_neo4j_password
```

`config.py` reads this value and the scripts use the configured Neo4j Aura URI
and username.

## Run the workflow

Run commands from the `Neo4j` directory so the local `config` module resolves:

```bash
cd Neo4j
```

1. **Prepare data (optional).** `datasets.py` replaces `-` and ` NaN ` values in the local
   CSV files with `Unknown`. 

   ```bash
   python datasets.py
   ```

2. **Ingest the graph.** `data_ingestion.py` loads the versioned CSV files from
   GitHub using Cypher `LOAD CSV`, creates nodes and relationships with `MERGE`,
   and enriches airport properties.

   ```bash
   python data_ingestion.py
   ```

   The ingestion currently limits route rows to 10,000. Remove or adjust
   `WITH routes LIMIT 10000` to load more of the dataset. The remote CSV URLs
   must also remain publicly reachable by the Neo4j server.

3. **Run example Cypher queries.**

   ```bash
   python queries.py
   ```

   On running, it prints US-airline departure airports, the ten busiest transit
   hubs (inbound + outbound route count), and the ten airlines operating the
   most routes.

4. **Run graph algorithms.**

   ```bash
   python GDS.py
   ```

   This projects airport-to-airport connectivity through `Route` nodes, then:

   - writes PageRank scores to `Airport.pagerank` and prints the top 10 hubs;
   - writes Louvain community IDs to `Airport.louvain` and prints the largest
     airport communities.

   Each in-memory GDS projection is dropped after its algorithm completes;
   the written airport properties remain in Neo4j.
