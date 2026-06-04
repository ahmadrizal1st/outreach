from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from datetime import datetime
import os

from app.core.database import get_db
from app.models.prospect import ProspectScore, WebsiteReview
from app.scraper.website_analyzer import WebsiteAnalyzer

router = APIRouter()

templates_dir = os.path.join(os.path.dirname(__file__), "..", "..", "templates")
templates = Jinja2Templates(directory=templates_dir)

@router.post("/{prospect_id}", response_class=HTMLResponse)
async def scan_website(
    request: Request,
    prospect_id: int,
    provider: str = None,
    db: Session = Depends(get_db)
):
    analyzer = WebsiteAnalyzer(db=db, manual_provider=provider)
    result = await analyzer.analyze(prospect_id)

    review = db.query(WebsiteReview).filter(WebsiteReview.prospect_id == prospect_id).first()
    
    return templates.TemplateResponse(request=request, name="review/result.html", context={"request": request, "review": review, "prospect_id": prospect_id, "scan_result": result})

@router.post("/all")
async def scan_all_unreviewed(provider: str = None, db: Session = Depends(get_db)):
    analyzer = WebsiteAnalyzer(db=db, manual_provider=provider)
    result = await analyzer.analyze_all_unreviewed()
    return result

@router.post("/manual/{prospect_id}", response_class=HTMLResponse)
async def save_manual_review(
    request: Request,
    prospect_id: int,
    opportunity_type: str = Form(...),
    opportunity_notes: str = Form(None),
    estimated_value: str = Form(None),
    urgency: str = Form(None),
    db: Session = Depends(get_db)
):
    review = db.query(WebsiteReview).filter(WebsiteReview.prospect_id == prospect_id).first()
    if not review:
        review = WebsiteReview(prospect_id=prospect_id)
        db.add(review)
        
    review.manual_reviewed = True
    review.manual_reviewed_at = datetime.now()
    review.opportunity_type = opportunity_type
    review.opportunity_notes = opportunity_notes
    review.estimated_value = estimated_value
    review.urgency = urgency
    
    db.commit()

    recalculate_score_after_review(db, prospect_id, review)

    return templates.TemplateResponse(request=request, name="review/result.html", context={"request": request, "review": review, "prospect_id": prospect_id})

def recalculate_score_after_review(db: Session, prospect_id: int, review: WebsiteReview):
    score = db.query(ProspectScore).filter(ProspectScore.prospect_id == prospect_id).first()
    if not score:
        return
        
    bonus = 0.0
    if review.opportunity_type in ['remake', 'redesign']:
        bonus = 1.5
    elif review.opportunity_type == 'optimasi':
        bonus = 0.5

    if review.urgency == 'high':
        bonus += 0.5

    new_score = min(10.0, score.priority_score + bonus)

    if new_score >= 7.0:
        tier = 'HOT'
    elif new_score >= 4.0:
        tier = 'WARM'
    else:
        tier = 'COLD'

    score.priority_score = new_score
    score.priority_tier = tier
    db.commit()
