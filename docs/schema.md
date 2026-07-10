# Schema

### 1. Column Mapping (Raw .dat files have no headers)

### airports.dat
| s.no | Column | Notes |
|------|--------|-------|
| 1    | Airport ID | Unique OpenFlights identifier |
| 2    | Name | Airport name |
| 3    | City | Main city served |
| 4    | Country | Country |
| 5    | IATA | 3-letter code, or "\N" if none |
| 6    | ICAO | 4-letter code, or "\N" if none |
| 7    | Latitude | Decimal degrees |
| 8    | Longitude | Decimal degrees |
| 9    | Altitude | Feet |
| 10   | Timezone | Hours offset from UTC |
| 11   | DST | Daylight savings type (E/A/S/O/Z/N/U) |
| 12   | Tz database timezone | e.g. "Asia/Kolkata" |
| 13   | Type | Usually "airport" |
| 14   | Source | Usually "OurAirports" |

### airlines.dat
| # | Column | Notes |
|---|--------|-------|
| 1 | Airline ID | Unique OpenFlights identifier |
| 2 | Name | Airline name |
| 3 | Alias | Alternate name, or "\N" |
| 4 | IATA | 2-letter code, or "\N" |
| 5 | ICAO | 3-letter code, or "\N" |
| 6 | Callsign | or "\N" |
| 7 | Country | Country of registration |
| 8 | Active | "Y"/"N" |

### routes.dat
| # | Column | Notes |
|---|--------|-------|
| 1 | Airline | 2-letter IATA or 3-letter ICAO code |
| 2 | Airline ID | References airlines.dat, may not exist |
| 3 | Source airport | Code |
| 4 | Source airport ID | References airports.dat, may not exist |
| 5 | Destination airport | Code |
| 6 | Destination airport ID | References airports.dat, may not exist |
| 7 | Codeshare | "Y" if codeshare, else blank |
| 8 | Stops | Number of stops (0 = direct) |
| 9 | Equipment | Space-separated aircraft codes |

**Null handling:** OpenFlights uses the literal string `\N` (backslash-N) to represent nulls — this will NOT be caught by pandas' default `NaN` detection and must be handled explicitly, e.g. `pd.read_csv(..., na_values=["\\N"])`.

## 2. Graph Schema Design

### Node labels
- **`Airport`** — properties: `airport_id` (unique), `name`, `city`, `country`, `iata`, `icao`, `latitude`, `longitude`, `altitude`, `timezone`
- **`Airline`** — properties: `airline_id` (unique), `name`, `iata`, `icao`, `country`, `active`

### Relationship type
- **`(:Airport)-[:ROUTE {airline_id, airline_name, stops, equipment, codeshare}]->(:Airport)`**

### Reasoning: why Airline is a NODE, not just a route property
Airline needs its own identity because:
1. It has its own attributes (country, active status, codes) independent of any single route
2. Meaningful queries need to traverse *through* it — e.g. "which airports does Delta serve" is a graph traversal question, not just a filter
3. GDS algorithms (e.g. community detection, centrality) become more interesting if airlines are queryable as entities connected to the network, not just labels

### Reasoning: why routes are direct Airport→Airport relationships (not Airport-Route-Airport)
A route is inherently a directed edge between two airports — modeling it as an intermediate `Route` node would add complexity without benefit, since a route doesn't have its own further