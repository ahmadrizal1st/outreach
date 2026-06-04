import pytest
from fastapi.testclient import TestClient
from main import app
from app.core.database import SessionLocal
from app.models.prospect import Prospect, Pipeline

client = TestClient(app)

def test_pipeline_drag_and_drop_update():
    """Test Item 22: Unit test endpoint Pipeline Drag-and-Drop (API Update Status)."""
    db = SessionLocal()
    prospect = None
    try:
        # 1. Create a dummy prospect for testing
        prospect = Prospect(
            place_id="test_drag_drop_123",
            name="Test Prospect Drag Drop",
            category="Test",
            city="Test City"
        )
        db.add(prospect)
        db.commit()
        db.refresh(prospect)

        # 2. Hit the endpoint to update status
        # Endpoint: POST /pipeline/status/{id}
        response = client.post(
            f"/pipeline/status/{prospect.id}",
            data={"status": "sudah_dihubungi"}
        )
        
        # 3. Assert success response
        assert response.status_code == 200

        # 4. Verify in database
        pipeline = db.query(Pipeline).filter(Pipeline.prospect_id == prospect.id).first()
        assert pipeline is not None
        assert pipeline.contact_status == "sudah_dihubungi"
        assert pipeline.contacted_at is not None

    finally:
        # Cleanup
        if prospect:
            db.query(Pipeline).filter(Pipeline.prospect_id == prospect.id).delete()
            db.query(Prospect).filter(Prospect.id == prospect.id).delete()
            db.commit()
        db.close()
