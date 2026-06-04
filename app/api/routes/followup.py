from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
import os

from app.core.database import get_db
from app.followup.tracker import FollowupTracker
from app.followup.notifier import FollowupNotifier

router = APIRouter()
templates_dir = os.path.join(os.path.dirname(__file__), "..", "..", "templates")
templates = Jinja2Templates(directory=templates_dir)

@router.get("/today", response_class=HTMLResponse)
async def get_followups_today(request: Request, db: Session = Depends(get_db)):
    tracker = FollowupTracker()
    followups = tracker.get_followups_today()
    return templates.TemplateResponse(request=request, name="followup/list.html", context={"request": request, "followups": followups})

@router.post("/api/check")
async def run_followup_check(db: Session = Depends(get_db)):
    tracker = FollowupTracker()
    result = tracker.check_and_flag()
    return JSONResponse(content=result)

@router.post("/api/sent/{prospect_id}")
async def mark_followup_sent(request: Request, prospect_id: int, db: Session = Depends(get_db)):
    tracker = FollowupTracker()
    tracker.mark_followup_sent(prospect_id)

    from app.models.prospect import Prospect, Pipeline, ProspectScore
    result = db.query(Prospect, Pipeline, ProspectScore).join(
        Pipeline, Prospect.id == Pipeline.prospect_id
    ).join(
        ProspectScore, Prospect.id == ProspectScore.prospect_id
    ).filter(Prospect.id == prospect_id).first()
    
    if result:
        p, pl, ps = result
        prospect_data = {
            "id": p.id,
            "name": p.name,
            "category": p.category,
            "city": p.city,
            "followup_count": pl.followup_count or 0,
            "priority_tier": ps.priority_tier,
            "priority_score": ps.priority_score,
            "pitch_angle": ps.pitch_angle
        }
        return templates.TemplateResponse(request=request, name="followup/card.html", context={"request": request, "prospect": prospect_data})
    return HTMLResponse("Updated")

@router.post("/api/cold/{prospect_id}")
async def manual_mark_cold(request: Request, prospect_id: int, db: Session = Depends(get_db)):
    tracker = FollowupTracker()
    tracker._mark_cold(prospect_id)
    return HTMLResponse("")

@router.get("/api/summary")
async def followup_summary(db: Session = Depends(get_db)):
    notifier = FollowupNotifier()
    return JSONResponse(content=notifier.get_summary())
