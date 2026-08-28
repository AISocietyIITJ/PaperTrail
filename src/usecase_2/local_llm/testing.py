import os
import json
from ollama import Client
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.config import OLLAMA_API_KEY

from src.usecase_2.local_llm.prompts import SYSTEM_PROMPT

key = str(OLLAMA_API_KEY)

client = Client(
    host="https://ollama.com",
    headers={'Authorization': 'Bearer ' + key}
)


def extract_information(user_query: str, resume_content:str) -> dict:
    """
    Extract keyphrases, aliases and interest topics
    from a research-related user query.
    """

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
                "content": user_query+resume_content
            }
        ]
    )

    output = response["message"]["content"].strip()
    if output.startswith("```json"):
        output = output[7:]
    elif output.startswith("```"):
        output = output[3:]
    if output.endswith("```"):
        output = output[:-3]
    output = output.strip()

    return json.loads(output)


def get_interest_topics(user_query: str, resume_path:str):

    result = extract_information(user_query,resume_path)

    if(result.get('interest_topics', []) == [] or result.get('keyphrases', []) == []):
        return None

    if(result["keyphrases"] == result["interest_topics"]):
        interest_topics = ", ".join(result.get("interest_topics", []))
        return f"{interest_topics}"
    
    interest_topics = ", ".join(result.get("interest_topics", []))
    details = ", ".join(result.get("keyphrases", []))
    
    return f"{interest_topics}: {details}"