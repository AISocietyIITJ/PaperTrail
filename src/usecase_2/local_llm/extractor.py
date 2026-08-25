import json
import os

from .prompts import SYSTEM_PROMPT


def extract_information(user_query: str, resume_content:str) -> dict:
    """
    Extract keyphrases, aliases and interest topics
    from a research-related user query.
    """
    gemini_api_key = os.environ.get("GEMINI_API_KEY")
    openai_api_key = os.environ.get("OPENAI_API_KEY")

    if gemini_api_key:
        from google import genai
        from google.genai import types
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
                    "content": user_query + resume_content
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