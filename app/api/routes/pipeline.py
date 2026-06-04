from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from datetime import datetime
import os

from app.core.database import get_db
from app.models.prospect import Pipeline, Prospect

router = APIRouter()

templates_dir = os.path.join(os.path.dirname(__file__), "..", "..", "templates")
templates = Jinja2Templates(directory=templates_dir)

def get_or_create_pipeline(db: Session, prospect_id: int):
    pipeline = db.query(Pipeline).filter(Pipeline.prospect_id == prospect_id).first()
    if not pipeline:
        pipeline = Pipeline(prospect_id=prospect_id)
        db.add(pipeline)
        db.commit()
        db.refresh(pipeline)
    return pipeline

@router.get("/", response_class=HTMLResponse)
async def pipeline_board(request: Request, db: Session = Depends(get_db)):
    columns = [
        {"id": "belum_dihubungi", "label": "Belum Dihubungi", "icon": "<i class='fa-solid fa-note-sticky'></i>"},
        {"id": "sudah_dihubungi", "label": "Sudah Dihubungi", "icon": "[SENT]"},
        {"id": "dibalas", "label": "Dibalas", "icon": "[MSG]"},
        {"id": "deal", "label": "Deal [SUCCESS]", "icon": "[DEAL]"}
    ]
    
    pipeline_columns = []
    
    for col in columns:
        
        if col["id"] == "belum_dihubungi":
            
            prospects_data = db.query(Prospect, Pipeline).outerjoin(
                Pipeline, Prospect.id == Pipeline.prospect_id
            ).filter(
                (Pipeline.id == None) | (Pipeline.contact_status == col["id"]),
                (Pipeline.is_blacklisted == False) | (Pipeline.id == None)
            ).all()
        else:
            prospects_data = db.query(Prospect, Pipeline).join(
                Pipeline, Prospect.id == Pipeline.prospect_id
            ).filter(
                Pipeline.contact_status == col["id"],
                Pipeline.is_blacklisted == False
            ).all()

        col_prospects = []
        for p, pl in prospects_data:
            col_prospects.append({
                "id": p.id,
                "name": p.name,
                "category": p.category,
                "city": p.city,
                "priority_tier": None, 
                "next_followup_date": pl.next_followup_date if pl else None
            })
            
        pipeline_columns.append({
            "id": col["id"],
            "label": col["label"],
            "icon": col["icon"],
            "count": len(col_prospects),
            "prospects": col_prospects
        })
        
    return templates.TemplateResponse(request=request, name="pipeline/board.html", context={"request": request, "pipeline_columns": pipeline_columns})

@router.post("/skip/{id}")
async def skip_prospect(id: int, db: Session = Depends(get_db)):
    
    pipeline = get_or_create_pipeline(db, id)
    pipeline.contact_status = "skipped"
    db.commit()
    
    return HTMLResponse("")

@router.post("/blacklist/{id}")
async def blacklist_prospect(id: int, db: Session = Depends(get_db)):
    pipeline = get_or_create_pipeline(db, id)
    pipeline.is_blacklisted = True
    pipeline.blacklisted_at = datetime.now()
    db.commit()
    return HTMLResponse("")

@router.post("/status/{id}")
async def update_status(id: int, status: str = Form(...), db: Session = Depends(get_db)):
    pipeline = get_or_create_pipeline(db, id)
    pipeline.contact_status = status
    if status == 'sudah_dihubungi' and not pipeline.contacted_at:
        pipeline.contacted_at = datetime.now()
    db.commit()

    return HTMLResponse("")

@router.post("/notes/{id}")
async def update_notes(id: int, notes: str = Form(""), db: Session = Depends(get_db)):
    pipeline = get_or_create_pipeline(db, id)
    pipeline.notes = notes
    db.commit()
    
    return HTMLResponse("")
