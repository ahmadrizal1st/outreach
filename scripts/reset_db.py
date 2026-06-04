import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.database import Base, engine

def reset():
    confirm = input("⚠️ Reset database? Semua data akan hilang. (y/n): ")
    if confirm.lower() != 'y':
        print("Dibatalkan")
        return

    db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "database.sqlite"))
    if os.path.exists(db_path):
        os.remove(db_path)
        print("✅ Database direset")

    # Recreate tables
    Base.metadata.create_all(bind=engine)
    print("✅ Tabel dibuat ulang")

if __name__ == "__main__":
    reset()
