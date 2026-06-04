import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.database import SessionLocal
from tests.fixtures.prospect_sample import SAMPLE_PROSPECT, SAMPLE_PROSPECT_WITH_WEBSITE
from app.models.prospect import Prospect
from app.models.settings import LLMProvider, ScraperConfig

def seed():
    db = SessionLocal()
    try:
        
        samples = [SAMPLE_PROSPECT, SAMPLE_PROSPECT_WITH_WEBSITE]
        for sample in samples:
            existing = db.query(Prospect).filter(Prospect.place_id == sample['place_id']).first()
            if not existing:
                p = Prospect(**sample)
                db.add(p)
        db.commit()

        existing_provider = db.query(LLMProvider).filter(LLMProvider.provider_name == 'gemini').first()
        if not existing_provider:
            provider1 = LLMProvider(
                provider_name='gemini',
                api_key='YOUR_GEMINI_KEY',
                model_name='gemini-2.5-flash',
                is_active=True,
                priority_order=1,
                daily_token_limit=60000
            )
            db.add(provider1)
            
        existing_provider2 = db.query(LLMProvider).filter(LLMProvider.provider_name == 'groq').first()
        if not existing_provider2:
            provider2 = LLMProvider(
                provider_name='groq',
                api_key='YOUR_GROQ_KEY',
                model_name='llama-3.3-70b-versatile',
                is_active=True,
                priority_order=2,
                daily_token_limit=100000
            )
            db.add(provider2)
        db.commit()

        existing_config = db.query(ScraperConfig).first()
        if not existing_config:
            config = ScraperConfig(
                keywords='restoran,cafe,salon,klinik',
                target_categories='Restoran,Cafe,Salon,Klinik',
                target_cities='Surabaya',
                max_per_day=20
            )
            db.add(config)
        db.commit()

        print("[SUCCESS] Seed data berhasil")
    finally:
        db.close()

if __name__ == "__main__":
    seed()
