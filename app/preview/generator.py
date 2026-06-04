import os
import json
from datetime import date, timedelta
from jinja2 import Environment, FileSystemLoader

from app.ai.provider import LLMProvider
from app.ai.prompts.preview_content import get_preview_content_prompt
from app.preview.template_selector import TemplateSelector
from app.preview.content_builder import ContentBuilder
from app.core.database import SessionLocal
from app.models.prospect import Prospect, ProspectScore, WebsiteReview

class PreviewGenerator:
    def __init__(self, manual_provider=None):
        self.provider = LLMProvider(manual_provider)
        self.selector = TemplateSelector()
        self.builder = ContentBuilder()
        self.output_dir = "previews/generated"

    async def generate(self, prospect_id: int) -> dict:
        db = SessionLocal()
        try:
            prospect = db.query(Prospect).filter(Prospect.id == prospect_id).first()
            score = db.query(ProspectScore).filter(ProspectScore.prospect_id == prospect_id).first()
            review = db.query(WebsiteReview).filter(WebsiteReview.prospect_id == prospect_id).first()

            if not prospect:
                return {"status": "error", "message": "Prospect tidak ditemukan"}

            prospect_dict = {
                "id": prospect.id,
                "name": prospect.name,
                "category": prospect.category,
                "city": prospect.city,
                "address": prospect.address,
                "phone_raw": prospect.phone_raw,
                "phone_normalized": prospect.phone_normalized,
                "rating": prospect.rating,
                "review_count": prospect.review_count,
                "google_maps_url": prospect.google_maps_url
            }
            score_dict = {
                "relevant_keywords": score.relevant_keywords if score else None,
                "recommended_service": score.recommended_service if score else None
            } if score else {}
            review_dict = {
                "opportunity_notes": review.opportunity_notes if review else None
            } if review else {}

            ai_content = await self._generate_content(prospect_dict, score_dict, review_dict)
            content = self.builder.build(prospect_dict, ai_content)

            template_path = self.selector.get_template_path(prospect.category)
            template_name = self.selector.get_template_name(prospect.category)

            html = self._render_template(template_path, content)
            file_path = self._save_html(prospect_id, html)

            self._save_to_db(db, prospect_id, file_path, template_name)

            return {
                "status": "success",
                "file_path": file_path,
                "template": template_name,
                "prospect_name": prospect.name
            }
        finally:
            db.close()

    async def _generate_content(self, prospect: dict, score: dict, review: dict) -> dict:
        messages = get_preview_content_prompt(prospect, score, review)
        try:
            response = await self.provider.complete(messages)
            clean = response.strip()
            if clean.startswith("```json"):
                clean = clean[7:]
            if clean.endswith("```"):
                clean = clean[:-3]
            return json.loads(clean.strip())
        except Exception as e:
            return {
                "tagline": f"Selamat Datang di {prospect.get('name')}",
                "hero_description": f"Kami hadir untuk melayani Anda di {prospect.get('city')}",
                "about_text": f"{prospect.get('name')} adalah bisnis terpercaya di {prospect.get('city')}.",
                "services": [
                    {"title": "Layanan Utama", "description": "Layanan terbaik untuk Anda"},
                    {"title": "Konsultasi", "description": "Gratis konsultasi untuk Anda"},
                    {"title": "Informasi", "description": "Hubungi kami untuk info lebih lanjut"}
                ],
                "cta_text": "Hubungi Kami",
                "footer_tagline": "Terima kasih telah mempercayai kami"
            }

    def _render_template(self, template_path: str, content: dict) -> str:
        template_dir = os.path.dirname(os.path.abspath(template_path))
        template_file = os.path.basename(template_path)

        env = Environment(loader=FileSystemLoader(template_dir))
        template = env.get_template(template_file)
        return template.render(**content)

    def _save_html(self, prospect_id: int, html: str) -> str:
        folder = os.path.join(self.output_dir, str(prospect_id))
        os.makedirs(folder, exist_ok=True)
        file_path = os.path.join(folder, "index.html")
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(html)
        return file_path

    def _save_to_db(self, db, prospect_id: int, file_path: str, template_name: str):
        from app.models.prospect import Preview
        expired_at = date.today() + timedelta(days=14)

        preview = db.query(Preview).filter(Preview.prospect_id == prospect_id).first()
        if preview:
            preview.file_path = file_path
            preview.industry_template = template_name
            preview.expired_at = expired_at
            preview.open_count = 0
            preview.status = 'active'
        else:
            preview = Preview(
                prospect_id=prospect_id,
                file_path=file_path,
                industry_template=template_name,
                expired_at=expired_at,
                status='active'
            )
            db.add(preview)
        db.commit()

    def check_and_expire(self):
        db = SessionLocal()
        try:
            from app.models.prospect import Preview
            previews = db.query(Preview).filter(
                Preview.expired_at < date.today(),
                Preview.status == 'active'
            ).all()
            for p in previews:
                p.status = 'expired'
            db.commit()
        finally:
            db.close()

    def open_preview(self, prospect_id: int) -> str:
        db = SessionLocal()
        try:
            from app.models.prospect import Preview
            preview = db.query(Preview).filter(
                Preview.prospect_id == prospect_id,
                Preview.status == 'active'
            ).first()
            if not preview:
                return None

            preview.open_count = (preview.open_count or 0) + 1
            from datetime import datetime
            preview.last_opened_at = datetime.now()
            db.commit()

            abs_path = os.path.abspath(preview.file_path)
            return f"file://{abs_path}"
        finally:
            db.close()
