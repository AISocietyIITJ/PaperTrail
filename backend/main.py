from fastapi import FastAPI
from pydantic import BaseModel
from typing import List

app = FastAPI(title="PaperTrail Backend Demo")

# requesting models 

class ReadingPathRequest(BaseModel):
    query: str


class ProfessorRequest(BaseModel):
    interest_topics: List[str]
                                                                                                                                                                                                                                                            

class PaperRecommendationRequest(BaseModel):
    query: str
    top_n: int = 5 #if user doesn't specify any value top 5 papers will be recommended


# Use Case 1
# Reading Path Generation


@app.post("/usecase1/reading-path")
def reading_path(request: ReadingPathRequest):

    return {
        "query": request.query,
        "reading_path": [
            {
                "hop_distance": 0,
                "title": "Linear Algebra",
                "published_date": "2018"
            },
            {
                "hop_distance": 1,
                "title": "Machine Learning Basics",
                "published_date": "2020"
            },
            {
                "hop_distance": 2,
                "title": "Deep Learning",
                "published_date": "2022"
            },
            {
                "hop_distance": 3,
                "title": "Vision Transformers",
                "published_date": "2024"
            }
        ]
    }



# Use Case 2
# Professor Recommendation


@app.post("/usecase2/professors")
def professor_recommendation(request: ProfessorRequest):

    return {
        "interest_topics": request.interest_topics,
        "professors": [
            {
                "name": "Dr. A",
                "department": "Computer Science",
                "h_index": 42,
                "citations": 6100,
                "matching_topics": ["Computer Vision", "Deep Learning"]
            },
            {
                "name": "Dr. B",
                "department": "AI Research",
                "h_index": 36,
                "citations": 4100,
                "matching_topics": ["Image Recognition"]
            }
        ]
    }



# Use Case 3
# Paper Recommendation


@app.post("/usecase3/papers")
def paper_recommendation(request: PaperRecommendationRequest):

    papers = [
        {
            "title": "Attention is All You Need",
            "authors": ["Ashish Vaswani"],
            "year": 2017,
            "similarity_score": 0.96
        },
        {
            "title": "Vision Transformer",
            "authors": ["Dosovitskiy"],
            "year": 2021,
            "similarity_score": 0.94
        },
        {
            "title": "CLIP",
            "authors": ["OpenAI"],
            "year": 2021,
            "similarity_score": 0.92
        },
        {
            "title": "ResNet",
            "authors": ["Kaiming He"],
            "year": 2016,
            "similarity_score": 0.90
        },
        {
            "title": "Swin Transformer",
            "authors": ["Microsoft"],
            "year": 2021,
            "similarity_score": 0.89
        }
    ]

    return {
        "query": request.query,
        "recommendations": papers[:request.top_n]
    }


# Home Route


@app.get("/")
def home():
    return {
        "message": "PaperTrail Hardcoded Backend Running",
        "available_routes": [
            "/usecase1/reading-path",
            "/usecase2/professors",
            "/usecase3/papers"
        ]
    }

#this endpoint function currently returns hardcoded data    