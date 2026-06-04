"""
Prospects route — list, filter, detail, and full CRUD for manual prospects.
"""
import logging
from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import templates
from app.models.prospect import Prospect, ProspectScore, Pipeline
from app.scraper.normalizer import DataNormalizer

logger = logging.getLogger(__name__)
router = APIRouter()


normalizer = DataNormalizer()

PIPELINE_STATUSES = [
    {"value": "belum_dihubungi", "label": "Belum Dihubungi"},
    {"value": "sudah_dihubungi", "label": "Sudah Dihubungi"},
    {"value": "perlu_followup", "label": "Perlu Follow-up"},
    {"value": "dibalas", "label": "Dibalas"},
    {"value": "deal", "label": "Deal"},
    {"value": "tidak_tertarik", "label": "Tidak Tertarik"},
]

CATEGORIES = [
    "Restoran", "Cafe", "Salon", "Klinik", "Hotel",
    "Toko", "Apotek", "Barbershop", "Gym", "Studio Foto",
    "Wedding Organizer", "Catering", "Jasa", "Lainnya"
]

def _prospect_to_card_dict(p: Prospect, s: ProspectScore = None) -> dict:
    return {
        "id": p.id,
        "name": p.name,
        "category": p.category,
        "city": p.city,
        "address": p.address,
        "rating": p.rating,
        "review_count": p.review_count,
        "phone_raw": p.phone_raw,
        "phone_normalized": p.phone_normalized,
        "website": p.website,
        "is_manual": getattr(p, 'is_manual', False),
        "priority_tier": s.priority_tier if s else None,
        "priority_score": s.priority_score if s else None,
    }

@router.get("/", response_class=HTMLResponse)
async def page_prospects(
    request: Request,
    page: int = 1,
    per_page: int = 20,
    db: Session = Depends(get_db),
):
    page = max(1, page)
    per_page = min(max(1, per_page), 100)  # clamp between 1-100
    offset = (page - 1) * per_page

    total = db.query(Prospect).count()
    prospects_q = db.query(Prospect, ProspectScore).outerjoin(
        ProspectScore, Prospect.id == ProspectScore.prospect_id
    ).offset(offset).limit(per_page).all()

    prospects = [_prospect_to_card_dict(p, s) for p, s in prospects_q]
    total_pages = (total + per_page - 1) // per_page

    return templates.TemplateResponse(
        request=request,
        name="prospects/list.html",
        context={
            "request": request,
            "prospects": prospects,
            "categories": CATEGORIES,
            "page": page,
            "per_page": per_page,
            "total": total,
            "total_pages": total_pages,
        },
    )

@router.get("/filter", response_class=HTMLResponse)
async def filter_prospects(
    request: Request,
    tier: str = "",
    category: str = "",
    status: str = "",
    search: str = "",
    page: int = 1,
    per_page: int = 20,
    db: Session = Depends(get_db),
):
    """Filter prospects — ALL parameters are combined (Item 13).
    The form in list.html wraps all controls so they are submitted together.
    """
    page = max(1, page)
    per_page = min(max(1, per_page), 100)
    offset = (page - 1) * per_page

    query = db.query(Prospect, ProspectScore, Pipeline).outerjoin(
        ProspectScore, Prospect.id == ProspectScore.prospect_id
    ).outerjoin(
        Pipeline, Prospect.id == Pipeline.prospect_id
    )

    # All active filters are applied simultaneously (Item 13)
    if tier:
        query = query.filter(ProspectScore.priority_tier == tier)
    if category:
        query = query.filter(Prospect.category == category)
    if status:
        if status in ("raw", "scored"):
            query = query.filter(Prospect.status == status)
        else:
            query = query.filter(Pipeline.contact_status == status)
    if search:
        query = query.filter(Prospect.name.ilike(f"%{search}%"))

    total = query.count()
    results = query.offset(offset).limit(per_page).all()
    total_pages = (total + per_page - 1) // per_page

    prospects = [_prospect_to_card_dict(p, s) for p, s, pl in results]

    return templates.TemplateResponse(
        request=request,
        name="prospects/list_partial.html",
        context={
            "request": request,
            "prospects": prospects,
            "page": page,
            "per_page": per_page,
            "total": total,
            "total_pages": total_pages,
            "tier": tier,
            "category": category,
            "status": status,
            "search": search,
        },
    )

@router.get("/new", response_class=HTMLResponse)
async def new_prospect_form(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="prospects/form.html",
        context={"request": request, "prospect": None, "categories": CATEGORIES, "edit_mode": False},
    )

