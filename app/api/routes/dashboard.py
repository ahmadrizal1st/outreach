from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date
import os

from app.core.database import get_db
from app.models.prospect import Prospect, ProspectScore, LLMProvider, Pipeline

router = APIRouter()

# Setup templates
templates_dir = os.path.join(os.path.dirname(__file__), "..", "..", "templates")
templates = Jinja2Templates(directory=templates_dir)

@router.get("/", response_class=HTMLResponse)
async def read_dashboard(request: Request, db: Session = Depends(get_db)):
    # Calculate stats
    total_prospects = db.query(Prospect).count()
    hot = db.query(ProspectScore).filter(ProspectScore.priority_tier == 'HOT').count()
    warm = db.query(ProspectScore).filter(ProspectScore.priority_tier == 'WARM').count()
    
    # Calculate contacted today
    today = date.today()
    contacted_today = db.query(Pipeline).filter(
        func.date(Pipeline.contacted_at) == today
    ).count()

    stats = {
        "total": total_prospects,
        "hot": hot,
        "warm": warm,
        "contacted_today": contacted_today
    }

    # Top 10 logic
    # Find prospects not blacklisted, not contacted (contact_status = 'belum_dihubungi' or no pipeline entry)
    # Order by priority_score DESC, review_count DESC
    # Ensure they have a phone number (normalized)
    
    # SQL equivalent logic
    top10_query = (
        db.query(Prospect, ProspectScore, Pipeline)
        .join(ProspectScore, Prospect.id == ProspectScore.prospect_id)
        .outerjoin(Pipeline, Prospect.id == Pipeline.prospect_id)
        .filter(
            (Pipeline.is_blacklisted == False) | (Pipeline.id == None),
            (Pipeline.contact_status == 'belum_dihubungi') | (Pipeline.id == None),
            Prospect.phone_normalized != None,
            Prospect.phone_normalized != ""
        )
        .order_by(
            ProspectScore.priority_score.desc(),
            Prospect.review_count.desc()
        )
        .limit(10)
        .all()
    )

    top10 = []
    for prospect, score, pipeline in top10_query:
        # Build dict for template
        top10.append({
            "id": prospect.id,
            "name": prospect.name,
            "category": prospect.category,
            "city": prospect.city,
            "rating": prospect.rating,
            "review_count": prospect.review_count,
            "website": prospect.website,
            "phone_normalized": prospect.phone_normalized,
            "priority_tier": score.priority_tier,
            "priority_score": score.priority_score,
            "pitch_angle": score.pitch_angle
        })

    # Follow-ups summary using Phase 7 logic
    from app.followup.notifier import FollowupNotifier
    notifier = FollowupNotifier()
    summary = notifier.get_summary()

    # Providers status
    providers = db.query(LLMProvider).all()

    # Scraper status mock
    scraper = {
        "today": 0,
        "max": 20
    }

    context = {
        "request": request,
        "stats": stats,
        "top10": top10,
        "summary": summary,
        "providers": providers,
        "scraper": scraper,
        "contacted_today": contacted_today
    }
    
    return templates.TemplateResponse(request=request, name="dashboard.html", context=context)
