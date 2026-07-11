from openflights.db import get_driver


def run_query(session, query, **params):
    return [dict(r) for r in session.run(query, **params)]


def airport_by_iata(session, iata):
    return run_query(
        session,
        "MATCH (a:Airport {iata: $iata}) RETURN a.name, a.city, a.country",
        iata=iata,
    )


def airlines_in_country(session, country):
    return run_query(
        session,
        "MATCH (a:Airline {country: $country}) RETURN a.name, a.iata ORDER BY a.name",
        country=country,
    )

def top_airports_by_outgoing_routes(session, limit=10):
    return run_query(
        session,
        """MATCH (a:Airport)-[r:ROUTE]->()
           RETURN a.name AS airport, a.iata AS iata, count(r) AS outgoing_routes
           ORDER BY outgoing_routes DESC LIMIT $limit""",
        limit=limit,
    )


def direct_non_codeshare_routes(session, source_iata, dest_iata):
    return run_query(
        session,
        """MATCH (src:Airport {iata: $source_iata})-[r:ROUTE]->(dst:Airport {iata: $dest_iata})
           WHERE r.codeshare IS NULL OR r.codeshare <> 'Y'
           RETURN r.airline AS airline, r.stops AS stops, r.equipment AS equipment""",
        source_iata=source_iata,
        dest_iata=dest_iata,
    )


def airports_within_two_hops(session, source_iata):
    return run_query(
        session,
        """MATCH (a:Airport {iata: $source_iata})-[:ROUTE*1..2]->(b:Airport)
           RETURN DISTINCT b.name AS airport, b.iata AS iata LIMIT 25""",
        source_iata=source_iata,
    )


def shortest_path(session, source_iata, dest_iata):
    return run_query(
        session,
        """MATCH p = shortestPath((a:Airport {iata: $source_iata})-[:ROUTE*]-(b:Airport {iata: $dest_iata}))
           RETURN length(p) AS hops, [n IN nodes(p) | n.iata] AS route""",
        source_iata=source_iata,
        dest_iata=dest_iata,
    )



def main():
    driver = get_driver()
    with driver.session() as session:
        print("\n--- Lookup: JFK ---", airport_by_iata(session, "JFK"))
        print("\n--- Airlines in India ---", airlines_in_country(session, "India")[:10])
        print("\n--- Top 10 by outgoing routes ---", top_airports_by_outgoing_routes(session))
        print("\n--- DEL -> BOM direct, non-codeshare ---", direct_non_codeshare_routes(session, "DEL", "BOM"))
        print("\n--- Within 2 hops of DEL ---", airports_within_two_hops(session, "DEL"))
        print("\n--- Shortest path DEL -> JFK ---", shortest_path(session, "DEL", "JFK"))
    driver.close()


if __name__ == "__main__":
    main()