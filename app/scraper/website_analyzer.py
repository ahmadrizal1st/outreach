import json
import logging
from sqlalchemy.orm import Session
from app.scraper.website_checker import WebsiteChecker
from app.ai.provider import LLMProvider
from app.ai.prompts.website_review import get_website_review_prompt
from app.models.prospect import Prospect, WebsiteReview as WebsiteReviewModel

logger = logging.getLogger(__name__)

class WebsiteAnalyzer:
    def __init__(self, db: Session, manual_provider: str = None):
        self.db = db
        self.checker = WebsiteChecker()
        self.provider = LLMProvider(db, manual_provider)

    async def analyze(self, prospect_id: int) -> dict:
        prospect = self._get_prospect(prospect_id)
        if not prospect:
            return {"error": "Prospect tidak ditemukan"}

        if not prospect.website:
            return self._save_no_website(prospect_id)

        check_result = await self.checker.check(prospect.website)

        if check_result['website_status'] != 'accessible':
            return self._save_inaccessible(prospect_id, check_result)

        prospect_dict = {
            "name": prospect.name,
            "category": prospect.category,
            "city": prospect.city,
            "website": prospect.website
        }

        messages = get_website_review_prompt(prospect_dict, check_result)
        response = await self.provider.complete(messages)

        try:
            clean = response.strip()
            if '```json' in clean:
                clean = clean.split('```json')[1].split('```')[0].strip()
            elif '```' in clean:
                clean = clean.split('```')[1].strip()
            ai_result = json.loads(clean)
        except Exception as e:
            logger.error(f"Error parsing AI response: {e}")
            ai_result = {}

        final_result = {**check_result, **ai_result}

        self._save_review(prospect_id, final_result)
        self._update_status(prospect_id, 'reviewed')

        return final_result

    async def analyze_all_unreviewed(self) -> dict:
        
        prospects = self.db.query(Prospect).outerjoin(
            WebsiteReviewModel, Prospect.id == WebsiteReviewModel.prospect_id
        ).filter(
            WebsiteReviewModel.id == None,
            Prospect.website != None,
            Prospect.website != '',
            Prospect.status == 'scored'
        ).limit(20).all()

        results = {
            "total": len(prospects),
            "success": 0,
            "failed": 0,
            "no_website": 0
        }

        for p in prospects:
            try:
                res = await self.analyze(p.id)
                if res.get('website_status') == 'no_website':
                    results["no_website"] += 1
                elif 'error' in res:
                    results["failed"] += 1
                else:
                    results["success"] += 1
            except Exception as e:
                logger.error(f"Failed analyzing {p.id}: {e}")
                results["failed"] += 1

        return results

    def _save_review(self, prospect_id: int, data: dict):
        review = self.db.query(WebsiteReviewModel).filter(
            WebsiteReviewModel.prospect_id == prospect_id
        ).first()
        if not review:
            review = WebsiteReviewModel(prospect_id=prospect_id)
            self.db.add(review)

        review.website_status = data.get('website_status')
        review.is_mobile_friendly = data.get('is_mobile_friendly')
        review.has_ssl = data.get('has_ssl')
        review.has_ecommerce = data.get('has_ecommerce')
        review.has_booking = data.get('has_booking')
        review.has_contact_form = data.get('has_contact_form')
        review.speed_score = data.get('speed_score')
        review.design_quality_score = data.get('design_quality_score')

        issues = data.get('website_issues', [])
        review.website_issues = json.dumps(issues) if isinstance(issues, list) else str(issues)
        review.website_summary = data.get('website_summary')
        review.opportunity_type = data.get('opportunity_type')
        review.opportunity_notes = data.get('opportunity_reason')
        review.estimated_value = data.get('estimated_value')
        review.urgency = data.get('urgency')

        self.db.commit()

    def _save_no_website(self, prospect_id: int):
        review = self.db.query(WebsiteReviewModel).filter(
            WebsiteReviewModel.prospect_id == prospect_id
        ).first()
        if not review:
            review = WebsiteReviewModel(prospect_id=prospect_id)
            self.db.add(review)

        review.website_status = 'no_website'
        self.db.commit()
        return {"website_status": "no_website"}

    def _save_inaccessible(self, prospect_id: int, check_result: dict):
        review = self.db.query(WebsiteReviewModel).filter(
            WebsiteReviewModel.prospect_id == prospect_id
        ).first()
        if not review:
            review = WebsiteReviewModel(prospect_id=prospect_id)
            self.db.add(review)

        review.website_status = check_result['website_status']
        self.db.commit()
        return check_result

    def _get_prospect(self, prospect_id: int):
        return self.db.query(Prospect).filter(Prospect.id == prospect_id).first()

    def _update_status(self, prospect_id: int, status: str):
        """Update prospect status only if it hasn't progressed further."""
        prospect = self._get_prospect(prospect_id)
        if prospect and prospect.status in ('raw', 'scored'):
            prospect.status = status
            self.db.commit()
