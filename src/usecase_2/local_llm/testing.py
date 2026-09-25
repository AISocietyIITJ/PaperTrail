import os
import json
from ollama import Client
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.config import OLLAMA_API_KEY
from src.logger import logger

from src.usecase_2.local_llm.prompts import SYSTEM_PROMPT

key = str(OLLAMA_API_KEY)

client = Client(
    host="https://ollama.com",
    headers={'Authorization': 'Bearer ' + key}
)


def extract_information(user_query: str, resume_content: str) -> dict:
    """
    Extract keyphrases, aliases and interest topics
    from a research-related user query.
    """
    logger.info("Calling Ollama model gemma4:cloud for information extraction")
    logger.debug(f"User query: {user_query!r} | Resume content length: {len(resume_content)}")

    try:
        response = client.chat(
            model="gemma4:cloud",
            format="json",
            messages=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT
                },
                {
                    "role": "user",
                    "content": user_query + resume_content
                }
            ]
        )
    except Exception:
        logger.exception("Ollama client call failed")
        raise

    output = response["message"]["content"].strip()
    logger.debug(f"Raw model output: {output}")

    if output.startswith("```json"):
        output = output[7:]
    elif output.startswith("```"):
        output = output[3:]
    if output.endswith("```"):
        output = output[:-3]
    output = output.strip()

    try:
        parsed = json.loads(output)
    except json.JSONDecodeError:
        logger.exception(f"Failed to parse model output as JSON: {output!r}")
        raise

    logger.info("Successfully extracted information from model response")
    logger.debug(f"Parsed result: {parsed}")

    return parsed


def get_interest_topics(user_query: str, resume_path: str):
    logger.info("Getting interest topics")

    result = extract_information(user_query, resume_path)

    if result.get('interest_topics', []) == [] or result.get('keyphrases', []) == []:
        logger.warning("No interest_topics or keyphrases found in extraction result")
        return None

    if result["keyphrases"] == result["interest_topics"]:
        interest_topics = ", ".join(result.get("interest_topics", []))
        logger.debug(f"keyphrases match interest_topics: {interest_topics}")
        return f"{interest_topics}"

    interest_topics = ", ".join(result.get("interest_topics", []))
    details = ", ".join(result.get("keyphrases", []))

    logger.debug(f"interest_topics: {interest_topics} | keyphrases: {details}")

    return f"{interest_topics}: {details}"