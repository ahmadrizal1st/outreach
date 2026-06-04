from app.core.database import SessionLocal
from app.models.prospect import Prospect

class Deduplicator:

    def is_duplicate(self, place_id: str) -> bool:
        if not place_id:
            return False
            
        db = SessionLocal()
        try:
            exists = db.query(Prospect).filter(Prospect.place_id == place_id).first()
            return exists is not None
        finally:
            db.close()

    def get_duplicate_count(self) -> int:
        db = SessionLocal()
        try:
            return db.query(Prospect).count()
        finally:
            db.close()
