from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
import os

from app.core.database import get_db
from app.ai.message_generator import MessageGenerator
from app.models.prospect import Message, Prospect

router = APIRouter()

templates_dir = os.path.join(os.path.dirname(__file__), "..", "..", "templates")
templates = Jinja2Templates(directory=templates_dir)

@router.post("/generate/{prospect_id}", response_class=HTMLResponse)
async def generate_first_message(
    request: Request,
    prospect_id: int,
    provider: str = None,
    db: Session = Depends(get_db)
):
    generator = MessageGenerator(db=db, manual_provider=provider)
    result = await generator.generate_first(prospect_id)
    
    return templates.TemplateResponse(request=request, name="messages/preview.html", context={"request": request, "result": result, "prospect_id": prospect_id, "generator": generator})

@router.post("/followup/{prospect_id}", response_class=HTMLResponse)
async def generate_followup_message(
    request: Request,
    prospect_id: int,
    sequence: int = 1,
    provider: str = None,
    db: Session = Depends(get_db)
):
    generator = MessageGenerator(db=db, manual_provider=provider)
    result = await generator.generate_followup(prospect_id, sequence)
    
    return templates.TemplateResponse(request=request, name="messages/preview.html", context={"request": request, "result": result, "prospect_id": prospect_id, "generator": generator})

@router.post("/regenerate/{prospect_id}", response_class=HTMLResponse)
async def regenerate_message(
    request: Request,
    prospect_id: int,
    provider: str = None,
    db: Session = Depends(get_db)
):
    generator = MessageGenerator(db=db, manual_provider=provider)
    result = await generator.generate_first(prospect_id)
    
    return templates.TemplateResponse(request=request, name="messages/preview.html", context={"request": request, "result": result, "prospect_id": prospect_id, "generator": generator})

@router.post("/sent/{message_id}")
async def mark_sent(message_id: int, db: Session = Depends(get_db)):
    generator = MessageGenerator(db=db)
    generator.mark_as_sent(message_id)

    return HTMLResponse("")

@router.get("/history/{prospect_id}", response_class=HTMLResponse)
async def message_history(request: Request, prospect_id: int, db: Session = Depends(get_db)):
    messages = db.query(Message).filter(Message.prospect_id == prospect_id).order_by(Message.generated_at.desc()).all()
    prospect = db.query(Prospect).filter(Prospect.id == prospect_id).first()
    
    return templates.TemplateResponse(request=request, name="messages/history.html", context={"request": request, "messages": messages, "phone": prospect.phone_normalized if prospect else ""})
