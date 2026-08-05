"""
FastAPI Server for PaperTrail Use Cases.
"""

import os
import sys
from typing import Any, List, Dict, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
try:
    import pandas as pd
except ImportError:
    pd = None

try:
    import torch
except ImportError:
    torch = None

try:
    import numpy as np
except ImportError:
    np = None

# Ensure parent directory is in sys.path for module resolution
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import (
    generate_reading_path_pipeline,
    get_reading_path as query_reading_path,
    find_academic_profiles as query_academic_profiles,
    recommend_papers as get_paper_recommendations,
)


def ingest_academic_interests_pinecone():
    from src.usecase_2.embedding.generate_embedding import gen_res_emb_ingestion
    return gen_res_emb_ingestion()


def ingest_professor_profiles_pinecone():
    from src.usecase_2.embedding.generate_embedding_prof import gen_prof_emb_ingestion
    return gen_prof_emb_ingestion()


def setup_recommendations_pinecone():
    from src.usecase_3.Pinecone_setup import create_pc_index, load_dataset, load_data_to_pc
    from src.usecase_3.UC3 import read_paper_embeds
    index = create_pc_index("paper-embeds")
    dataset = load_dataset()
    paper_embeddings = read_paper_embeds()
    return load_data_to_pc(index, 100, dataset, paper_embeddings)

app = FastAPI(
    title="PaperTrail API",
    description="Unified FastAPI server for PaperTrail Use Cases",
    version="1.0.0",
)


def format_response(result: Any) -> Any:
    """
    Format output values according to API rules:
    - None (side-effects only) -> {"status": "success"}
    - pandas.DataFrame -> list of dicts via .to_dict(orient="records")
    - torch.Tensor -> list via .tolist()
    - numpy.ndarray -> list via .tolist()
    - Dict/List -> recursively formatted
    """
    if result is None:
        return {"status": "success"}
    if pd is not None and isinstance(result, pd.DataFrame):
        return result.to_dict(orient="records")
    if torch is not None and isinstance(result, torch.Tensor):
        return result.tolist()
    if np is not None and isinstance(result, np.ndarray):
        return result.tolist()
    if isinstance(result, dict):
        return {k: format_response(v) for k, v in result.items()}
    if isinstance(result, list):
        return [format_response(item) for item in result]
    return result


# ------------------------------------------------------------------------------
# Use Case 1 Pydantic Models & Endpoints
# ------------------------------------------------------------------------------

class GenerateReadingPathPipelineRequest(BaseModel):
    config_path: str = Field(default="config.yaml", description="Path to configuration YAML file")


@app.post("/generate_reading_path_pipeline", tags=["Use Case 1"])
def endpoint_generate_reading_path_pipeline(body: GenerateReadingPathPipelineRequest):
    try:
        result = generate_reading_path_pipeline(config_path=body.config_path)
        return format_response(result)
    except Exception as e:
        raise HTTPException(status_code=501, detail=f"Use Case 1 pipeline error (under active development): {str(e)}")


class QueryReadingPathRequest(BaseModel):
    query: str = Field(..., description="Topic query for generating foundational reading path")
    config_path: str = Field(default="config.yaml", description="Path to configuration YAML file")


@app.post("/query_reading_path", tags=["Use Case 1"])
def endpoint_query_reading_path(body: QueryReadingPathRequest):
    try:
        result = query_reading_path(query=body.query, config_path=body.config_path)
        return format_response(result)
    except Exception as e:
        raise HTTPException(status_code=501, detail=f"Use Case 1 query error (under active development): {str(e)}")


# ------------------------------------------------------------------------------
# Use Case 2 Pydantic Models & Endpoints
# ------------------------------------------------------------------------------

class IngestAcademicInterestsPineconeRequest(BaseModel):
    pass


@app.post("/ingest_academic_interests_pinecone", tags=["Use Case 2"])
def endpoint_ingest_academic_interests_pinecone(body: IngestAcademicInterestsPineconeRequest = IngestAcademicInterestsPineconeRequest()):
    result = ingest_academic_interests_pinecone()
    return format_response(result)


class IngestProfessorProfilesPineconeRequest(BaseModel):
    pass


@app.post("/ingest_professor_profiles_pinecone", tags=["Use Case 2"])
def endpoint_ingest_professor_profiles_pinecone(body: IngestProfessorProfilesPineconeRequest = IngestProfessorProfilesPineconeRequest()):
    result = ingest_professor_profiles_pinecone()
    return format_response(result)


class QueryAcademicProfilesRequest(BaseModel):
    query: str = Field(..., description="Query string for matching academic profiles")
    resume_path: str = Field(..., description="Path to candidate resume PDF file")


@app.post("/query_academic_profiles", tags=["Use Case 2"])
def endpoint_query_academic_profiles(body: QueryAcademicProfilesRequest):
    result = query_academic_profiles(query=body.query, resume_path=body.resume_path)
    return format_response(result)


# ------------------------------------------------------------------------------
# Use Case 3 Pydantic Models & Endpoints
# ------------------------------------------------------------------------------

class GetPaperRecommendationsRequest(BaseModel):
    query: str = Field(..., description="Topic or query string for paper recommendation")
    top_n: int = Field(default=5, description="Number of top paper recommendations to return")


@app.post("/get_paper_recommendations", tags=["Use Case 3"])
def endpoint_get_paper_recommendations(body: GetPaperRecommendationsRequest):
    result = get_paper_recommendations(query=body.query, top_n=body.top_n)
    return format_response(result)


class SetupRecommendationsPineconeRequest(BaseModel):
    pass


@app.post("/setup_recommendations_pinecone", tags=["Use Case 3"])
def endpoint_setup_recommendations_pinecone(body: SetupRecommendationsPineconeRequest = SetupRecommendationsPineconeRequest()):
    result = setup_recommendations_pinecone()
    return format_response(result)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
