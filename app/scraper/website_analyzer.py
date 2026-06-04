import json
from app.scraper.website_checker import WebsiteChecker
from app.ai.provider import LLMProvider
from app.ai.prompts.website_review import get_website_review_prompt
from app.core.database import get_db

class WebsiteAnalyzer:
    def __init__(self, manual_provider=None):
        self.checker = WebsiteChecker()
        self.provider = LLMProvider(manual_provider)
        self.db = next(get_db())

    async def analyze(self, prospect_id: int) -> dict:
        prospect = self._get_prospect(prospect_id)
        if not prospect:
            return {"error": "Prospect tidak ditemukan"}

        # If no website, skip scan
        if not prospect.website:
            return self._save_no_website(prospect_id)

        # Technical check
        check_result = await self.checker.check(prospect.website)

        # If inaccessible
        if check_result['website_status'] != 'accessible':
            return self._save_inaccessible(prospect_id, check_result)

        # AI Analysis
        prospect_dict = {
            "name": prospect.name,
            "category": prospect.category,
            "city": prospect.city,
            "website": prospect.website
        }
        
        messages = get_website_review_prompt(prospect_dict, check_result)
        response = await self.provider.complete(messages)

        # Parse JSON
        try:
            clean = response.strip()
            if '```json' in clean:
                clean = clean.split('```json')[1].split('```')[0].strip()
            elif '```' in clean:
                clean = clean.split('```')[1].strip()
            ai_result = json.loads(clean)
        except Exception as e:
            print(f"Error parsing AI response: {e}")
            ai_result = {}

        # Combine
        final_result = {**check_result, **ai_result}

        # Save to DB
        self._save_review(prospect_id, final_result)

        # Update prospect status to reviewed (or keeping it scored is fine too)
        self._update_status(prospect_id, 'reviewed')

        return final_result

    async def analyze_all_unreviewed(self) -> dict:
        # Get unreviewed prospects that have a website
        prospects = self.db.execute("""
            SELECT p.id FROM prospects p
            LEFT JOIN website_reviews wr ON p.id = wr.prospect_id
            WHERE wr.id IS NULL
            AND p.website IS NOT NULL
            AND p.website != ''
            AND p.status = 'scored'
            LIMIT 20
        """).fetchall()

        results = {
            "total": len(prospects),
            "success": 0,
            "failed": 0,
            "no_website": 0
        }

        for p in prospects:
            try:
                res = await self.analyze(p[0])
                if res.get('website_status') == 'no_website':
                    results["no_website"] += 1
                elif 'error' in res:
                    results["failed"] += 1
                else:
                    results["success"] += 1
            except Exception as e:
                print(f"Failed analyzing {p[0]}: {e}")
                results["failed"] += 1

        return results

    def _save_review(self, prospect_id: int, data: dict):
        from app.models.prospect import WebsiteReview
        
        review = self.db.query(WebsiteReview).filter(WebsiteReview.prospect_id == prospect_id).first()
        if not review:
            review = WebsiteReview(prospect_id=prospect_id)
            self.db.add(review)

        review.website_status = data.get('website_status')
        review.is_mobile_friendly = data.get('is_mobile_friendly')
        review.has_ssl = data.get('has_ssl')
        review.has_ecommerce = data.get('has_ecommerce')
        review.has_booking = data.get('has_booking')
        review.has_contact_form = data.get('has_contact_form')
        review.speed_score = data.get('speed_score')
        review.design_quality_score = data.get('design_quality_score')
        
        # Handle list correctly
        issues = data.get('website_issues', [])
        if isinstance(issues, list):
            review.website_issues = json.dumps(issues)
        else:
            review.website_issues = str(issues)
            
        review.website_summary = data.get('website_summary')
        review.opportunity_type = data.get('opportunity_type')
        review.opportunity_notes = data.get('opportunity_reason') # Note: using opportunity_reason from prompt
        review.estimated_value = data.get('estimated_value')
        review.urgency = data.get('urgency')

        self.db.commit()

    def _save_no_website(self, prospect_id: int):
        from app.models.prospect import WebsiteReview
        review = self.db.query(WebsiteReview).filter(WebsiteReview.prospect_id == prospect_id).first()
        if not review:
            review = WebsiteReview(prospect_id=prospect_id)
            self.db.add(review)
            
        review.website_status = 'no_website'
        self.db.commit()
        return {"website_status": "no_website"}

    def _save_inaccessible(self, prospect_id: int, check_result: dict):
        from app.models.prospect import WebsiteReview
        review = self.db.query(WebsiteReview).filter(WebsiteReview.prospect_id == prospect_id).first()
        if not review:
            review = WebsiteReview(prospect_id=prospect_id)
            self.db.add(review)
            
        review.website_status = check_result['website_status']
        self.db.commit()
        return check_result

    def _get_prospect(self, prospect_id: int):
        from app.models.prospect import Prospect
        return self.db.query(Prospect).filter(Prospect.id == prospect_id).first()

    def _update_status(self, prospect_id: int, status: str):
        prospect = self._get_prospect(prospect_id)
        if prospect:
            # We don't overwrite if it's already beyond reviewed, but for simplicity we do it here.
            # Actually, let's keep status as scored so it shows up in normal lists unless we strictly use reviewed
            pass
            # prospect.status = status
            # self.db.commit()
