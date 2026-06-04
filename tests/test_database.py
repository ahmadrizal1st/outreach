import pytest
from app.core.database import SessionLocal
from app.models.prospect import Prospect, Pipeline
from tests.fixtures.prospect_sample import SAMPLE_PROSPECT

def test_insert_prospect():
    db = SessionLocal()
    try:
        existing = db.query(Prospect).filter(Prospect.place_id == SAMPLE_PROSPECT['place_id']).first()
        if existing:
            db.delete(existing)
            db.commit()

        prospect = Prospect(**SAMPLE_PROSPECT)
        db.add(prospect)
        db.commit()

        result = db.query(Prospect).filter(Prospect.place_id == SAMPLE_PROSPECT['place_id']).first()
        assert result is not None
        assert result.name == SAMPLE_PROSPECT['name']
    finally:
        db.close()

def test_pipeline_creation():
    db = SessionLocal()
    try:
        prospect = db.query(Prospect).filter(Prospect.place_id == SAMPLE_PROSPECT['place_id']).first()
        if prospect:
            existing_pipeline = db.query(Pipeline).filter(Pipeline.prospect_id == prospect.id).first()
            if not existing_pipeline:
                pipeline = Pipeline(prospect_id=prospect.id, contact_status='belum_dihubungi')
                db.add(pipeline)
                db.commit()

            pipeline = db.query(Pipeline).filter(Pipeline.prospect_id == prospect.id).first()
            assert pipeline is not None
            assert pipeline.contact_status == 'belum_dihubungi'
    finally:
        db.close()
