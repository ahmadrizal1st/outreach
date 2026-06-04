from fastapi import APIRouter
from . import dashboard, settings, scraper

api_router = APIRouter()
api_router.include_router(dashboard.router, tags=["dashboard"])
api_router.include_router(settings.router, prefix="/settings", tags=["settings"])
api_router.include_router(scraper.router, prefix="/scraper", tags=["scraper"])
