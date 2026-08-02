from src.embedding.generate_alias import generate_phrase
from src.embedding.generate_embedding import gen_res_emb_ingestion
from src.embedding.generate_embedding_prof import gen_prof_emb_ingestion

from src.ingestion.load_reaseach_node import ingest_research_node
from src.ingestion.load_proffesor import ingest_proff_connect_edges

print("\n" + "=" * 60)
print("PaperTrail Setup")
print("=" * 60)

print("\n[1/5] Generating phrase aliases...")
generate_phrase()

print("[2/5] Generating research embeddings...")
gen_res_emb_ingestion()

print("[3/5] Generating professor embeddings...")
gen_prof_emb_ingestion()


print("[4/5] Ingesting research nodes...")
ingest_research_node()

print("[5/5] Ingesting professor connections...")
ingest_proff_connect_edges()

print("\nSetup complete.")
