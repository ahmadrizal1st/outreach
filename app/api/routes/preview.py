import json
import logging
from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import templates
from app.models.prospect import Prospect, ProspectScore, WebsiteReview
from app.models.settings import AppSetting
from app.ai.provider import LLMProvider
from app.ai.prompts.preview_content import get_preview_content_prompt

logger = logging.getLogger(__name__)
router = APIRouter()



@router.post("/generate/{prospect_id}", response_class=HTMLResponse)
async def generate_preview(
    request: Request,
    prospect_id: int,
    provider: str = None,
    db: Session = Depends(get_db)
):
    """Generate website preview content via AI and return the "Lihat Preview" button."""
    prospect = db.query(Prospect).filter(Prospect.id == prospect_id).first()
    if not prospect:
        raise HTTPException(status_code=404, detail="Prospect not found")

    score = db.query(ProspectScore).filter(ProspectScore.prospect_id == prospect_id).first()
    review = db.query(WebsiteReview).filter(WebsiteReview.prospect_id == prospect_id).first()

    llm = LLMProvider(db, provider)
    
    # We pass dicts to the prompt
    p_dict = {
        "name": prospect.name,
        "category": prospect.category,
        "city": prospect.city,
        "rating": prospect.rating,
        "review_count": prospect.review_count,
        "address": prospect.address,
        "phone_raw": prospect.phone_raw,
    }
    
    s_dict = {
        "relevant_keywords": score.relevant_keywords if score else "",
        "recommended_service": score.recommended_service if score else ""
    }
    
    r_dict = {
        "opportunity_notes": review.opportunity_notes if review else ""
    }

    messages = get_preview_content_prompt(p_dict, s_dict, r_dict)
    
    try:
        response_text = await llm.complete(messages)
        # Parse JSON
        clean = response_text.strip()
        if '```json' in clean:
            clean = clean.split('```json')[1].split('```')[0].strip()
        elif '```' in clean:
            clean = clean.split('```')[1].strip()
        
        content = json.loads(clean)
        
        # Save to database (we'll save it as JSON string in Prospect's notes or create a new field)
        # However, to keep schema changes minimal, let's inject it into `about_summary` 
        # or we can pass it via session/temporary cache. 
        # But wait, we can store it in the Prospect model if we add a preview_data column,
        # Or we can just use the DB to store it in WebsiteReview.website_summary?
        # A simpler way: just save it to `Prospect.about_summary` as a JSON string,
        # because the original code doesn't use `about_summary` extensively.
        
        prospect.about_summary = json.dumps(content)
        db.commit()
        
        return HTMLResponse(
            f'''
            <div class="text-green-600 text-sm font-medium p-3 bg-green-50 rounded-lg border border-green-200 mb-3 flex items-center gap-2">
                <i class="fa-solid fa-check-circle"></i> Preview berhasil di-generate!
            </div>
            <a href="/preview/view/{prospect.id}" target="_blank" class="w-full inline-flex items-center justify-center bg-indigo-600 hover:bg-indigo-700 text-white font-medium py-2 rounded-lg transition-colors text-sm gap-2">
                <i class="fa-solid fa-arrow-up-right-from-square"></i> Lihat Live Preview
            </a>
            '''
        )
    except Exception as e:
        logger.error(f"Failed to generate preview: {e}")
        return HTMLResponse(
            f'''
            <div class="text-red-600 text-sm font-medium p-3 bg-red-50 rounded-lg border border-red-200">
                <i class="fa-solid fa-xmark-circle"></i> Gagal generate: {str(e)}
            </div>
            '''
        )


@router.get("/view/{prospect_id}", response_class=HTMLResponse)
async def view_preview(request: Request, prospect_id: int, db: Session = Depends(get_db)):
    """Render the actual preview landing page using the generated data."""
    prospect = db.query(Prospect).filter(Prospect.id == prospect_id).first()
    if not prospect or not prospect.about_summary:
        return HTMLResponse("Preview data not found. Please generate it first.", status_code=404)

    try:
        data = json.loads(prospect.about_summary)
    except json.JSONDecodeError:
        data = {}

    # We also pass the app settings (Agency Profile) to make the footer look authentic
    settings_rows = db.query(AppSetting).all()
    app_settings = {r.key: r.value for r in settings_rows}

    return templates.TemplateResponse(
        request=request,
        name="preview/result.html",
        context={"request": request, "prospect": prospect, "data": data, "agency": app_settings}
    )
