#fastapi backend layer

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pathlib import Path
from typing import List, Optional
from uuid import uuid4

import main

app = FastAPI(title="Reading Path & Academic Graph API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://paper-trail-k7cp.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    resume_path: Optional[str] = None
    resume_text: Optional[str] = None


# Usecase 1: Reading path pipeline

@app.post("/api/structured-path")
def api_structured_path(req: QueryReq):
    result = generate_structured_path(req.query_str)
    return {"query": req.query_str, "path": result or []}

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
async def find_academic_profiles(
    query: str = Form(...),
    resume: UploadFile | None = File(default=None),
):
    resume_path = None
    data_dir = Path(__file__).resolve().parent / "data"

    if resume is not None:
        if resume.content_type != "application/pdf":
            raise HTTPException(status_code=415, detail="Only PDF resumes are supported")

        data_dir.mkdir(exist_ok=True)
        resume_path = data_dir / f"resume-{uuid4().hex}.pdf"
        try:
            with resume_path.open("wb") as destination:
                while chunk := await resume.read(1024 * 1024):
                    destination.write(chunk)

            return main.find_academic_profiles(
                query=query,
                resume_path=str(resume_path),
            )
        finally:
            resume_path.unlink(missing_ok=True)
            await resume.close()

    return main.find_academic_profiles(query=query)

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
