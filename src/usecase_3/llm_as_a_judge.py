from ollama import Client
from src.config import REPHRASING_API_KEY
from src.usecase_3.llm_rephrase_prompt import LLM_AS_A_JUDGE_PROMPT
import json

client = Client(
    host="https://ollama.com",
    headers={"Authorization": f"Bearer {REPHRASING_API_KEY}"}
)
def llm_as_a_judge(query_title_abs):
    response= client.chat(
            model='gemma4',
            format='json',
            options={'temperature': 0.0},
            messages=[
                {
                    "role":"system",
                    "content": LLM_AS_A_JUDGE_PROMPT
                },
                {
                    "role":"user",
                    "content": query_title_abs
                }
            ]
        )

    output=response.message.content.strip()
    cleaned_response = output.strip()
    if cleaned_response.startswith("```json"):
        cleaned_response = cleaned_response[7:]
    if cleaned_response.startswith("```"):
        cleaned_response = cleaned_response[3:]
    if cleaned_response.endswith("```"):
        cleaned_response = cleaned_response[:-3]

    cleaned_response = cleaned_response.strip()
    cleaned_response = cleaned_response.replace("\\n", "\n")

    final_response= json.loads(cleaned_response)
    return final_response

def main():
    with open('benchmark_reranked_jina.json',"r",encoding="utf-8") as f:
        rr_benchmarks= json.load(f)

    for idx,obj in enumerate(rr_benchmarks):
        query= obj['query']

        candidates=obj['candidates']

        for candidate in candidates:
            title = candidate.get('title','')
            abstract= candidate.get('abstract','')

            query_title_abs = f"query:{query}\nTitle: {title}\nAbstract: {abstract}"
            benchmarks_llm_graded=llm_as_a_judge(query_title_abs)

            candidate['llm_grade']= benchmarks_llm_graded[0]


        with open("benchmark_llm_graded_jina.json", "w", encoding="utf-8") as f:
            json.dump(rr_benchmarks, f, indent=2)

if __name__=="__main__":
    main()

