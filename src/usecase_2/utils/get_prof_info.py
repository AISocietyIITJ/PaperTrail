from neo4j import GraphDatabase
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from config import aura_uri,aura_password,aura_user


AURA_URI = aura_uri
AURA_USER = aura_user
AURA_PASSWORD = aura_password


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

        print(f"      Found {len(professors_list)} connected professor(s)")
        print("      " + "-" * 72)
        for prof in professors_list:
            print(f"      Name        : {prof['professor_name']}")
            print(f"      Affiliation : {prof['affiliation']}")
            print(f"      Scholar URL : {prof['profile_url']}")
            print(f"      Citations   : {prof['cited_by']}")
            print(f"      H-index     : {prof['h_index']}")
            print(
                f"      Interests   : {prof['matching_interest_count']} matched - {', '.join(map(str, prof['matched_interests']))}"
            )
            print("      " + "-" * 72)

    finally:
        driver.close()

# query_graph_db(["interest_3"])
