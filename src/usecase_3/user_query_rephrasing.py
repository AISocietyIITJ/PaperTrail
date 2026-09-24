import json
from ollama import Client
from pathlib import Path
from src.usecase_3.llm_rephrase_prompt import PROMPT_TO_LLM
import src.config

api_key = str(src.config.REPHRASING_API_KEY)


client = Client(
    host="https://ollama.com",
    headers={"Authorization": f"Bearer {api_key}"}
)

def rephrase_user_query(user_query:str):
    response= client.chat(
        model='gemma4',
        format='json',
        messages=[
            {
                "role":"system",
                "content": PROMPT_TO_LLM,
            },
            {
                "role":"user",
                "content":user_query
            }
        ]
    )

    output=response['message']['content'].strip()

    return output

def main():
    query= input("Enter your query:\n")
    rephrased_query= rephrase_user_query(user_query=query)
    print("\n")
    print(rephrased_query)

if __name__=="__main__":
    main()



