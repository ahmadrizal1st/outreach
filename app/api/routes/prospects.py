from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
import os

from app.core.database import get_db
from app.models.prospect import Prospect, ProspectScore, Pipeline

router = APIRouter()

templates_dir = os.path.join(os.path.dirname(__file__), "..", "..", "templates")
templates = Jinja2Templates(directory=templates_dir)

@router.get("/", response_class=HTMLResponse)
async def page_prospects(request: Request, db: Session = Depends(get_db)):
    # Render main page. HTMX will load the filter list.
    prospects = db.query(Prospect).limit(20).all() # default initial load
    return templates.TemplateResponse("prospects/list.html", {"request": request, "prospects": prospects})

@router.get("/filter", response_class=HTMLResponse)
async def filter_prospects(
    request: Request,
    tier: str = "",
    category: str = "",
    status: str = "",
    search: str = "",
    db: Session = Depends(get_db)
):
    query = db.query(Prospect, ProspectScore, Pipeline).outerjoin(
        ProspectScore, Prospect.id == ProspectScore.prospect_id
    ).outerjoin(
        Pipeline, Prospect.id == Pipeline.prospect_id
    )

    if tier:
        query = query.filter(ProspectScore.priority_tier == tier)
    if category:
        query = query.filter(Prospect.category == category)
    if status:
        if status in ['raw', 'scored']:
            query = query.filter(Prospect.status == status)
        else:
            query = query.filter(Pipeline.contact_status == status)
    if search:
        query = query.filter(Prospect.name.ilike(f"%{search}%"))

    results = query.limit(50).all()
    
    # Map to list of dicts for the card template
    prospects = []
    for p, s, pl in results:
        prospects.append({
            "id": p.id,
            "name": p.name,
            "category": p.category,
            "city": p.city,
            "address": p.address,
            "rating": p.rating,
            "review_count": p.review_count,
            "phone_raw": p.phone_raw,
            "phone_normalized": p.phone_normalized,
            "website": p.website,
            "priority_tier": s.priority_tier if s else None,
            "priority_score": s.priority_score if s else None
        })

    return templates.TemplateResponse(
        "partials/prospect_card.html" if len(prospects) == 1 else "prospects/list.html", 
        {"request": request, "prospects": prospects}
    )

@router.get("/{id}", response_class=HTMLResponse)
async def prospect_detail(request: Request, id: int, db: Session = Depends(get_db)):
    prospect = db.query(Prospect).filter(Prospect.id == id).first()
    score = db.query(ProspectScore).filter(ProspectScore.prospect_id == id).first()
    pipeline = db.query(Pipeline).filter(Pipeline.prospect_id == id).first()
    
    # Defaults/Placeholders for Phase 5 & 6
    review = None 
    message = None
    message_history = []
    
    pipeline_statuses = [
        {"value": "belum_dihubungi", "label": "Belum Dihubungi"},
        {"value": "sudah_dihubungi", "label": "Sudah Dihubungi"},
        {"value": "perlu_followup", "label": "Perlu Follow-up 🔔"},
        {"value": "dibalas", "label": "Dibalas"},
        {"value": "deal", "label": "Deal ✅"},
        {"value": "tidak_tertarik", "label": "Tidak Tertarik"}
    ]

    context = {
        "request": request,
        "prospect": prospect,
        "score": score,
        "pipeline": pipeline,
        "review": review,
        "message": message,
        "message_history": message_history,
        "pipeline_statuses": pipeline_statuses
    }
    
    return templates.TemplateResponse("prospects/detail.html", context)
