import os
import sys

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.database import Base, engine, SessionLocal
from app.models.prospect import Prospect

def init_db():
    print("Creating database and tables...")
    # Ensure data directory exists
    os.makedirs(os.path.join(os.path.dirname(__file__), "..", "data"), exist_ok=True)
    
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully!")

    print("Seeding dummy data...")
    db = SessionLocal()
    
    # Check if we already have dummy data
    if db.query(Prospect).count() == 0:
        dummy_prospect = Prospect(
            place_id="ChIJN1t_tDeuEmsRUsoyG83frY4",
            name="Dummy Cafe",
            category="Restaurant",
            address="123 Dummy Street",
            city="Jakarta"
        )
        db.add(dummy_prospect)
        db.commit()
        print("Dummy data seeded!")
    else:
        print("Data already exists. Skipping seed.")
        
    db.close()

if __name__ == "__main__":
    init_db()
