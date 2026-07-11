import pandas as pd

airports = [
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
    "tz",
    "type",
    "source",
]
airlines = [
    "airline_id",
    "name",
    "alias",
    "iata",
    "icao",
    "callsign",
    "country",
    "active",
]
routes = [
    "airline",
    "airline_id",
    "source_airport",
    "source_airport_id",
    "destination_airport",
    "destination_airport_id",
    "codeshare",
    "stops",
    "equipment",
]


def clean_airports():
    data = pd.read_csv(
        "data/airports.dat", header=None, names=airports, na_values="\\N"
    )
    clean_data = data.dropna(subset=["airport_id"])
    clean_data = clean_data.fillna("")
    clean_data.to_csv("data/clean_airports.csv", index=False)


def clean_airlines():
    data = pd.read_csv(
        "data/airlines.dat", header=None, names=airlines, na_values="\\N"
    )
    clean_data = data.dropna(subset=["airline_id"])
    clean_data = clean_data.fillna("")
    clean_data.to_csv("data/clean_airlines.csv", index=False)


def clean_routes():
    data = pd.read_csv("data/routes.dat", header=None, names=routes, na_values="\\N")
    clean_data = data.dropna(
        subset=["airline_id", "source_airport_id", "destination_airport_id"]
    )
    clean_data = clean_data.fillna("")
    clean_data.to_csv("data/clean_routes.csv", index=False)


def main():
    clean_airports()
    clean_airlines()
    clean_routes()


if __name__ == "__main__":
    main()
