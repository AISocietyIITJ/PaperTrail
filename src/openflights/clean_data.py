from pathlib import Path
import pandas as pd

RAW_DIR = Path(__file__).resolve().parents[2] / "data" / "raw"
PROCESSED_DIR = Path(__file__).resolve().parents[2] / "data" / "processed"

AIRPORT_COLS = [
    "airport_id", "name", "city", "country", "iata", "icao",
    "latitude", "longitude", "altitude", "timezone", "dst",
    "tz_database", "type", "source",
]

AIRLINE_COLS = [
    "airline_id", "name", "alias", "iata", "icao",
    "callsign", "country", "active",
]

ROUTE_COLS = [
    "airline", "airline_id", "source_airport", "source_airport_id",
    "destination_airport", "destination_airport_id", "codeshare",
    "stops", "equipment",
]


def clean_airports() -> pd.DataFrame:
    df = pd.read_csv(
        RAW_DIR / "airports.dat", header=None, names=AIRPORT_COLS, na_values=["\\N"]
    )
    df["airport_id"] = pd.to_numeric(df["airport_id"], errors="coerce")
    df = df.dropna(subset=["airport_id"])
    df["airport_id"] = df["airport_id"].astype(int)
    return df


def clean_airlines() -> pd.DataFrame:
    df = pd.read_csv(
        RAW_DIR / "airlines.dat", header=None, names=AIRLINE_COLS, na_values=["\\N"]
    )
    df["airline_id"] = pd.to_numeric(df["airline_id"], errors="coerce")
    df = df.dropna(subset=["airline_id"])
    df["airline_id"] = df["airline_id"].astype(int)
    return df


def clean_routes() -> pd.DataFrame:
    df = pd.read_csv(
        RAW_DIR / "routes.dat", header=None, names=ROUTE_COLS, na_values=["\\N"]
    )
    df["airline_id"] = df["airline_id"].astype(object).where(df["airline_id"].notna(), None)
    df["source_airport_id"] = pd.to_numeric(df["source_airport_id"], errors="coerce")
    df["destination_airport_id"] = pd.to_numeric(
        df["destination_airport_id"], errors="coerce"
    )

    before = len(df)
    df = df.dropna(subset=["source_airport_id", "destination_airport_id"])
    after = len(df)
    print(f"Routes: dropped {before - after} rows with missing airport IDs "
          f"({before} -> {after})")

    df["source_airport_id"] = df["source_airport_id"].astype(int)
    df["destination_airport_id"] = df["destination_airport_id"].astype(int)
    df["airline_id"] = df["airline_id"].astype("Int64")  # nullable int, some airlines missing
    return df


def main():
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    airports = clean_airports()
    airlines = clean_airlines()
    routes = clean_routes()

    airports.to_csv(PROCESSED_DIR / "airports.csv", index=False)
    airlines.to_csv(PROCESSED_DIR / "airlines.csv", index=False)
    routes.to_csv(PROCESSED_DIR / "routes.csv", index=False)

    print(f"Airports: {len(airports)} rows")
    print(f"Airlines: {len(airlines)} rows")
    print(f"Routes: {len(routes)} rows")


if __name__ == "__main__":
    main()