import torch
from transformers import AutoModel, AutoTokenizer, AutoModelForCausalLM
import numpy as np
# import gc

tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen3-Reranker-0.6B", padding_side='left')
model = AutoModelForCausalLM.from_pretrained("Qwen/Qwen3-Reranker-0.6B", torch_dtype= torch.bfloat16).eval()

token_false_id = tokenizer.convert_tokens_to_ids("no")
token_true_id = tokenizer.convert_tokens_to_ids("yes")
max_length = 512

prefix = "<|im_start|>system\nJudge whether the Document meets the requirements based on the Query and the Instruct provided. Note that the answer can only be \"yes\" or \"no\".<|im_end|>\n<|im_start|>user\n"
suffix = "<|im_end|>\n<|im_start|>assistant\n<think>\n\n</think>\n\n"
prefix_tokens = tokenizer.encode(prefix, add_special_tokens=False)
suffix_tokens = tokenizer.encode(suffix, add_special_tokens=False)

def format_instruction(instruction, query, doc):
    if instruction is None:
        instruction = 'Given a web search query, retrieve relevant passages that answer the query'
    output = "<Instruct>: {instruction}\n<Query>: {query}\n<Document>: {doc}".format(instruction=instruction,query=query, doc=doc)
    return output

def process_inputs(pairs):
    inputs = tokenizer(
        pairs, padding=True, truncation=True,
        return_attention_mask=True, max_length=1024
    )
    for i, ele in enumerate(inputs['input_ids']):
        inputs['input_ids'][i] = prefix_tokens + ele + suffix_tokens
    inputs = tokenizer.pad(inputs, padding=True, return_tensors="pt", max_length=max_length)
    for key in inputs:
        inputs[key] = inputs[key].to(model.device)
    return inputs

@torch.no_grad()
def compute_logits(inputs, **kwargs):
    batch_scores = model(**inputs).logits[:, -1, :]
    true_vector = batch_scores[:, token_true_id]
    false_vector = batch_scores[:, token_false_id]
    batch_scores = torch.stack([false_vector, true_vector], dim=1)
    batch_scores = torch.nn.functional.log_softmax(batch_scores, dim=1)
    scores = batch_scores[:, 1].exp().tolist()
    return scores


def return_reranked_docs(query, documents, top_n=5):        
    task = 'Given a web search query, retrieve relevant passages that answer the query'

    pairs = [format_instruction(task, query, doc) for doc in documents]
    print(f"Length of pairs:{len(pairs)}")

    with torch.no_grad():
        with torch.autocast('cuda'):
            inputs = process_inputs(pairs)
            reranked_scores = compute_logits(inputs)

            # gc.collect()
            # torch.cuda.empty_cache()
    print(f"DEBUG: Reranker scores count = {len(reranked_scores)}")

    top_n_indices= np.argsort(np.array(reranked_scores))[::-1][:top_n]

    top_n_reranked_docs= [documents[i] for i in top_n_indices]
    print(f"Length of top_n_reranked:{len(top_n_reranked_docs)}")

    return (top_n_indices,top_n_reranked_docs)
