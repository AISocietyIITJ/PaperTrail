from openflights.db import get_driver


def airports_in_country(session, country: str):
    result = session.run(
        "MATCH (a:Airport {country: $country}) RETURN a.name, a.city, a.iata "
        "ORDER BY a.name",
        country=country,
    )
    return [dict(r) for r in result]


def routes_operated_by_airline(session, airline_name: str):
    result = session.run(
        """
        MATCH ()-[r:ROUTE]->()
        WHERE r.airline = $airline_name
        RETURN count(r) AS route_count
        """,
        airline_name=airline_name,
    )
    return result.single()["route_count"]


def top_airports_by_outgoing_routes(session, limit: int = 10):
    result = session.run(
        """
        MATCH (a:Airport)-[r:ROUTE]->()
        RETURN a.name AS airport, a.iata AS iata, count(r) AS outgoing_routes
        ORDER BY outgoing_routes DESC
        LIMIT $limit
        """,
        limit=limit,
    )
    return [dict(r) for r in result]


def direct_non_codeshare_routes(session, source_iata: str, dest_iata: str):
    result = session.run(
        """
        MATCH (src:Airport {iata: $source_iata})-[r:ROUTE]->(dst:Airport {iata: $dest_iata})
        WHERE r.codeshare IS NULL OR r.codeshare <> 'Y'
        RETURN r.airline AS airline, r.stops AS stops, r.equipment AS equipment
        """,
        source_iata=source_iata,
        dest_iata=dest_iata,
    )
    return [dict(r) for r in result]


def airports_within_two_hops(session, source_iata: str):
    result = session.run(
        """
        MATCH (a:Airport {iata: $source_iata})-[:ROUTE*1..2]->(b:Airport)
        RETURN DISTINCT b.name AS airport, b.iata AS iata
        LIMIT 25
        """,
        source_iata=source_iata,
    )
    return [dict(r) for r in result]


def main():
    driver = get_driver()
    with driver.session() as session:
        print("\n--- Airports in India ---")
        for row in airports_in_country(session, "India")[:10]:
            print(row)

        print("\n--- Top 10 airports by outgoing routes ---")
        for row in top_airports_by_outgoing_routes(session):
            print(row)

        print("\n--- Direct non-codeshare routes DEL -> BOM ---")
        for row in direct_non_codeshare_routes(session, "DEL", "BOM"):
            print(row)

        print("\n--- Airports within 2 hops of DEL ---")
        for row in airports_within_two_hops(session, "DEL"):
            print(row)

    driver.close()


if __name__ == "__main__":
    main()