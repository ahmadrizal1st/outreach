import json
from sqlalchemy.orm import Session
from app.ai.provider import LLMProvider
from app.ai.prompts.analysis import get_analysis_prompt
from app.models.prospect import Prospect, ProspectScore

class BusinessAnalyzer:

    def __init__(self, db: Session, manual_provider: str = None):
        self.db = db
        self.provider = LLMProvider(db, manual_provider)

    async def analyze(self, prospect_id: int) -> dict:
        prospect = self._get_prospect(prospect_id)
        if not prospect:
            return {"error": "Prospect tidak ditemukan"}

        prospect_dict = {
            "name": prospect.name,
            "category": prospect.category,
            "city": prospect.city,
            "rating": prospect.rating,
            "review_count": prospect.review_count,
            "website": prospect.website
        }

        messages = get_analysis_prompt(prospect_dict)

        try:
            response = await self.provider.complete(messages)
            if not response:
                return {"error": "Analysis failed"}
            clean = response.strip()
            clean = clean.replace('```json', '')
            clean = clean.replace('```', '')
            analysis = json.loads(clean)

            self._save_analysis(prospect_id, analysis)
            return analysis

        except Exception as e:
            return {"error": str(e)}

    def _save_analysis(self, prospect_id: int, analysis: dict):
        score = self.db.query(ProspectScore).filter(ProspectScore.prospect_id == prospect_id).first()
        if score:
            score.pitch_angle = analysis.get('value_proposition')
            self.db.commit()

    def _get_prospect(self, prospect_id: int):
        return self.db.query(Prospect).filter(Prospect.id == prospect_id).first()
