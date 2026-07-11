from openflights.db import get_driver


def project_graph(session):
    session.run("CALL gds.graph.drop('flightNetwork', false)")  # clean slate if rerun
    session.run(
        """
        CALL gds.graph.project(
            'flightNetwork',
            'Airport',
            'ROUTE'
        )
        """
    )
    print("Graph projected as 'flightNetwork'.")


def run_pagerank(session, top_n: int = 10):
    result = session.run(
        """
        CALL gds.pageRank.stream('flightNetwork')
        YIELD nodeId, score
        RETURN gds.util.asNode(nodeId).name AS airport,
               gds.util.asNode(nodeId).iata AS iata,
               score
        ORDER BY score DESC
        LIMIT $top_n
        """,
        top_n=top_n,
    )
    return [dict(r) for r in result]

def largest_community_countries(session, community_id: int):
    result = session.run(
        """
        CALL gds.louvain.stream('flightNetwork')
        YIELD nodeId, communityId
        WHERE communityId = $community_id
        RETURN gds.util.asNode(nodeId).country AS country, count(*) AS airport_count
        ORDER BY airport_count DESC
        LIMIT 10
        """,
        community_id=community_id,
    )
    return [dict(r) for r in result]


def run_louvain(session, top_n: int = 10):
    result = session.run(
        """
        CALL gds.louvain.stream('flightNetwork')
        YIELD nodeId, communityId
        RETURN communityId, count(*) AS size
        ORDER BY size DESC
        LIMIT $top_n
        """,
        top_n=top_n,
    )
    return [dict(r) for r in result]



def main():
    driver = get_driver()
    with driver.session() as session:
        project_graph(session)

        print("\n--- PageRank (top 10 most central airports) ---")
        for row in run_pagerank(session):
            print(row)

        print("\n--- Louvain (top 10 largest communities) ---")
        for row in run_louvain(session):
            print(row)

        print("\n--- Countries in largest community (id 3899) ---")
        for row in largest_community_countries(session, 3899):
            print(row)

    driver.close()


if __name__ == "__main__":
    main()