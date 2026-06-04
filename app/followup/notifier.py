from datetime import date
from sqlalchemy import func
from app.core.database import get_db
from app.models.prospect import Pipeline, ProspectScore

from sqlalchemy.orm import Session

class FollowupNotifier:
    def __init__(self, db: Session):
        self.db = db

    def get_summary(self) -> dict:
        return {
            "followups_today": self._count_followups_today(),
            "contacted_today": self._count_contacted_today(),
            "pending_cold": self._count_pending_cold(),
            "total_active": self._count_active_prospects()
        }

    def _count_followups_today(self) -> int:
        return self.db.query(Pipeline).filter(
            Pipeline.contact_status == 'perlu_followup',
            Pipeline.next_followup_date <= date.today(),
            Pipeline.is_blacklisted == False
        ).count()

    def _count_contacted_today(self) -> int:
        today = date.today()
        return self.db.query(Pipeline).filter(
            (func.date(Pipeline.contacted_at) == today) | (func.date(Pipeline.last_followup_at) == today)
        ).count()

    def _count_pending_cold(self) -> int:
        from app.core.config import settings
        return self.db.query(Pipeline).join(
            ProspectScore, Pipeline.prospect_id == ProspectScore.prospect_id
        ).filter(
            Pipeline.followup_count >= settings.MAX_FOLLOWUP,
            Pipeline.contact_status != 'tidak_tertarik'
        ).count()

    def _count_active_prospects(self) -> int:
        return self.db.query(Pipeline).filter(
            Pipeline.contact_status.notin_(['tidak_tertarik', 'deal']),
            Pipeline.is_blacklisted == False
        ).count()
