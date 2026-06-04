"""
Settings route — renders full settings page with all configurations.
"""
import logging
from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import templates
from app.models.settings import LLMProvider, ScraperConfig, AppSetting

logger = logging.getLogger(__name__)
router = APIRouter()


def _get_settings_dict(db: Session) -> dict:
    """Load all app settings into a flat key-value dict."""
    rows = db.query(AppSetting).all()
    return {r.key: r.value for r in rows}

def _save_setting(db: Session, key: str, value: str, description: str = ""):
    row = db.query(AppSetting).filter(AppSetting.key == key).first()
    if row:
        row.value = value
    else:
        row = AppSetting(key=key, value=value, description=description)
        db.add(row)

@router.get("/", response_class=HTMLResponse)
async def read_settings(request: Request, db: Session = Depends(get_db)):
    settings = _get_settings_dict(db)
    providers = db.query(LLMProvider).order_by(LLMProvider.priority_order).all()
    scraper_config = db.query(ScraperConfig).first()

    from app.api.routes.llm_providers import _provider_to_dict
    return templates.TemplateResponse(
        request=request,
        name="settings.html",
        context={
            "request": request,
            "title": "Settings",
            "settings": settings,
            "providers": [_provider_to_dict(p) for p in providers],
            "scraper_config": scraper_config,
        },
    )

@router.post("/profile", response_class=HTMLResponse)
async def save_profile(
    request: Request,
    agency_name: str = Form(""),
    contact_name: str = Form(""),
    portfolio_url: str = Form(""),
    services_offered: str = Form(""),
    price_range: str = Form(""),
    db: Session = Depends(get_db),
):
    mapping = {
        "agency_name": agency_name,
        "contact_name": contact_name,
        "portfolio_url": portfolio_url,
        "services_offered": services_offered,
        "price_range": price_range,
    }
    for k, v in mapping.items():
        _save_setting(db, k, v)
    db.commit()
    logger.info("Saved profile settings")
    return HTMLResponse("")

@router.post("/scraper", response_class=HTMLResponse)
async def save_scraper_config(
    request: Request,
    keywords: str = Form(""),
    target_cities: str = Form(""),
    max_per_day: int = Form(20),
    delay_min_seconds: int = Form(3),
    delay_max_seconds: int = Form(7),
    db: Session = Depends(get_db),
):
    config = db.query(ScraperConfig).first()
    if not config:
        config = ScraperConfig()
        db.add(config)

    config.keywords = keywords
    config.target_cities = target_cities
    config.max_per_day = max_per_day
    config.delay_min_seconds = delay_min_seconds
    config.delay_max_seconds = delay_max_seconds
    db.commit()
    logger.info("Saved scraper config from settings")
    return HTMLResponse("")

@router.post("/followup", response_class=HTMLResponse)
async def save_followup_config(
    request: Request,
    followup_interval_days: int = Form(3),
    max_followup: int = Form(2),
    db: Session = Depends(get_db),
):
    _save_setting(db, "followup_interval_days", str(followup_interval_days), "Days between follow-ups")
    _save_setting(db, "max_followup", str(max_followup), "Max follow-up attempts before marking COLD")
    db.commit()
    logger.info("Saved follow-up config")
    return HTMLResponse("")

@router.post("/llm-mode", response_class=HTMLResponse)
async def save_llm_mode(
    request: Request,
    llm_mode: str = Form("auto"),
    manual_provider_id: str = Form(""),
    db: Session = Depends(get_db),
):
    _save_setting(db, "llm_mode", llm_mode, "LLM selection mode: auto / manual")
    _save_setting(db, "manual_provider_id", manual_provider_id, "ID of the manually selected provider")
    db.commit()
    logger.info(f"Saved LLM mode: {llm_mode}")
    return HTMLResponse("")
