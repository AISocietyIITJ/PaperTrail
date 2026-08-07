
# this is only core logic . app.py will import these functions 

import random
from typing import List, Dict, Any

# Usecase 1: Reading path pipeline

def run_reading_path_pipeline(config_path: str = "config.yaml") -> Dict[str, Any]:
   
    return {"status": "pipeline executed", "config_path": config_path}


def run_reading_path_query(query_str: str, config_path: str = "config.yaml") -> List[Dict[str, Any]]:
   
    return [
        {
            "hop_distance": i,
            "title": f"{query_str} paper {i}",
            "published_date": f"202{i}-01-01",
        }
        for i in range(3)
    ]


# Usecase 2: Academic profiles (Pinecone-backed)


def ingest_academic_interests() -> Dict[str, str]:
    
    return {"status": "success"}


def ingest_professor_profiles() -> Dict[str, str]:
    
    return {"status": "success"}


def get_academic_profiles(interest_id_list: List[str]) -> List[Dict[str, Any]]:
    
    return [
        {
            "name": f"Prof for {interest_id}",
            "h_index": random.randint(10, 60),
            "citations": random.randint(500, 20000),
        }
        for interest_id in interest_id_list
    ]

# Usecase 3: Paper recommendations (Pinecone-backed)

def get_paper_recommendations(query: str, top_n: int = 5) -> List[Dict[str, Any]]:

    return [
        {
            "paper_id": f"paper_{i}",
            "title": f"{query} result {i}",
            "score": round(random.uniform(0.7, 0.99), 3),
        }
        for i in range(1, top_n + 1)
    ]


def setup_recommendations_index() -> Dict[str, str]:
    return {"status": "success"}  