from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
import os

from app.core.database import get_db
from app.preview.generator import PreviewGenerator
from app.models.prospect import Preview

router = APIRouter()
templates_dir = os.path.join(os.path.dirname(__file__), "..", "..", "templates")
templates = Jinja2Templates(directory=templates_dir)

@router.post("/generate/{prospect_id}")
async def generate_preview(request: Request, prospect_id: int, provider: str = None, db: Session = Depends(get_db)):
    generator = PreviewGenerator(provider)
    result = await generator.generate(prospect_id)
    return templates.TemplateResponse(
        "preview/preview_card.html",
        {"request": request, "result": result, "prospect_id": prospect_id}
    )

@router.get("/open/{prospect_id}")
async def open_preview(prospect_id: int):
    generator = PreviewGenerator()
    file_url = generator.open_preview(prospect_id)

    if not file_url:
        return JSONResponse({"error": "Preview tidak ditemukan"}, status_code=404)

    return JSONResponse({"url": file_url})

@router.post("/regenerate/{prospect_id}")
async def regenerate_preview(request: Request, prospect_id: int, provider: str = None, db: Session = Depends(get_db)):
    generator = PreviewGenerator(provider)
    result = await generator.generate(prospect_id)
    return templates.TemplateResponse(
        "preview/preview_card.html",
        {"request": request, "result": result, "prospect_id": prospect_id}
    )

@router.post("/expire")
async def run_expire_check():
    generator = PreviewGenerator()
    generator.check_and_expire()
    return JSONResponse({"status": "done"})

@router.get("/status/{prospect_id}", response_class=HTMLResponse)
async def get_preview_status(request: Request, prospect_id: int, db: Session = Depends(get_db)):
    preview = db.query(Preview).filter(Preview.prospect_id == prospect_id, Preview.status == 'active').first()
    
    if preview:
        result = {
            "status": "success",
            "template": preview.industry_template
        }
    else:
        result = {"status": "none"}
        
    return templates.TemplateResponse(
        "preview/preview_card.html",
        {"request": request, "result": result, "prospect_id": prospect_id}
    )
