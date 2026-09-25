# testing file

from src.logger import logger

from src.usecase_2.local_llm.extractor import (
    extract_information,
    get_interest_topics,
)


def main():
    query = input("Enter your query: ")
    logger.info(f"Received query: {query}")

    logger.info("Starting information extraction")
    try:
        result = extract_information(query)
    except Exception as e:
        logger.exception(f"Extraction failed for query: {query}")
        raise

    logger.debug(f"Extraction result: {result}")
    print(result)

    logger.info("Fetching interest topics")
    print("\nInterest Topics\n")
    print(result["interest_topics"])

    # LLMs called only once because they are probabilistic and two responses can differ


if __name__ == "__main__":
    main()

