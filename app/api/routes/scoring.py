from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.ai.scorer import BusinessScorer
from app.models.prospect import ProspectScore, Prospect
from app.models.settings import LLMProvider

router = APIRouter()

class ProviderSchema(BaseModel):
    provider_name: str
    model_name: str
    api_key: str
    daily_token_limit: int = 100000
    priority_order: int = 1

@router.post("/run")
async def run_scoring(provider: str = None, db: Session = Depends(get_db)):
    scorer = BusinessScorer(db, provider)
    result = await scorer.score_all_unscored()
    return result

@router.post("/prospect/{prospect_id}")
async def score_single(prospect_id: int, provider: str = None, db: Session = Depends(get_db)):
    scorer = BusinessScorer(db, provider)
    result = await scorer.score_prospect(prospect_id)
    return result

@router.get("/status")
async def scoring_status(db: Session = Depends(get_db)):
    total_scored = db.query(ProspectScore).count()
    total_unscored = db.query(Prospect).filter(Prospect.status == 'raw').count()
    
    return {
        "scored": total_scored,
        "unscored": total_unscored
    }

@router.get("/providers")
async def get_providers(db: Session = Depends(get_db)):
    providers = db.query(LLMProvider).all()
    return providers

@router.post("/providers")
async def save_provider(provider_data: ProviderSchema, db: Session = Depends(get_db)):
    provider = db.query(LLMProvider).filter(LLMProvider.provider_name == provider_data.provider_name).first()
    if provider:
        provider.model_name = provider_data.model_name
        provider.api_key = provider_data.api_key
        provider.daily_token_limit = provider_data.daily_token_limit
        provider.priority_order = provider_data.priority_order
    else:
        provider = LLMProvider(
            provider_name=provider_data.provider_name,
            model_name=provider_data.model_name,
            api_key=provider_data.api_key,
            daily_token_limit=provider_data.daily_token_limit,
            priority_order=provider_data.priority_order
        )
        db.add(provider)
    
    db.commit()
    return {"status": "success"}

@router.put("/providers/{id}/toggle")
async def toggle_provider(id: int, db: Session = Depends(get_db)):
    provider = db.query(LLMProvider).filter(LLMProvider.id == id).first()
    if provider:
        provider.is_active = not provider.is_active
        db.commit()
        return {"status": "success", "is_active": provider.is_active}
    return {"error": "Provider not found"}
