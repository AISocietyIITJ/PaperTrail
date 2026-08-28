import json
import os

from .prompts import SYSTEM_PROMPT
from src.logger import logger


def extract_information(user_query: str, resume_content: str) -> dict:
    """
    Extract keyphrases, aliases and interest topics
    from a research-related user query.
    """
    gemini_api_key = os.environ.get("GEMINI_API_KEY")
    openai_api_key = os.environ.get("OPENAI_API_KEY")

    try:
        if gemini_api_key:
            from google import genai
            from google.genai import types

            logger.debug("Using Gemini backend (gemini-2.5-flash) for extraction")
            gemini_client = genai.Client(api_key=gemini_api_key)
            response = gemini_client.models.generate_content(
                model='gemini-2.5-flash',
                contents=user_query + "\n\n" + resume_content,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    response_mime_type="application/json",
                ),
            )
            output = response.text.strip()

        elif openai_api_key:
            from openai import OpenAI

            logger.debug("Using OpenAI backend (gpt-4o-mini) for extraction")
            openai_client = OpenAI(api_key=openai_api_key)
            response = openai_client.chat.completions.create(
                model="gpt-4o-mini",
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_query + "\n\n" + resume_content}
                ]
            )
            output = response.choices[0].message.content.strip()

        else:
            from .client import client

            logger.debug("Using local Ollama backend (qwen2.5:3b) for extraction")
            response = client.chat(
                model="qwen2.5:3b",
                format="json",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_query + resume_content}
                ]
            )
            output = response["message"]["content"].strip()

    except Exception:
        logger.exception("LLM call failed during information extraction")
        raise

    logger.debug(f"Raw LLM output (pre-clean): {output}")

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
        logger.exception(f"Failed to parse LLM output as JSON: {output!r}")
        raise

    logger.debug(f"Parsed extraction result: {parsed}")
    return parsed


def get_interest_topics(user_query: str, resume_path: str):
    logger.info("Extracting interest topics from user query")

    result = extract_information(user_query, resume_path)

    if result.get('interest_topics', []) == [] or result.get('keyphrases', []) == []:
        logger.warning("No interest_topics or keyphrases found in extraction result")
        return None

    if result["keyphrases"] == result["interest_topics"]:
        interest_topics = ", ".join(result.get("interest_topics", []))
        logger.debug("keyphrases and interest_topics are identical; skipping details")
        logger.info(f"Interest topics resolved: {interest_topics}")
        return f"{interest_topics}"

    interest_topics = ", ".join(result.get("interest_topics", []))
    details = ", ".join(result.get("keyphrases", []))

    logger.info(f"Interest topics resolved: {interest_topics} | details: {details}")
    return f"{interest_topics}: {details}"