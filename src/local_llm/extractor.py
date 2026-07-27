#core logic 
# user query -> call ollama -> recieve response -> convert json -> return python object


import json

from .client import client
from .prompts import SYSTEM_PROMPT


def extract_information(user_query: str) -> dict:
    """
    Extract keyphrases, aliases and interest topics
    from a research-related user query.
    """

    response = client.chat(
        model="qwen2.5:3b",
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": user_query
            }
        ]
    )

    output = response["message"]["content"]

    return json.loads(output)


def get_interest_topics(user_query: str):

    result = extract_information(user_query)

    if(result["keyphrases"] == result["interest_topics"]):
        interest_topics = ", ".join(result.get("interest_topics", []))
        return f"{interest_topics}"
    
    interest_topics = ", ".join(result.get("interest_topics", []))
    details = ", ".join(result.get("keyphrases", []))
    
    return f"{interest_topics}: {details}"