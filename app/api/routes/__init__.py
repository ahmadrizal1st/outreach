from fastapi import APIRouter
from . import dashboard, settings, scraper, scoring, prospects, pipeline, review

api_router = APIRouter()
api_router.include_router(dashboard.router, tags=["dashboard"])
api_router.include_router(prospects.router, prefix="/prospects", tags=["prospects"])
api_router.include_router(pipeline.router, prefix="/pipeline", tags=["pipeline"])
api_router.include_router(review.router, prefix="/review", tags=["review"])
api_router.include_router(settings.router, prefix="/settings", tags=["settings"])
api_router.include_router(scraper.router, prefix="/scraper", tags=["scraper"])
api_router.include_router(scoring.router, prefix="/scoring", tags=["scoring"])
