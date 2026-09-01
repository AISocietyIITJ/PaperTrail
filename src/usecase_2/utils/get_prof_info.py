from neo4j import GraphDatabase
from src.config import AURA_URI, AURA_USER, AURA_PASSWORD
from src.usecase_2.utils.score_metric import calculate_professor_score
from src.logger import logger


def get_professors_by_interest_ids(driver, search_results):
    logger.info("Building score map from search results")

    if isinstance(search_results, list):
        score_map = {
            item["vector_id"]: float(item["score"]) for item in search_results
        }
    elif isinstance(search_results, dict):
        score_map = {k: float(v) for k, v in search_results.items()}
    else:
        logger.error(f"Invalid search_results type: {type(search_results)}")
        raise ValueError("search_results must be a list or a dict.")

    logger.debug(f"Score map has {len(score_map)} entries: {score_map}")

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

    logger.info("Running Neo4j query to fetch matching professors")
    try:
        with driver.session() as session:
            result = session.run(query, score_map=score_map)
            professors = [record.data() for record in result]
    except Exception:
        logger.exception("Neo4j query execution failed")
        raise

    logger.info(f"Retrieved {len(professors)} professors from graph DB")
    return professors


def query_graph_db(interest_id_list: list):
    logger.info(f"Connecting to Neo4j Aura at {AURA_URI}")
    driver = GraphDatabase.driver(
        AURA_URI, auth=(AURA_USER, AURA_PASSWORD)
    )

    interest_ids = interest_id_list

    try:
        professors_list = get_professors_by_interest_ids(
            driver, interest_ids
        )

        logger.info("Calculating average and rank scores for professors")
        for prof in professors_list:
            score_list = []
            for topic in prof["matched_topics"]:
                score_list.append(topic['score'])

            if not score_list:
                logger.warning(f"No matched topic scores for professor: {prof.get('professor_name')}")
                prof['avg_score'] = 0
            else:
                prof['avg_score'] = sum(score_list) / len(score_list)

            prof['rank_score'] = (
                calculate_professor_score(prof['avg_score'], prof['h_index'], prof['cited_by'])
            )
            logger.debug(
                f"{prof.get('professor_name')} | avg_score={prof['avg_score']:.4f} "
                f"| rank_score={prof['rank_score']}"
            )

        professors_list.sort(key=lambda professor: professor['rank_score'], reverse=True)
        logger.info(f"Ranked {len(professors_list)} professors successfully")
        return professors_list

    except Exception:
        logger.exception("Error occurred while querying graph DB")
        raise

    finally:
        logger.info("Closing Neo4j driver connection")
        driver.close()

