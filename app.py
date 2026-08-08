#fastapi backend layer

from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional

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

class AcademicProfilesRequest(BaseModel):
    query: str
    # A path only exists on the API server, so clients should not have to send
    # one just to use this endpoint.  They can provide either server-side path
    # or the already extracted resume text.
    resume_path: Optional[str] = None
    resume_text: Optional[str] = None


# Usecase 1: Reading path pipeline

#@app.post("/usecase1/generate-reading-path-pipeline")
#def generate_reading_path_pipeline(req: GenReq):
 #   return main.generate_reading_path_pipeline(req.config_path)


@app.post("/usecase1/get-reading-path")
def get_reading_path(req: QueryReq):
    return main.get_reading_path(req.query_str, req.config_path)

# Usecase 2: Academic profiles (Pinecone-backed)


#@app.post("/usecase2/ingest-academic-interests")
#def ingest_academic_interests_pinecone():
 #   return main.ingest_academic_interests()


#@app.post("/usecase2/ingest-professor-profiles")
#def ingest_professor_profiles_pinecone():
 #   return main.ingest_professor_profiles()


#@app.post("/usecase2/setup-academic-profiles-pipeline")
#def setup_academic_profiles_pipeline(req: ProfilesReq):
 #   return main.setup_academic_profiles_pipeline(req.interest_id_list)

@app.post("/usecase2/find-academic-profiles")
def find_academic_profiles(req: AcademicProfilesRequest):
    return main.find_academic_profiles(
        query=req.query,
        resume_path=req.resume_path,
        resume_text=req.resume_text,
    )

# Usecase 3: Paper recommendations (Pinecone-backed)


@app.post("/usecase3/recommend_papers")
def recommend_papers(req: RecReq):
    return main.recommend_papers(req.query, req.top_n)


#@app.post("/usecase3/setup-recommendations-pinecone")
#def setup_recommendations_pinecone():
 #   return main.setup_recommendations_index()

# Root


@app.get("/")
def root():
    return {"message": "API running. Open /docs to test."}
