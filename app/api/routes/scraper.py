from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

class ScraperConfigSchema(BaseModel):
    keywords: str
    target_categories: str
    target_cities: str
    max_per_day: int
    delay_min_seconds: int
    delay_max_seconds: int

@router.post("/run")
async def run_scraper():
    from app.scraper.runner import ScraperRunner
    runner = ScraperRunner()
    result = await runner.run()
    return result

@router.get("/status")
async def scraper_status():
    from app.core.database import SessionLocal
    from app.models.prospect import ScraperProgress
    from datetime import datetime
    from sqlalchemy import func
    from fastapi.responses import HTMLResponse
    
    db = SessionLocal()
    try:
        today = datetime.utcnow().date()
        progresses = db.query(ScraperProgress).filter(
            func.date(ScraperProgress.scraped_at) == today
        ).all()
        
        total_found = sum(p.total_found for p in progresses)
        total_saved = sum(p.total_saved for p in progresses)
        
        html = f"""
        <div class="space-y-2">
            <p><strong>Total Terkumpul Hari Ini:</strong> {total_found}</p>
            <p><strong>Total Tersimpan:</strong> {total_saved}</p>
            <p class="text-sm text-gray-500 mt-2">Update terakhir: {datetime.now().strftime('%H:%M:%S')}</p>
        </div>
        """
        return HTMLResponse(content=html)
    finally:
        db.close()

@router.get("/config")
async def get_config():
    from app.core.database import SessionLocal
    from app.models.prospect import ScraperConfig
    db = SessionLocal()
    try:
        config = db.query(ScraperConfig).first()
        if not config:
            return {}
        return {
            "keywords": config.keywords,
            "target_categories": config.target_categories,
            "target_cities": config.target_cities,
            "max_per_day": config.max_per_day,
            "delay_min_seconds": config.delay_min_seconds,
            "delay_max_seconds": config.delay_max_seconds,
            "is_active": config.is_active
        }
    finally:
        db.close()

@router.post("/config")
async def save_config(config_data: ScraperConfigSchema):
    from app.core.database import SessionLocal
    from app.models.prospect import ScraperConfig
    db = SessionLocal()
    try:
        config = db.query(ScraperConfig).first()
        if not config:
            config = ScraperConfig()
            db.add(config)
        
        config.keywords = config_data.keywords
        config.target_categories = config_data.target_categories
        config.target_cities = config_data.target_cities
        config.max_per_day = config_data.max_per_day
        config.delay_min_seconds = config_data.delay_min_seconds
        config.delay_max_seconds = config_data.delay_max_seconds
        
        db.commit()
        return {"status": "success"}
    finally:
        db.close()
