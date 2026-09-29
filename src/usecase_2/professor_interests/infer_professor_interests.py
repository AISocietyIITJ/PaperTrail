import ast
import json
import pandas as pd

from src.usecase_2.local_llm.client import client
from src.logger import logger

from src.usecase_2.professor_interests.professor_prompt import SYSTEM_PROMPT


INPUT_FILE = "data/professor_all.csv"
OUTPUT_FILE = "data/professor_all_with_interests.csv"


def parse_research_papers(papers):
    """
    Convert the Research Papers column from a string representation
    of a Python list into an actual Python list.
    """

    if pd.isna(papers):
        return []

    if isinstance(papers, list):
        return papers

    try:
        parsed = ast.literal_eval(papers)

        if isinstance(parsed, list):
            return parsed

        return []

    except (ValueError, SyntaxError):
        logger.warning("Could not parse research papers")
        return []


def infer_interest_domains(research_papers):
    """
    Use the local LLM to infer research interest domains
    from the professor's research paper titles.
    """

    if not research_papers:
        return []

    papers_text = "\n".join(
        f"{i + 1}. {paper}"
        for i, paper in enumerate(research_papers)
    )

    user_prompt = f"""
Here are the top research paper titles of a professor:

{papers_text}

Infer the main research interest domains represented by these papers.

Return the result strictly in this JSON format:

{{
    "interest_domains": []
}}
"""

    logger.info("Sending research papers to local LLM")

    response = client.chat(
        model="qwen2.5:3b",
        format="json",
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": user_prompt
            }
        ]
    )

    output = response["message"]["content"].strip()

    logger.debug(f"Raw LLM response: {output}")

    result = json.loads(output)

    return result.get("interest_domains", [])


def main():
    logger.info("Loading professor CSV")

    df = pd.read_csv(INPUT_FILE)

    logger.info(f"Loaded {len(df)} professors")

    # Create the column if it does not already exist
    if "Interest Domains" not in df.columns:
        df["Interest Domains"] = ""

    total = len(df)

    for index, row in df.iterrows():

        professor_name = row["Name"]

        # Skip professors that have already been processed
        existing_result = row["Interest Domains"]

        if pd.notna(existing_result) and str(existing_result).strip():
            logger.info(
                f"Skipping {professor_name} "
                f"({index + 1}/{total}) - already processed"
            )
            continue

        logger.info(
            f"Processing professor {index + 1}/{total}: "
            f"{professor_name}"
        )

        research_papers = parse_research_papers(
            row["Research Papers"]
        )

        logger.info(
            f"Found {len(research_papers)} research papers"
        )

        # No papers available
        if not research_papers:
            logger.warning(
                f"No research papers found for {professor_name}"
            )

            df.at[index, "Interest Domains"] = "[]"

        else:
            try:
                domains = infer_interest_domains(
                    research_papers
                )

                df.at[index, "Interest Domains"] = json.dumps(
                    domains,
                    ensure_ascii=False
                )

                logger.info(
                    f"Interest domains for {professor_name}: "
                    f"{domains}"
                )

            except Exception:
                logger.exception(
                    f"Failed to infer domains for {professor_name}"
                )

                # Keep an empty result so the row can be retried later
                df.at[index, "Interest Domains"] = ""

        # Save every 50 professors
        if (index + 1) % 50 == 0:

            df.to_csv(
                OUTPUT_FILE,
                index=False
            )

            logger.info(
                f"Checkpoint saved at professor "
                f"{index + 1}/{total}"
            )

    # Final save
    df.to_csv(
        OUTPUT_FILE,
        index=False
    )

    logger.info(
        f"Finished processing all professors."
    )

    logger.info(
        f"Final output saved to: {OUTPUT_FILE}"
    )


if __name__ == "__main__":
    main()