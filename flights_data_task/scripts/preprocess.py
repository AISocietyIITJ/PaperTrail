import pandas as pd

# -----------------------------
# File Paths
# -----------------------------
AIRPORTS_PATH = "data/airports.dat"
AIRLINES_PATH = "data/airlines.dat"
ROUTES_PATH = "data/routes.dat"

# -----------------------------
# Column Names
# -----------------------------

airport_columns = [
    "airport_id",
    "name",
    "city",
    "country",
    "iata",
    "icao",
    "latitude",
    "longitude",
    "altitude",
    "timezone",
    "dst",
    "tz_database",
    "type",
    "source"
]

airline_columns = [
    "airline_id",
    "name",
    "alias",
    "iata",
    "icao",
    "callsign",
    "country",
    "active"
]

route_columns = [
    "airline",
    "airline_id",
    "source_airport",
    "source_airport_id",
    "destination_airport",
    "destination_airport_id",
    "codeshare",
    "stops",
    "equipment"
]

# -----------------------------
# Read the .dat files
# -----------------------------

airports = pd.read_csv(
    AIRPORTS_PATH,
    header=None,
    names=airport_columns
)

airlines = pd.read_csv(
    AIRLINES_PATH,
    header=None,
    names=airline_columns
)

routes = pd.read_csv(
    ROUTES_PATH,
    header=None,
    names=route_columns
)

# Replace "\N" with missing values (NaN)

airports.replace("\\N", pd.NA, inplace=True)
airlines.replace("\\N", pd.NA, inplace=True)
routes.replace("\\N", pd.NA, inplace=True)

#missing val

print("\nMissing values in Airports")
print(airports.isna().sum())

print("\nMissing values in Airlines")
print(airlines.isna().sum())

print("\nMissing values in Routes")
print(routes.isna().sum())

#convert

# -----------------------------
# Convert numeric columns
# -----------------------------

airport_numeric = [
    "airport_id",
    "latitude",
    "longitude",
    "altitude",
    "timezone"
]

for col in airport_numeric:
    airports[col] = pd.to_numeric(airports[col], errors="coerce")

airline_numeric = [
    "airline_id"
]

for col in airline_numeric:
    airlines[col] = pd.to_numeric(airlines[col], errors="coerce")

route_numeric = [
    "airline_id",
    "source_airport_id",
    "destination_airport_id",
    "stops"
]

for col in route_numeric:
    routes[col] = pd.to_numeric(routes[col], errors="coerce")
    print("\n========== DATA TYPES ==========\n")

print("Airports")
print(airports.dtypes)

print("\nAirlines")
print(airlines.dtypes)

print("\nRoutes")
print(routes.dtypes)

# -----------------------------
# Get valid airport and airline IDs
# -----------------------------

valid_airports = set(airports["airport_id"].dropna())
valid_airlines = set(airlines["airline_id"].dropna())

print("\nRoutes before cleaning:", len(routes))

# Keep only routes whose source and destination airports exist
routes = routes[
    routes["source_airport_id"].isin(valid_airports) &
    routes["destination_airport_id"].isin(valid_airports)
]

# Keep routes with either:
# 1. Missing airline_id, OR
# 2. Valid airline_id
routes = routes[
    routes["airline_id"].isna() |
    routes["airline_id"].isin(valid_airlines)
]

# Number of routes after cleaning
print("Routes after cleaning:", len(routes))


# -----------------------------
# Save cleaned datasets
# -----------------------------

airports.to_csv(
    "cleaned/airports.csv",
    index=False
)

airlines.to_csv(
    "cleaned/airlines.csv",
    index=False
)

routes.to_csv(
    "cleaned/routes.csv",
    index=False
)