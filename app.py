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
    allow_origins=["https://paper-trail-k7cp.vercel.app/"],
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

@app.post("/usecase1/get-reading-path")
def get_reading_path(req: QueryReq):
    records = main.get_reading_path(req.query_str, req.config_path)
    if not records:
        return {"query": req.query_str, "targetNodeIdx": None, "nodes": [], "edges": []}
    
    # Format for frontend React Flow DAG
    # The frontend expects full nodes: {nodeIdx, title, publishedDate, hopDistance, ...}
    # and edges: {src, dst, similarity, reason}
    nodes = []
    edges = []
    
    # We will synthesize the target node and edges since backend returns a flat list of ancestors.
    # The target node is implied to be hop 0, but query.py doesn't return it directly.
    # We will just map what we have into nodes.
    targetNodeIdx = records[0]["node_idx"] if records else 0

    for r in records:
        nodes.append({
            "nodeIdx": r["node_idx"],
            "title": r["title"],
            "publishedDate": r["published_date"],
            "hopDistance": r.get("hop_distance", 0),
            "abstract": r.get("abstract", ""),
            "arxivId": r.get("arxiv_id", ""),
            "arxivUrl": f"https://arxiv.org/abs/{r.get('arxiv_id', '')}",
            "pdfUrl": f"https://arxiv.org/pdf/{r.get('arxiv_id', '')}.pdf",
            "authors": [] # Neo4j doesn't currently store authors
        })
    
    # Synthesize edges connecting n -> n-1 hop distance
    # Group by hop distance
    hops = {}
    for r in records:
        h = r.get("hop_distance", 0)
        if h not in hops:
            hops[h] = []
        hops[h].append(r["node_idx"])
        
    for h in sorted(hops.keys(), reverse=True):
        if h - 1 in hops:
            # Connect all nodes at hop h to all nodes at hop h-1
            for src in hops[h]:
                for dst in hops[h-1]:
                    edges.append({
                        "src": src,
                        "dst": dst,
                        "similarity": 0.8,
                        "reason": "prerequisite"
                    })

    return {
        "query": req.query_str,
        "targetNodeIdx": targetNodeIdx,
        "nodes": nodes,
        "edges": edges
    }

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
