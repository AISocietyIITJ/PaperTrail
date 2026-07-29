from src.local_llm.extractor import get_interest_topics
from src.utils.vec_query_search import search_vector_db
from src.utils.get_prof_info import query_graph_db

print("\n" + "=" * 60)
print("PaperTrail Discovery Console")
print("=" * 60)

user_query = input("\nEnter your query regarding your DC: ")

print("\n[1/3] Extracting interest topics...")
extracted_info = get_interest_topics(user_query)

if extracted_info == None:
    print("Sorry! But I can't able to find your interest field. Could you please tell more about your interest field :)")

else:
    print("[2/3] Searching matching research vectors...")
    vector_ids = search_vector_db(extracted_info)

    print("[3/3] Querying professor graph connections...")
    query_graph_db(vector_ids)

    print("\nDone.")
