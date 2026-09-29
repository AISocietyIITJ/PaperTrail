import json
import random
from ollama import Client
from src.config import REPHRASING_API_KEY,PINECONE_API_KEY
from pinecone import Pinecone
from src.usecase_3.llm_rephrase_prompt import GENERATE_ADV_QUERY_PROMPT

client = Client(
    host="https://ollama.com",
    headers={"Authorization": f"Bearer {REPHRASING_API_KEY}"}
)

def adv_query_generator_fn(content_text):
    response= client.chat(
            model='gemma4',
            format='json',
            messages=[
                {
                    "role":"system",
                    "content": GENERATE_ADV_QUERY_PROMPT
                },
                {
                    "role":"user",
                    "content": content_text
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
    content= """
Large-scale vision and language representation learning has shown promising improvements on various vision-language tasks. Most existing methods employ a transformer-based multimodal encoder to jointly model visual tokens (region-based image features) and word tokens. Because the visual tokens and word tokens are unaligned, it is challenging for the multimodal encoder to learn image-text interactions. In this paper, we introduce a contrastive loss to ALign the image and text representations BEfore Fusing (ALBEF) them through cross-modal attention, which enables more grounded vision and language representation learning. Unlike most existing methods, our method does not require bounding box annotations nor high-resolution images. In order to improve learning from noisy web data, we propose momentum distillation, a self-training method which learns from pseudo-targets produced by a momentum model. We provide a theoretical analysis of ALBEF from a mutual information maximization perspective, showing that different training tasks can be interpreted as different ways to generate views for an image-text pair. ALBEF achieves state-of-the-art performance on multiple downstream vision-language tasks. On image-text retrieval, ALBEF outperforms methods that are pre-trained on orders of magnitude larger datasets. On VQA and NLVR$^2$, ALBEF achieves absolute improvements of 2.37% and 3.84% compared to the state-of-the-art, while enjoying faster inference speed. Code and pre-trained models are available at https://github.com/salesforce/ALBEF/.
"""
    outputs= adv_query_generator_fn(content)

    with open('adversial_queries.json',"w",encoding='utf-8') as f:
        json.dump(outputs,f,indent=2)

if __name__=="__main__":
    main()