# OpenFlights Graph Pipeline and Analysis

This project takes the OpenFlights dataset and ingests and analyzes it using a Neo4j Graph Database through python. The pipeline consists of data preprocessing, data ingestion into database, Cypher querying, and Graph Data Science algorithm execution on the database.

## 1. Schema
**Nodes:**
  - `Airport`: Represents a airport location . Key properties include `airport_id`, `name`, `city`, `country`, `iata`, and `latitude`, `longitude`.
  - `Airline`: Represents an airline company. Key properties include `airline_id`, `name`, `iata`, `country`, `icao`, and `active`.
**Relationships:**
  - `(Airport)-[ROUTES_TO]->(Airport)`: Represents the flight route between two airports.
  - **Decision:** The airline_id is stored directly as a property on this relationship to optimize graph traversals.
**Constraints & Indexes:**
  - Unique constraints are enforced on `Airport.airport_id` and `Airline.airline_id` to prevent duplicate entity creation during ingestion.
  - An index is applied to `Airport.country` to accelerate text-based geographic lookups.

  ## 2. Cypher Queries

  The `queries.py` file executes the following graph operations on the database:

  1. **Node Aggregation:** Grouping the entire dataset by country to calculate and rank the top 5 nations with the highest total number of airports.
  2. **Relationship Aggregation:** Calculates the top 5 most utilized airlines in the network.
  3. **Node Lookup:** Exact matching for an airport by its IATA code (`JFK`) to retrieve core properties like location, coordinates and ID.
  4. **Specific Pathfinding:**  Finds 1-stop layover routes between two specific cities (`Ahmedabad` and `Osaka`), strictly filtering out circular return paths.
  5. **Shortest Path:** Utilizing Neo4j's built-in `shortestPath()` algorithm to calculate the absolute minimum number of connections required to travel between two nodes.

  ## 3. Algorithm Results 

  The `gds.py` file runs two primary Graph Data Science (GDS) algorithms: PageRank and Louvain Community Detection.

  ### Insights

  1. **The Hub-and-Spoke Model (PageRank Insight):** 
   The algorithm proves the network relies heavily on massive central routing nodes rather than direct point-to-point flights. US mega-hubs dominate global influence, with Atlanta (ATL) having a PageRank score nearly double that of its competitors (Chicago, LAX, and DFW). Paris (CDG) emerged as the only non-US airport in the top 5.
  2. **Geographic Network Modularity (Louvain Insight):**
   The Louvain algorithm naturally partitioned the world’s airports based purely on flight density and frequency. This mathematically proves that global aviation is highly localized; the vast majority of air travel remains strictly within specific geographic continents, connected only by a few web of inter-continental "bridge" routes.

  ## 4. How to Rebuild the Project  
  
  ### Prerequisites

  1. **Neo4j Desktop or Neo4j AuraDB:** Installed and running.
  2. **Database Credentials:** A .env file located in the root directory of your project containing the username, password and uri of neo4j instance.
  3. **Python Dependencies:** Install the required packages via terminal:
  ```
  bash
  uv pip install pandas neo4j python-dotenv
  ```
  ### Execution
  Make sure the raw Openflight datasets are properly placed in the `data/` folder. Then, run the following files:

  1. **Clean the Data:**
   ```bash
   uv run python preprocess.py
   ```
   *This reads the raw `.dat` files, handles missing values, remove unwanted data, and outputs clean `.csv` files.*

2. **Ingest the Graph:**
   ```bash
   uv run python ingest.py
   ```
   *Connects to your Neo4j database and uploads all that clean data in batches from `.csv` files to construct the global network.*

3. **Run Queries:**
   ```bash
   uv run python queries.py
   ```
   *Asks the database our basic routing questions, like finding the shortest flight paths and ranking top airlines.*

4. **Run GDS Analysis:**
   ```bash
   uv run python gds.py
   ```
   *This projects the graph into memory and executes the PageRank and Louvain algorithms to generate insights.*

