"""
Scraper route — provides start/stop/progress endpoints and the scraper page.
"""
import asyncio
import logging
from datetime import datetime
from fastapi import APIRouter, Request, Depends, Form, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import templates
from app.models.prospect import Prospect
from app.models.settings import ScraperConfig, ScraperProgress

logger = logging.getLogger(__name__)
router = APIRouter()


scraper_state = {
    "running": False,
    "should_stop": False,
    "started_at": None,
    "keyword": "",
    "city": "",
    "found": 0,
    "saved": 0,
    "total_target": 0,
    "log": [],
    "error": None,
}

def _log(msg: str):
    """Append a timestamped log message."""
    ts = datetime.now().strftime("%H:%M:%S")
    scraper_state["log"].append(f"[{ts}] {msg}")
    if len(scraper_state["log"]) > 100:
        scraper_state["log"] = scraper_state["log"][-100:]
    logger.info(msg)

async def _run_scraping(
    keywords: list[str],
    cities: list[str],
    max_per_day: int,
    db_url: str,
):
    """Background task: runs the scraper for each keyword × city pair."""
    from app.scraper.runner import ScraperRunner
    from app.core.database import SessionLocal

    scraper_state["running"] = True
    scraper_state["should_stop"] = False
    scraper_state["started_at"] = datetime.now().isoformat()
    scraper_state["found"] = 0
    scraper_state["saved"] = 0
    scraper_state["log"] = []
    scraper_state["error"] = None
    scraper_state["total_target"] = max_per_day

    _log(f"Scraping dimulai — {len(keywords)} keyword × {len(cities)} kota")

    db = SessionLocal()
    try:
        runner = ScraperRunner(db)
        for city in cities:
            for keyword in keywords:
                if scraper_state["should_stop"]:
                    _log("⛔ Scraping dihentikan oleh user.")
                    break

                scraper_state["keyword"] = keyword
                scraper_state["city"] = city
                _log(f"🔍 Mencari: {keyword} di {city}...")

                try:
                    result = await runner.run_single(
                        keyword=keyword,
                        city=city,
                        max_results=max_per_day,
                        stop_flag=scraper_state,
                    )
                    scraper_state["found"] += result.get("found", 0)
                    scraper_state["saved"] += result.get("saved", 0)
                    _log(
                        f"✅ {keyword} @ {city}: ditemukan {result.get('found', 0)}, "
                        f"disimpan {result.get('saved', 0)}"
                    )
                except Exception as e:
                    _log(f"❌ Error {keyword} @ {city}: {str(e)}")

            if scraper_state["should_stop"]:
                break

        _log(f"🏁 Selesai — Total ditemukan: {scraper_state['found']}, disimpan: {scraper_state['saved']}")
    except Exception as e:
        scraper_state["error"] = str(e)
        _log(f"❌ Fatal error: {e}")
    finally:
        db.close()
        scraper_state["running"] = False
        scraper_state["should_stop"] = False

@router.get("/", response_class=HTMLResponse)
async def scraper_page(request: Request, db: Session = Depends(get_db)):
    config = db.query(ScraperConfig).first()
    today_count = db.query(Prospect).filter(
        Prospect.created_at >= datetime.now().date()
    ).count() if hasattr(Prospect, 'created_at') else 0

    history = db.query(ScraperProgress).order_by(
        ScraperProgress.scraped_at.desc()
    ).limit(10).all()

    return templates.TemplateResponse(
        request=request,
        name="scraper/index.html",
        context={
            "request": request,
            "title": "Scraper",
            "config": config,
            "today_count": today_count,
            "history": history,
            "state": scraper_state,
        },
    )

@router.post("/start", response_class=HTMLResponse)
async def start_scraper(
    request: Request,
    background_tasks: BackgroundTasks,
    keywords: str = Form(...),
    cities: str = Form(...),
    max_per_day: int = Form(20),
    db: Session = Depends(get_db),
):
    if scraper_state["running"]:
        return HTMLResponse(
            '<div class="text-yellow-600 p-3 bg-yellow-50 rounded-lg text-sm">'
            '<i class="fa-solid fa-triangle-exclamation"></i> Scraper sedang berjalan.</div>'
        )

    keyword_list = [k.strip() for k in keywords.split(",") if k.strip()]
    city_list = [c.strip() for c in cities.split(",") if c.strip()]

    if not keyword_list or not city_list:
        return HTMLResponse(
            '<div class="text-red-600 p-3 bg-red-50 rounded-lg text-sm">'
            '<i class="fa-solid fa-xmark-circle"></i> Keyword dan kota tidak boleh kosong.</div>'
        )

    config = db.query(ScraperConfig).first()
    if not config:
        config = ScraperConfig()
        db.add(config)
    config.keywords = keywords
    config.target_cities = cities
    config.max_per_day = max_per_day
    db.commit()

    from app.core.config import settings as app_settings
    background_tasks.add_task(
        _run_scraping,
        keywords=keyword_list,
        cities=city_list,
        max_per_day=max_per_day,
        db_url=str(app_settings.DATABASE_URL),
    )

    return templates.TemplateResponse(
        request=request,
        name="scraper/progress.html",
        context={"request": request, "state": scraper_state},
    )

@router.post("/stop")
async def stop_scraper():
    if scraper_state["running"]:
        scraper_state["should_stop"] = True
        return {"status": "stop_requested"}
    return {"status": "not_running"}

@router.get("/progress", response_class=HTMLResponse)
async def get_progress(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="scraper/progress.html",
        context={"request": request, "state": scraper_state},
    )

@router.get("/status")
async def get_status():
    return JSONResponse(scraper_state)

@router.post("/run", response_class=HTMLResponse)
async def run_scraper_quick(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Quick-run from dashboard using saved config."""
    if scraper_state["running"]:
        return HTMLResponse(
            '<div class="text-xs text-yellow-600">Scraper sedang berjalan...</div>'
        )

    config = db.query(ScraperConfig).first()
    if not config or not config.keywords or not config.target_cities:
        return HTMLResponse(
            '<div class="text-xs text-red-500">Config belum diisi. <a href="/scraper" class="underline">Setup scraper</a></div>'
        )

    keyword_list = [k.strip() for k in config.keywords.split(",") if k.strip()]
    city_list = [c.strip() for c in config.target_cities.split(",") if c.strip()]

    from app.core.config import settings as app_settings
    background_tasks.add_task(
        _run_scraping,
        keywords=keyword_list,
        cities=city_list,
        max_per_day=config.max_per_day or 20,
        db_url=str(app_settings.DATABASE_URL),
    )

    return HTMLResponse(
        '<div class="text-xs text-green-600"><i class="fa-solid fa-check"></i> Scraper dimulai! '
        '<a href="/scraper" class="underline">Lihat progress</a></div>'
    )
