from fastapi import APIRouter, Depends, Request
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import os

from app.core.database import get_db
from app.core.exporter import DataExporter

router = APIRouter()

@router.get("/csv")
async def export_csv(tier: str = None, db: Session = Depends(get_db)):
    exporter = DataExporter()
    filepath = exporter.export_csv(tier)
    filename = os.path.basename(filepath)
    return FileResponse(path=filepath, filename=filename, media_type='text/csv')

@router.get("/excel")
async def export_excel(tier: str = None, db: Session = Depends(get_db)):
    exporter = DataExporter()
    filepath = exporter.export_excel(tier)
    filename = os.path.basename(filepath)
    return FileResponse(
        path=filepath,
        filename=filename,
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