@router.get("/{prospect_id}/edit", response_class=HTMLResponse)
async def edit_prospect_form(request: Request, prospect_id: int, db: Session = Depends(get_db)):
    prospect = db.query(Prospect).filter(Prospect.id == prospect_id).first()
    if not prospect:
        return RedirectResponse("/prospects", status_code=302)
    return templates.TemplateResponse(
        request=request,
        name="prospects/form.html",
        context={"request": request, "prospect": prospect, "categories": CATEGORIES, "edit_mode": True},
    )

@router.get("/{prospect_id}", response_class=HTMLResponse)
async def prospect_detail(request: Request, prospect_id: int, db: Session = Depends(get_db)):
from app.models.prospect import WebsiteReview, Message
    prospect = db.query(Prospect).filter(Prospect.id == prospect_id).first()
    if not prospect:
        return RedirectResponse("/prospects", status_code=302)

    score = db.query(ProspectScore).filter(ProspectScore.prospect_id == prospect_id).first()
    pipeline = db.query(Pipeline).filter(Pipeline.prospect_id == prospect_id).first()
    review = db.query(WebsiteReview).filter(WebsiteReview.prospect_id == prospect_id).first()
    message = db.query(Message).filter(
        Message.prospect_id == prospect_id, Message.status == "sent"
    ).order_by(Message.generated_at.desc()).first()

    return templates.TemplateResponse(
        request=request,
        name="prospects/detail.html",
        context={
            "request": request,
            "prospect": prospect,
            "score": score,
            "pipeline": pipeline,
            "review": review,
            "message": message,
            "pipeline_statuses": PIPELINE_STATUSES,
        },
    )

@router.post("/create", response_class=HTMLResponse)
async def create_prospect(
    request: Request,
    name: str = Form(...),
    category: str = Form(""),
    city: str = Form(""),
    address: str = Form(""),
    phone_raw: str = Form(""),
    website: str = Form(""),
    email: str = Form(""),
    instagram_url: str = Form(""),
    notes: str = Form(""),
    db: Session = Depends(get_db),
):
    phone_normalized = normalizer.normalize_phone(phone_raw) if phone_raw else None
    website_clean = normalizer.normalize_url(website) if website else None

    prospect = Prospect(
        name=name.strip(),
        category=category.strip() or "Lainnya",
        city=city.strip(),
        address=address.strip() or None,
        phone_raw=phone_raw.strip() or None,
        phone_normalized=phone_normalized,
        website=website_clean,
        instagram_url=instagram_url.strip() or None,
        status="raw",
        source_keyword="manual",
        source_city=city.strip(),
        place_id=f"manual_{name.strip().lower().replace(' ', '_')}_{city.strip().lower()}",
    )
    db.add(prospect)
    db.commit()
    db.refresh(prospect)

    logger.info(f"Created manual prospect: {prospect.name} (id={prospect.id})")
    return RedirectResponse(f"/prospects/{prospect.id}", status_code=302)

@router.post("/{prospect_id}/update", response_class=HTMLResponse)
async def update_prospect(
    request: Request,
    prospect_id: int,
    name: str = Form(...),
    category: str = Form(""),
    city: str = Form(""),
    address: str = Form(""),
    phone_raw: str = Form(""),
    website: str = Form(""),
    email: str = Form(""),
    instagram_url: str = Form(""),
    db: Session = Depends(get_db),
):
    prospect = db.query(Prospect).filter(Prospect.id == prospect_id).first()
    if not prospect:
        return RedirectResponse("/prospects", status_code=302)

    prospect.name = name.strip()
    prospect.category = category.strip() or prospect.category
    prospect.city = city.strip()
    prospect.address = address.strip() or None
    prospect.phone_raw = phone_raw.strip() or None
    prospect.phone_normalized = normalizer.normalize_phone(phone_raw) if phone_raw else prospect.phone_normalized
    prospect.website = normalizer.normalize_url(website) if website else None
    prospect.instagram_url = instagram_url.strip() or None

    db.commit()
    logger.info(f"Updated prospect id={prospect_id}")
    return RedirectResponse(f"/prospects/{prospect_id}", status_code=302)

@router.post("/{prospect_id}/delete", response_class=HTMLResponse)
async def delete_prospect(request: Request, prospect_id: int, db: Session = Depends(get_db)):
from app.models.prospect import ProspectScore, Pipeline, WebsiteReview, Message

    db.query(Message).filter(Message.prospect_id == prospect_id).delete()
    db.query(WebsiteReview).filter(WebsiteReview.prospect_id == prospect_id).delete()
    db.query(Pipeline).filter(Pipeline.prospect_id == prospect_id).delete()
    db.query(ProspectScore).filter(ProspectScore.prospect_id == prospect_id).delete()
    db.query(Prospect).filter(Prospect.id == prospect_id).delete()
    db.commit()

    logger.info(f"Deleted prospect id={prospect_id}")
    return RedirectResponse("/prospects", status_code=302)
