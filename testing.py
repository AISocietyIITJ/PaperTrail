from neo4j import GraphDatabase
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from config import aura_uri,aura_password,aura_user
from ranking import calculate_professor_score

AURA_URI = aura_uri
AURA_USER = aura_user
AURA_PASSWORD = aura_password


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


def query_graph_db(vector_search_matches:list):
    driver = GraphDatabase.driver(
        AURA_URI, auth=(AURA_USER, AURA_PASSWORD)
    )

    try:
        professors_list = get_professors_by_interest_ids(
            driver, vector_search_matches
        )

        print(f"      Found {len(professors_list)} connected professor(s)")
        print("      " + "-" * 72)
        for prof in professors_list:
            print(f"      Name        : {prof['professor_name']}")
            print(f"      Affiliation : {prof['affiliation']}")
            print(f"      Scholar URL : {prof['profile_url']}")
            print(f"      Citations   : {prof['cited_by']}")
            print(f"      H-index     : {prof['h_index']}")
            print("      Matched Topics:")
            score_list = []
            for topic in prof["matched_topics"]:
                score_list.append(topic['score'])
                print(
                    f"    - [{topic['interest_id']}] {topic['topic_name']} (Score: {topic['score']:.4f})"
                )
            print("Score list",score_list)
            
            prof['avg_score'] = sum(score_list)/len(score_list)
            prof['rank_score'] = (calculate_professor_score(prof['avg_score'],prof['h_index'],prof['cited_by']))

            print("      " + "-" * 72)
        return professors_list


    finally:
        driver.close()


x = [{'vector_id': 'interest_2', 'score': 0.634656906}, {'vector_id': 'interest_3', 'score': 0.539255142}, {'vector_id': 'interest_36', 'score': 0.517588615}, {'vector_id': 'interest_461', 'score': 0.517588615}, {'vector_id': 'interest_71', 'score': 0.516258299}, {'vector_id': 'interest_463', 'score': 0.516258299}]

print(query_graph_db(x))

# for data in a :
#     print(data)
#     scores = data['matched_topics']
#     score_list = []
#     for score in scores:
#         score_list.append(score['score'])

#     print("Scorelist are :- ",score_list)
#     print("Average Score:-", sum(score_list)/len(score_list))
#     print("-"*70)
#     print("\n")

# query_graph_db(x)
