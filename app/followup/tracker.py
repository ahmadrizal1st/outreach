from datetime import date, datetime, timedelta
from app.core.database import get_db
from app.core.config import settings
from app.models.prospect import Prospect, Pipeline, ProspectScore

class FollowupTracker:
    def __init__(self):
        self.db = next(get_db())
        self.interval_days = settings.FOLLOWUP_INTERVAL_DAYS
        self.max_followup = settings.MAX_FOLLOWUP

    def check_and_flag(self) -> dict:
        prospects = self._get_prospects_to_check()
        flagged = 0
        coldened = 0

        for prospect in prospects:
            pipeline = self.db.query(Pipeline).filter(Pipeline.prospect_id == prospect.id).first()
            if not pipeline:
                continue

            last_contact = pipeline.last_followup_at or pipeline.contacted_at
            if not last_contact:
                continue

            last_contact_date = last_contact.date()
            days_since = (date.today() - last_contact_date).days

            if days_since >= self.interval_days:
                if (pipeline.followup_count or 0) >= self.max_followup:
                    self._mark_cold(prospect.id)
                    coldened += 1
                else:
                    self._flag_followup(prospect.id)
                    flagged += 1

        return {
            "flagged": flagged,
            "coldened": coldened,
            "checked": len(prospects)
        }

    def get_followups_today(self) -> list:
        # Join prospect, pipeline, prospect_scores
        results = self.db.query(Prospect, Pipeline, ProspectScore).join(
            Pipeline, Prospect.id == Pipeline.prospect_id
        ).join(
            ProspectScore, Prospect.id == ProspectScore.prospect_id
        ).filter(
            Pipeline.contact_status == 'perlu_followup',
            Pipeline.is_blacklisted == False,
            (Pipeline.next_followup_date <= date.today()) | (Pipeline.next_followup_date == None)
        ).order_by(ProspectScore.priority_score.desc()).all()

        followups = []
        for p, pl, ps in results:
            followups.append({
                "id": p.id,
                "name": p.name,
                "category": p.category,
                "city": p.city,
                "followup_count": pl.followup_count or 0,
                "priority_tier": ps.priority_tier,
                "priority_score": ps.priority_score,
                "pitch_angle": ps.pitch_angle
            })
        return followups

    def mark_followup_sent(self, prospect_id: int):
        pipeline = self.db.query(Pipeline).filter(Pipeline.prospect_id == prospect_id).first()
        if pipeline:
            new_count = (pipeline.followup_count or 0) + 1
            next_date = date.today() + timedelta(days=self.interval_days)

            pipeline.followup_count = new_count
            pipeline.last_followup_at = datetime.now()
            pipeline.next_followup_date = next_date
            pipeline.contact_status = 'sudah_dihubungi'
            self.db.commit()

    def _get_prospects_to_check(self) -> list:
        return self.db.query(Prospect).join(
            Pipeline, Prospect.id == Pipeline.prospect_id
        ).filter(
            Pipeline.contact_status.in_(['sudah_dihubungi', 'perlu_followup']),
            Pipeline.is_blacklisted == False,
            Pipeline.followup_count < self.max_followup
        ).all()

    def _flag_followup(self, prospect_id: int):
        pipeline = self.db.query(Pipeline).filter(Pipeline.prospect_id == prospect_id).first()
        if pipeline:
            pipeline.contact_status = 'perlu_followup'
            pipeline.next_followup_date = date.today()
            self.db.commit()

    def _mark_cold(self, prospect_id: int):
        pipeline = self.db.query(Pipeline).filter(Pipeline.prospect_id == prospect_id).first()
        if pipeline:
            pipeline.contact_status = 'tidak_tertarik'
            pipeline.updated_at = datetime.now()
            
        score = self.db.query(ProspectScore).filter(ProspectScore.prospect_id == prospect_id).first()
        if score:
            score.priority_tier = 'COLD'
            
        self.db.commit()
