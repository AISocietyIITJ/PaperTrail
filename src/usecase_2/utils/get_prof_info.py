from neo4j import GraphDatabase
from src.config import AURA_URI, AURA_USER, AURA_PASSWORD
from src.usecase_2.utils.score_metric import calculate_professor_score



def get_professors_by_interest_ids(driver,search_results):
    if isinstance(search_results, list):
        score_map = {
            item["vector_id"]: float(item["score"]) for item in search_results
        }
    elif isinstance(search_results, dict):
        score_map = {k: float(v) for k, v in search_results.items()}
    else:
        raise ValueError("search_results must be a list or a dict.")

    query = """
    MATCH (r:ResearchTopic)
    WHERE r.vector_id IN keys($score_map)
    MATCH (p:Professor)-[:WORKS_IN]->(r)
    WITH p, r, $score_map[r.vector_id] AS score
    RETURN 
        p.name AS professor_name,
        p.affiliation AS affiliation,
        p.profile_url AS profile_url,
        p.cited_by AS cited_by,
        p.h_index AS h_index,
        collect(DISTINCT {
            interest_id: r.vector_id,
            topic_name: r.name,
            score: score
        }) AS matched_topics,
        count(DISTINCT r) AS matching_topic_count
    ORDER BY matching_topic_count DESC;
    """

    with driver.session() as session:
        result = session.run(query, score_map=score_map)
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

        for prof in professors_list:
            score_list = []
            for topic in prof["matched_topics"]:
                score_list.append(topic['score'])
            # print("Score list",score_list)
            
            prof['avg_score'] = sum(score_list)/len(score_list)
            prof['rank_score'] = (calculate_professor_score(prof['avg_score'],prof['h_index'],prof['cited_by']))

        return professors_list

    finally:
        driver.close()

