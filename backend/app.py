#fastapi backend layer

from fastapi import FastAPI
from pydantic import BaseModel
from typing import List

import main

app = FastAPI(title="Reading Path & Academic Graph API")

# Request models

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


# Usecase 1: Reading path pipeline

@app.post("/usecase1/generate-reading-path-pipeline")
def generate_reading_path_pipeline(req: GenReq):
    return main.run_reading_path_pipeline(req.config_path)


@app.post("/usecase1/query-reading-path")
def query_reading_path(req: QueryReq):
    return main.run_reading_path_query(req.query_str, req.config_path)

# Usecase 2: Academic profiles (Pinecone-backed)


@app.post("/usecase2/ingest-academic-interests")
def ingest_academic_interests_pinecone():
    return main.ingest_academic_interests()


@app.post("/usecase2/ingest-professor-profiles")
def ingest_professor_profiles_pinecone():
    return main.ingest_professor_profiles()


@app.post("/usecase2/query-academic-profiles")
def query_academic_profiles(req: ProfilesReq):
    return main.get_academic_profiles(req.interest_id_list)


# Usecase 3: Paper recommendations (Pinecone-backed)


@app.post("/usecase3/paper-recommendations")
def get_paper_recommendations(req: RecReq):
    return main.get_paper_recommendations(req.query, req.top_n)


@app.post("/usecase3/setup-recommendations-pinecone")
def setup_recommendations_pinecone():
    return main.setup_recommendations_index()

# Root


@app.get("/")
def root():
    return {"message": "API running. Open /docs to test."}