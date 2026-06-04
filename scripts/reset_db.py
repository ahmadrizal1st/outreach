import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.database import Base, engine
from app.models import prospect  

def reset():
    confirm = input("[WARNING] Reset database? Semua data akan hilang. (y/n): ")
    if confirm.lower() != 'y':
        print("Dibatalkan")
        return

    db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "database.sqlite"))
    if os.path.exists(db_path):
        os.remove(db_path)
        print("[SUCCESS] Database direset")

    Base.metadata.create_all(bind=engine)
    print("[SUCCESS] Tabel dibuat ulang")

if __name__ == "__main__":
    reset()
