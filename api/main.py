
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import logging
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from recommender.engine import SHLRecommender

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# Global recommender instance (loaded at startup)
_recommender: Optional[SHLRecommender] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load the recommender once at startup."""
    global _recommender
    logger.info("Loading SHLRecommender at startup...")
    _recommender = SHLRecommender()
    logger.info("SHLRecommender loaded. API ready.")
    yield
    logger.info("API shutting down.")


app = FastAPI(
    title="SHL Assessment Recommender API",
    description="Recommends SHL Individual Test Solutions for a given job description or query.",
    version="1.0.0",
    lifespan=lifespan,
)
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def serve_frontend():
    return FileResponse("static/index.html")




class RecommendRequest(BaseModel):
    query: str = Field(..., description="Natural language query or job description text.")
    top_n: int = Field(10, ge=1, le=10, description="Max number of recommendations (1–10).")


class AssessmentResult(BaseModel):
    url: str
    name: str
    adaptive_support: str
    description: str
    duration: Optional[int]
    remote_support: str
    test_type: list[str]


class RecommendResponse(BaseModel):
    recommended_assessments: list[AssessmentResult]




@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "ok"}


@app.post("/recommend", response_model=RecommendResponse)
def recommend(request: RecommendRequest):
    """
    Accept a job description or natural language query.
    Return 5–10 most relevant SHL Individual Test Solutions.
    """
    global _recommender

    if _recommender is None:
        raise HTTPException(status_code=503, detail="Recommender not initialized.")

    query = request.query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Query must not be empty.")

    try:
        results = _recommender.recommend(query, top_n=request.top_n)
    except Exception as exc:
        logger.error("Recommendation error: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Recommendation failed: {str(exc)}")

    assessments = [
        AssessmentResult(
            url=r.get("url", ""),
            name=r.get("name", ""),
            adaptive_support=r.get("adaptive_support", "No"),
            description=r.get("description", ""),
            duration=r.get("duration"),
            remote_support=r.get("remote_support", "No"),
            test_type=r.get("test_types", []),
        )
        for r in results
    ]

    return RecommendResponse(recommended_assessments=assessments)
