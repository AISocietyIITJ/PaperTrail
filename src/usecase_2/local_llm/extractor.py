#core logic 
# user query -> call ollama -> recieve response -> convert json -> return python object


import json

from .client import client
from .prompts import SYSTEM_PROMPT


def extract_information(user_query: str, resume_content:str) -> dict:
    """
    Extract keyphrases, aliases and interest topics
    from a research-related user query.
    """

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