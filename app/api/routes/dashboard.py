from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import func
import os

from app.core.database import get_db
from app.models.prospect import Prospect, ProspectScore, LLMProvider

router = APIRouter()

# Setup templates
templates_dir = os.path.join(os.path.dirname(__file__), "..", "..", "templates")
templates = Jinja2Templates(directory=templates_dir)

@router.get("/", response_class=HTMLResponse)
async def read_dashboard(request: Request, db: Session = Depends(get_db)):
    unscored = db.query(Prospect).outerjoin(
        ProspectScore, Prospect.id == ProspectScore.prospect_id
    ).filter(ProspectScore.id == None, Prospect.status == 'raw').count()
    
    scored = db.query(ProspectScore).count()
    
    hot = db.query(ProspectScore).filter(ProspectScore.priority_tier == 'HOT').count()
    warm = db.query(ProspectScore).filter(ProspectScore.priority_tier == 'WARM').count()
    cold = db.query(ProspectScore).filter(ProspectScore.priority_tier == 'COLD').count()
    
    providers = db.query(LLMProvider).all()
    
    context = {
        "title": "Dashboard",
        "unscored": unscored,
        "scored": scored,
        "hot": hot,
        "warm": warm,
        "cold": cold,
        "providers": providers
    }
    
    return templates.TemplateResponse(
        request=request, name="dashboard.html", context=context
    )
