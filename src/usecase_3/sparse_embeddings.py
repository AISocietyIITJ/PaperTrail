from pinecone import Pinecone
from pinecone_text.sparse import BM25Encoder
from src.config import PINECONE_API_KEY
from src.usecase_3.document_setter import concatenate_title_abstract
from tqdm import tqdm

bm25_encoder = BM25Encoder()
bm25_encoder.load("academic_bm25_params.json")

pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index("papertrail-papers-2000")
NAMESPACE = "__default__"

print("=== STARTING FULL SPARSE VECTOR RE-INDEXING ===")

print("Fetching all vector IDs from namespace '__default__'...")
query_res = index.query(
    vector=[0.0] * 768,
    top_k=10000, 
    include_metadata=False,
    namespace=NAMESPACE
)

all_vector_ids = [m.id for m in query_res.matches]
print(f"✅ Retrived {len(all_vector_ids)} vector IDs.")

BATCH_SIZE = 100
success_count = 0

for i in tqdm(range(0, len(all_vector_ids), BATCH_SIZE), desc="Updating Sparse Payloads"):
    batch_ids = all_vector_ids[i : i + BATCH_SIZE]
    fetched = index.fetch(ids=batch_ids, namespace=NAMESPACE)

    for vec_id, record in fetched.vectors.items():
        if not record.metadata:
            continue
            
        text_output = concatenate_title_abstract(record.metadata)
        
        if isinstance(text_output, (list, tuple)) and len(text_output) > 1:
            doc_text = str(text_output[1]).strip()
        elif isinstance(text_output, str):
            doc_text = text_output.strip()
        else:
            doc_text = ""

        if doc_text:

            sparse_vec = bm25_encoder.encode_documents(doc_text)
            
            index.update(
                id=vec_id,
                sparse_values=sparse_vec,
                namespace=NAMESPACE
            )
            success_count += 1