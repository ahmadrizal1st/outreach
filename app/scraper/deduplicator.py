from sqlalchemy.orm import Session
from app.models.prospect import Prospect

class Deduplicator:
    def __init__(self, db: Session):
        self.db = db

    def is_duplicate(self, place_id: str) -> bool:
        if not place_id:
            return False
            
        exists = self.db.query(Prospect).filter(Prospect.place_id == place_id).first()
        return exists is not None

    def get_duplicate_count(self) -> int:
        return self.db.query(Prospect).count()
