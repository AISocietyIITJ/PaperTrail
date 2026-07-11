# OpenFlights Graph Network Analysis

A Neo4j graph built from the raw OpenFlights dataset (airports, airlines,
routes), used to run Cypher queries and Graph Data Science algorithms to
find some insights about the global flight network.

#### Column Schema (raw `.dat` files have no headers)

The `.dat` files don't have headers, so columns had to be mapped
manually using the OpenFlights schema docs (https://openflights.org/data.php).

**airports.dat columns:** airport_id, name, city, country, iata, icao,
latitude, longitude, altitude, timezone, dst, tz_database, type, source

**airlines.dat columns:** airline_id, name, alias, iata, icao, callsign,
country, active

**routes.dat columns:** airline, airline_id, source_airport,
source_airport_id, destination_airport, destination_airport_id,
codeshare, stops, equipment

Note: nulls in these files show up as the literal text `\N`, not a
blank cell. Had to handle this manually with `na_values=["\\N"]` in
pandas or it would just read `\N` as a normal string.

#### Graph Data Model

**Nodes:**
- `Airport` - airport_id (unique), name, city, country, iata, icao,
  latitude, longitude, altitude, timezone
- `Airline` - airline_id (unique), name, iata, icao, country, active

**Relationship:**
- `(Airport)-[:ROUTE {airline, airline_id, stops, equipment, codeshare}]->(Airport)`

**Why Airline is its own node and not just a route property:**
Airline has its own attributes (country, active status) separate from
any one route, and you might want to ask questions like "which airports
does this airline fly to" - that needs Airline to be something you can
traverse to/from, not just a text label.

**Why routes are a direct Airport->Airport relationship instead of
going through a separate Route node:**
A route doesn't really have its own identity beyond connecting two
airports, so making it a direct edge with airline info as a property
keeps things simpler and faster to query than adding an extra hop.

**Constraints & indexes (set up before loading any data):**
- Uniqueness constraint on Airport.airport_id and Airline.airline_id -
  since ingestion uses MERGE and might get rerun while debugging, this
  stops duplicate nodes from building up
- Index on Airport.country - queries filter by country a lot, so this
  should make those faster

#### Handling Missing / Broken Data

routes.dat has some rows pointing to airport IDs that don't actually
exist in airports.dat. Handled this in two places:

- While cleaning: dropped 423 route rows (out of 67,663) that had a
  missing/broken source or destination airport ID
- While ingesting: used MATCH instead of MERGE for the airport
  endpoints, so if an airport doesn't exist, that route just gets
  skipped instead of creating a broken relationship. Another 469 rows
  got skipped here

Ended up with 66,771 ROUTE relationships in the final graph.

#### Cypher Queries

All in `src/openflights/queries.py`, run through the Python driver:

1. Look up an airport by IATA code (JFK)
2. All airlines based in a country (India)
3. Top 10 airports by outgoing routes
4. Direct non-codeshare routes between two airports (DEL -> BOM)
5. Variable-length path - airports within 1-2 hops of DEL
6. Shortest path between DEL and JFK using shortestPath()

Some results:
- Atlanta (ATL) has the most outgoing routes at 915, way ahead of
  Chicago O'Hare at 558
- DEL -> BOM has 5 airlines running it direct, no stops
- DEL -> JFK is actually just 1 hop, there's a direct flight

#### GDS Algorithms

`src/openflights/gds_algorithms.py` first creates a graph projection
called flightNetwork (this step is required before GDS algorithms can
run - they work off an in-memory copy, not the actual stored graph).

**PageRank (centrality)** - top result was Atlanta again, with a score
of about 29.5, almost double the next airport (Chicago, ~18.6). Since
PageRank looks at how important your connections are, not just how many
you have, this seemed like a stronger signal that Atlanta really is the
central hub of the whole network, not just the busiest by route count.

**Louvain (community detection)** - splits the graph into clusters.
Biggest cluster had 649 airports. Checked what countries were in it and
it was 410 US, 71 Canada, 56 Mexico, plus some Caribbean/Central
American countries - so it's basically a North American cluster. Makes
sense that airports would cluster by region since most routes are
probably short-haul/regional.

####  A Few Insights

1. Atlanta isn't just the busiest airport, its PageRank score is
   nearly 2x the next airport - so it's disproportionately central to
   the network, not just tied for "one of the busy ones."

2. The Louvain communities line up with real geography (checked this,
   didn't just assume it) - the biggest community is basically North
   America. So most of the network is regionally clustered, with fewer
   long routes connecting the regions together.

3. Delhi doesn't show up in the top 10 for routes or PageRank, but it
   has a direct flight to JFK and reaches a lot of hubs in Europe and
   the Gulf within 2 hops - so it's more of a regional connector than
   a top global hub.

#### How to Rebuild This From Scratch

Need Neo4j Desktop running locally with the GDS plugin installed, plus
Python 3.11+ and uv.

Create a `.env` file with:
```
NEO4J_URI=neo4j://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=<your password>
```

Install deps:
```bash
uv sync
```

Download the raw data:
```bash
curl -o data/raw/airports.dat https://raw.githubusercontent.com/jpatokal/openflights/master/data/airports.dat
curl -o data/raw/airlines.dat https://raw.githubusercontent.com/jpatokal/openflights/master/data/airlines.dat
curl -o data/raw/routes.dat https://raw.githubusercontent.com/jpatokal/openflights/master/data/routes.dat
```

Then run these in order (make sure Neo4j is showing RUNNING first):
```bash
uv run python -m openflights.clean_data
uv run python -m openflights.ingest
uv run python -m openflights.queries
uv run python -m openflights.gds_algorithms
```