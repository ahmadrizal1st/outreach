from sqlalchemy.sql import func
import json
from sqlalchemy.orm import Session
from app.ai.provider import LLMProvider
from app.ai.prompts.scoring import get_scoring_prompt
from app.models.prospect import Prospect, ProspectScore

class BusinessScorer:

    def __init__(self, db: Session, manual_provider: str = None):
        self.db = db
        self.provider = LLMProvider(db, manual_provider)

    async def score_prospect(self, prospect_id: int) -> dict:
        
        prospect = self._get_prospect(prospect_id)
        if not prospect:
            return {"error": "Prospect tidak ditemukan"}

        prospect_dict = {
            "name": prospect.name,
            "category": prospect.category,
            "city": prospect.city,
            "rating": prospect.rating,
            "review_count": prospect.review_count,
            "website": prospect.website,
            "phone_normalized": prospect.phone_normalized
        }

        score_data = await self._get_score(prospect_dict)
        if not score_data:
            return {"error": "Scoring gagal"}

        self._save_score(prospect_id, score_data)

        self._update_prospect_status(prospect_id, 'scored')

        return score_data

    async def score_all_unscored(self) -> dict:

        prospects = self.db.query(Prospect).outerjoin(
            ProspectScore, Prospect.id == ProspectScore.prospect_id
        ).filter(
            ProspectScore.id == None,
            Prospect.status == 'raw'
        ).limit(50).all()

        results = {
            "total": len(prospects),
            "success": 0,
            "failed": 0
        }

        for prospect in prospects:
            try:
                await self.score_prospect(prospect.id)
                results["success"] += 1
            except Exception as e:
                results["failed"] += 1
                continue

        return results

    async def _get_score(self, prospect: dict) -> dict:
        messages = get_scoring_prompt(prospect)

        try:
            response = await self.provider.complete(messages)
            if not response:
                return None
            
            clean = response.strip()
            
            clean = clean.replace('```json', '')
            clean = clean.replace('```', '')
            return json.loads(clean)
        except json.JSONDecodeError:
            return None
        except Exception as e:
            return None

    def _save_score(self, prospect_id: int, score_data: dict):
        new_score = ProspectScore(
            prospect_id=prospect_id,
            priority_score=score_data.get('priority_score'),
            priority_tier=score_data.get('priority_tier'),
            score_reasoning=score_data.get('score_reasoning'),
            recommended_service=score_data.get('recommended_service'),
            pitch_angle=score_data.get('pitch_angle'),
            relevant_keywords=json.dumps(score_data.get('relevant_keywords', []))
        )
        self.db.add(new_score)
        self.db.commit()

    def _get_prospect(self, prospect_id: int):
        return self.db.query(Prospect).filter(Prospect.id == prospect_id).first()

    def _update_prospect_status(self, prospect_id: int, status: str):
        prospect = self._get_prospect(prospect_id)
        if prospect:
            prospect.status = status
            prospect.updated_at = func.now()
            self.db.commit()
