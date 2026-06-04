import json
from urllib.parse import quote
from sqlalchemy.orm import Session
from app.ai.provider import LLMProvider
from app.ai.prompts.message_first import get_first_message_prompt
from app.ai.prompts.message_followup import get_followup_message_prompt
from app.models.prospect import Prospect, ProspectScore, WebsiteReview, Message

class MessageGenerator:
    def __init__(self, db: Session, manual_provider: str = None):
        self.db = db
        self.provider = LLMProvider(db, manual_provider)

    async def generate_first(self, prospect_id: int) -> dict:
        prospect = self._get_prospect(prospect_id)
        score = self._get_score(prospect_id)
        review = self._get_review(prospect_id)

        if not prospect or not score:
            return {"error": "Data tidak lengkap (Prospect atau Score tidak ditemukan)"}

        prospect_dict = {
            "name": prospect.name,
            "category": prospect.category,
            "city": prospect.city,
            "rating": prospect.rating,
            "review_count": prospect.review_count,
            "phone_normalized": prospect.phone_normalized
        }
        score_dict = {
            "pitch_angle": score.pitch_angle,
            "recommended_service": score.recommended_service,
            "relevant_keywords": score.relevant_keywords
        }
        review_dict = {
            "opportunity_type": review.opportunity_type,
            "opportunity_notes": review.opportunity_notes
        } if review else None

        messages = get_first_message_prompt(prospect_dict, score_dict, review_dict)
        response = await self.provider.complete(messages)

        variants = self._parse_variants(response)
        if not variants:
            return {"error": "Gagal generate pesan"}

        self.db.query(Message).filter(Message.prospect_id == prospect_id, Message.status == 'draft').delete()
        self.db.commit()

        saved_ids = self._save_variants(prospect_id, variants, sequence=0)

        saved_messages = self.db.query(Message).filter(Message.id.in_(saved_ids)).all()

        return {
            "variants": saved_messages,
            "prospect": prospect_dict
        }

    async def generate_followup(self, prospect_id: int, sequence: int) -> dict:
        prospect = self._get_prospect(prospect_id)
        score = self._get_score(prospect_id)
        review = self._get_review(prospect_id)
        previous = self._get_previous_messages(prospect_id)

        if not prospect or not score:
            return {"error": "Data tidak lengkap"}

        prospect_dict = {
            "name": prospect.name,
            "category": prospect.category,
            "city": prospect.city,
            "phone_normalized": prospect.phone_normalized
        }
        score_dict = {
            "pitch_angle": score.pitch_angle,
            "recommended_service": score.recommended_service
        }
        review_dict = {"opportunity_type": review.opportunity_type} if review else {}

        messages = get_followup_message_prompt(prospect_dict, score_dict, review_dict, previous, sequence)
        response = await self.provider.complete(messages)

        variants = self._parse_variants(response)
        if not variants:
            return {"error": "Gagal generate pesan"}

        self.db.query(Message).filter(Message.prospect_id == prospect_id, Message.status == 'draft').delete()
        self.db.commit()

        saved_ids = self._save_variants(prospect_id, variants, sequence=sequence)
        saved_messages = self.db.query(Message).filter(Message.id.in_(saved_ids)).all()

        return {
            "variants": saved_messages,
            "prospect": prospect_dict
        }

    def generate_wa_link(self, phone: str, message: str) -> str:
        if not phone:
            return "#"
        encoded = quote(message)
        return f"https://wa.me/{phone}?text={encoded}"

    def mark_as_sent(self, message_id: int):
        from datetime import datetime
        msg = self.db.query(Message).filter(Message.id == message_id).first()
        if msg:
            msg.status = 'sent'
            msg.sent_at = datetime.now()
            self.db.commit()

            self.db.query(Message).filter(
                Message.prospect_id == msg.prospect_id,
                Message.sequence == msg.sequence,
                Message.status == 'draft'
            ).delete()
            self.db.commit()

    def _parse_variants(self, response: str) -> list:
        try:
            clean = response.strip()
            if '```json' in clean:
                clean = clean.split('```json')[1].split('```')[0].strip()
            elif '```' in clean:
                clean = clean.split('```')[1].strip()
            data = json.loads(clean)
            return data.get('variants', [])
        except Exception as e:
            logger.error(f"Failed to parse variants: {e}")
            return []

    def _save_variants(self, prospect_id: int, variants: list, sequence: int) -> list:
        saved_ids = []
        for variant in variants:
            msg = Message(
                prospect_id=prospect_id,
                sequence=sequence,
                content=variant.get('message'),
                tone=variant.get('tone'),
                provider_used=self.provider.last_used_provider,
                status='draft'
            )
            self.db.add(msg)
            self.db.commit()
            self.db.refresh(msg)
            saved_ids.append(msg.id)
        return saved_ids

    def _get_prospect(self, prospect_id: int):
        return self.db.query(Prospect).filter(Prospect.id == prospect_id).first()

    def _get_score(self, prospect_id: int):
        return self.db.query(ProspectScore).filter(ProspectScore.prospect_id == prospect_id).order_by(ProspectScore.scored_at.desc()).first()

    def _get_review(self, prospect_id: int):
        return self.db.query(WebsiteReview).filter(WebsiteReview.prospect_id == prospect_id).first()

    def _get_previous_messages(self, prospect_id: int) -> list:
        rows = self.db.query(Message).filter(Message.prospect_id == prospect_id, Message.status == 'sent').order_by(Message.sent_at.asc()).all()
        return [{"content": r.content, "tone": r.tone, "sequence": r.sequence} for r in rows]
