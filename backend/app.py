from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
import random

app = FastAPI(title="Reading Path & Academic Graph API")


class GenReq(BaseModel):
    config_path: str = "config.yaml"


class QueryReq(BaseModel):
    query_str: str
    config_path: str = "config.yaml"


class ProfilesReq(BaseModel):
    interest_id_list: List[str]


class RecReq(BaseModel):
    query: str
    top_n: int = 5


@app.post("/usecase1/generate-reading-path-pipeline")
def generate_reading_path_pipeline(req: GenReq):
    return {"status": "pipeline executed", "config_path": req.config_path}


@app.post("/usecase1/query-reading-path")
def query_reading_path(req: QueryReq):
    return [
        {"hop_distance": i, "title": f"{req.query_str} paper {i}", "published_date": f"202{i}-01-01"}
        for i in range(3)
    ]


@app.post("/usecase2/ingest-academic-interests")
def ingest_academic_interests_pinecone():
    return {"status": "success"}


@app.post("/usecase2/ingest-professor-profiles")
def ingest_professor_profiles_pinecone():
    return {"status": "success"}


@app.post("/usecase2/query-academic-profiles")
def query_academic_profiles(req: ProfilesReq):
    return [
        {"name": f"Prof for {i}", "h_index": random.randint(10, 60), "citations": random.randint(500, 20000)}
        for i in req.interest_id_list
    ]


@app.post("/usecase3/paper-recommendations")
def get_paper_recommendations(req: RecReq):
    return [
        {"paper_id": f"paper_{i}", "title": f"{req.query} result {i}", "score": round(random.uniform(0.7, 0.99), 3)}
        for i in range(1, req.top_n + 1)
    ]


@app.post("/usecase3/setup-recommendations-pinecone")
def setup_recommendations_pinecone():
    return {"status": "success"}


@app.get("/")
def root():
    return {"message": "API running. Open /docs to test."}
