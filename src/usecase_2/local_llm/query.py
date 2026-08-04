#testing file

from src.usecase_2.local_llm.extractor import (
    extract_information,
    get_interest_topics,
)


def main():

    query = input("Enter your query: ")

    print("\nExtracted Information\n")

    result = extract_information(query)

    print(result)

    print("\nInterest Topics\n")
    print(result["interest_topics"])

  # LLMs called only once because they are probabilistic and two responses can differ 


if __name__ == "__main__":
    main()