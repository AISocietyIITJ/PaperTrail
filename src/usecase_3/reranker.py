import torch
from transformers import AutoModel, AutoTokenizer, AutoModelForCausalLM,AutoModelForSequenceClassification
import numpy as np
import gc

# tokenizer = AutoTokenizer.from_pretrained("cross-encoder/ms-marco-MiniLM-L-6-v2")
# model = AutoModelForSequenceClassification.from_pretrained("cross-encoder/ms-marco-MiniLM-L-6-v2").to('cuda')

# tokenizer = AutoTokenizer.from_pretrained("BAAI/bge-reranker-large")
# model = AutoModelForSequenceClassification.from_pretrained("BAAI/bge-reranker-large").to('cuda')

tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen3-Reranker-0.6B", padding_side='left',trust_remote_code=True)
model = AutoModelForCausalLM.from_pretrained("Qwen/Qwen3-Reranker-0.6B", torch_dtype= torch.bfloat16,trust_remote_code=True).to('cuda')
# tokenizer = AutoTokenizer.from_pretrained('jinaai/jina-reranker-v2-base-multilingual', trust_remote_code=True)
# model = AutoModelForSequenceClassification.from_pretrained(
#     'jinaai/jina-reranker-v2-base-multilingual',
#     torch_dtype="auto",
#     trust_remote_code=True,
# ).to('cuda')

# from sentence_transformers import CrossEncoder

# model = CrossEncoder(
#     "jinaai/jina-reranker-v2-base-multilingual",
#     automodel_args={"torch_dtype": "auto"},
#     trust_remote_code=True,
# )

model.eval()

token_false_id = tokenizer.convert_tokens_to_ids("no")
token_true_id = tokenizer.convert_tokens_to_ids("yes")
max_length = 512

prefix = "<|im_start|>system\nJudge whether the Document meets the requirements based on the Query and the Instruct provided. Note that the answer can only be \"yes\" or \"no\".<|im_end|>\n<|im_start|>user\n"
suffix = "<|im_end|>\n<|im_start|>assistant\n<think>\n\n</think>\n\n"
prefix_tokens = tokenizer.encode(prefix, add_special_tokens=False)
suffix_tokens = tokenizer.encode(suffix, add_special_tokens=False)

def format_instruction(query, doc,instruction= 'Given a web search query, retrieve relevant passages that answer the query'):
    output = f"<Instruct>: {instruction}\n<Query>: {query}\n<Document>: {doc}"
    return output

def process_inputs(pairs):
    # if not pairs:
    #     raise ValueError(
    #         "process_inputs received an empty list of pairs! Ensure candidate"
    #         " documents are not empty."
    #     )
    formatted_pairs = [f"{prefix}{p}{suffix}" for p in pairs]
    inputs = tokenizer(
        formatted_pairs, padding=True, truncation=True,
        max_length=384,return_tensors="pt"
    )

    for key in inputs:
        inputs[key] = inputs[key].to(model.device)
    return inputs

@torch.no_grad()
def compute_logits(inputs,batch_size2=8,**kwargs,):
    scores_list=[]
    num_samples = inputs['input_ids'].shape[0]
    for i in range(0,num_samples,batch_size2):
        batch_inputs = {
            k: v[i : i + batch_size2]
            for k, v in inputs.items()
        }
        outputs= model(**batch_inputs)
        # batch_scores = model(**inputs).logits
        # batch_scores=batch_scores[:,0]
        if "attention_mask" in batch_inputs:
            # Get index of the last non-padded token for each sample in batch
            sequence_lengths = batch_inputs["attention_mask"].sum(dim=1) - 1
            batch_indices = torch.arange(batch_inputs["input_ids"].shape[0], device=model.device)
            batch_scores = outputs.logits[batch_indices, sequence_lengths, :]
        else:
            # Fallback if no padding was applied
            batch_scores = outputs.logits[:, -1, :]

        true_vector = batch_scores[:, token_true_id]
        false_vector = batch_scores[:, token_false_id]

        batch_scores = torch.stack([false_vector, true_vector], dim=1)
        batch_scores = torch.nn.functional.log_softmax(batch_scores, dim=1)

        scores = batch_scores[:, 1].exp().tolist()
        scores_list.extend(scores)
    # batch_scores_sigmoid=torch.sigmoid(batch_scores)
    # scores = batch_scores_sigmoid.squeeze(-1)
    # print(scores.shape)
    # scores=scores.tolist()    

    return scores_list

    # return scores if isinstance(scores,list) else [scores]  


def return_reranked_docs(query, documents,top_n=5,batch_size=8): 
    print(f"DEBUG: Query='{query[:30]}...' | Documents Count={len(documents)}")     
    if not documents:
        print(
            f"[WARNING] Skipping query '{query[:30]}...' because candidate list is"
            " empty."
        )
        return ([], [], [])
    
    task = 'Given a web search query, retrieve relevant passages that answer the query'

    pairs = [format_instruction(query, doc, task) for doc in documents]
    print(f"Length of pairs:{len(pairs)}")

    reranked_scores_fin=[]

    with torch.no_grad():
        with torch.autocast('cuda'):
            for i in range(0,len(documents),batch_size):
                batch_pairs=pairs[i:i+ batch_size]
                # batch_docs=documents[i:i+ batch_size]
                if not batch_pairs:
                    continue

                batch_inputs = process_inputs(batch_pairs)
                # batch_inputs= process_inputs(batch_docs)
                batch_reranked_scores = compute_logits(batch_inputs)

                reranked_scores_fin.extend(batch_reranked_scores)

                del batch_inputs,batch_reranked_scores

    # gc.collect()
    # torch.cuda.empty_cache()
    top_n_indices= np.argsort(np.array(reranked_scores_fin))[::-1][:top_n].tolist()


    top_n_reranked_scores = [reranked_scores_fin[i] for i in top_n_indices]


    print(f"DEBUG: Reranker scores count = {len(reranked_scores_fin)}")


    top_n_reranked_docs= [documents[i] for i in top_n_indices]
    print(f"Length of top_n_reranked:{len(top_n_reranked_docs)}")   

    return (top_n_indices,top_n_reranked_docs,top_n_reranked_scores)
