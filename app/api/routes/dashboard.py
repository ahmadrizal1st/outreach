from app.followup.notifier import FollowupNotifier
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date

from app.core.database import get_db
from app.core.dependencies import templates
from app.models.prospect import Prospect, ProspectScore, Pipeline
from app.models.settings import LLMProvider

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def read_dashboard(request: Request, db: Session = Depends(get_db)):
    
    total_prospects = db.query(Prospect).count()
    hot = db.query(ProspectScore).filter(ProspectScore.priority_tier == 'HOT').count()
    warm = db.query(ProspectScore).filter(ProspectScore.priority_tier == 'WARM').count()

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

    notifier = FollowupNotifier()
    summary = notifier.get_summary()

    providers = db.query(LLMProvider).all()

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
