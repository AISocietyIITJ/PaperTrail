from neo4j import GraphDatabase
from src.config import AURA_URI, AURA_USER, AURA_PASSWORD



def get_professors_by_interest_ids(driver, interest_ids):
    query = """
    MATCH (r:ResearchTopic)
    WHERE r.vector_id IN $interest_ids
    MATCH (p:Professor)-[:WORKS_IN]->(r)
    RETURN 
        p.name AS professor_name,
        p.affiliation AS affiliation,
        p.profile_url AS profile_url,
        p.cited_by AS cited_by,
        p.h_index AS h_index,
        collect(DISTINCT r.name) AS matched_interests,
        count(DISTINCT r) AS matching_interest_count
    ORDER BY cited_by DESC;
    """

    with driver.session() as session:
        result = session.run(query, interest_ids=interest_ids)
        professors = [record.data() for record in result]

    return professors


def query_graph_db(interest_id_list:list):
    driver = GraphDatabase.driver(
        AURA_URI, auth=(AURA_USER, AURA_PASSWORD)
    )

    interest_ids = interest_id_list

    try:
        professors_list = get_professors_by_interest_ids(
            driver, interest_ids
        )

        return professors_list

    finally:
        driver.close()

# query_graph_db(["interest_3"])
