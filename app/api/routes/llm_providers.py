"""
LLM Providers CRUD route.
Handles create, read, update, delete, toggle, and test for LLM providers.
"""
import json
import logging
from datetime import datetime

from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
import os

from app.core.database import get_db
from app.models.prospect import LLMProvider

logger = logging.getLogger(__name__)
router = APIRouter()

templates_dir = os.path.join(os.path.dirname(__file__), "..", "..", "templates")
templates = Jinja2Templates(directory=templates_dir)

def _provider_to_dict(p: LLMProvider) -> dict:
    return {
        "id": p.id,
        "provider_name": p.provider_name,
        "display_name": p.display_name or p.provider_name,
        "api_key": p.api_key,
        "api_key_masked": (p.api_key[:6] + "..." + p.api_key[-4:]) if p.api_key and len(p.api_key) > 10 else p.api_key,
        "model_name": p.model_name,
        "base_url": p.base_url or "",
        "api_type": p.api_type or "openai",
        "extra_headers": p.extra_headers or "",
        "max_tokens": p.max_tokens or 1000,
        "temperature": p.temperature or 0.7,
        "notes": p.notes or "",
        "is_active": p.is_active,
        "is_available": p.is_available,
        "priority_order": p.priority_order or 1,
        "daily_token_limit": p.daily_token_limit,
        "tokens_used_today": p.tokens_used_today or 0,
        "last_used_at": p.last_used_at,
    }

@router.get("/", response_class=HTMLResponse)
async def list_providers(request: Request, db: Session = Depends(get_db)):
    """Render list of providers as HTML partial (used inside Settings tab)."""
    providers = db.query(LLMProvider).order_by(LLMProvider.priority_order).all()
    return templates.TemplateResponse(
        request=request,
        name="settings/providers_list.html",
        context={"request": request, "providers": [_provider_to_dict(p) for p in providers]},
    )

@router.post("/create", response_class=HTMLResponse)
async def create_provider(
    request: Request,
    provider_name: str = Form(...),
    display_name: str = Form(""),
    api_key: str = Form(...),
    model_name: str = Form(...),
    base_url: str = Form(""),
    api_type: str = Form("openai"),
    extra_headers: str = Form(""),
    max_tokens: int = Form(1000),
    temperature: float = Form(0.7),
    daily_token_limit: int = Form(None),
    priority_order: int = Form(1),
    notes: str = Form(""),
    db: Session = Depends(get_db),
):
    provider = LLMProvider(
        provider_name=provider_name.strip().lower(),
        display_name=display_name.strip() or provider_name.strip(),
        api_key=api_key.strip(),
        model_name=model_name.strip(),
        base_url=base_url.strip() or None,
        api_type=api_type.strip(),
        extra_headers=extra_headers.strip() or None,
        max_tokens=max_tokens,
        temperature=temperature,
        daily_token_limit=daily_token_limit if daily_token_limit else None,
        priority_order=priority_order,
        notes=notes.strip() or None,
        is_active=True,
        is_available=True,
        tokens_used_today=0,
    )
    db.add(provider)
    db.commit()
    db.refresh(provider)
    logger.info(f"Created LLM provider: {provider.provider_name}/{provider.model_name}")

    providers = db.query(LLMProvider).order_by(LLMProvider.priority_order).all()
    return templates.TemplateResponse(
        request=request,
        name="settings/providers_list.html",
        context={"request": request, "providers": [_provider_to_dict(p) for p in providers], "success": "Provider berhasil ditambahkan!"},
    )

@router.get("/{provider_id}/edit", response_class=HTMLResponse)
async def edit_provider_form(request: Request, provider_id: int, db: Session = Depends(get_db)):
    """Return edit form partial for the given provider."""
    provider = db.query(LLMProvider).filter(LLMProvider.id == provider_id).first()
    if not provider:
        return HTMLResponse("<p class='text-red-500'>Provider tidak ditemukan.</p>", status_code=404)
    return templates.TemplateResponse(
        request=request,
        name="settings/provider_form.html",
        context={"request": request, "provider": _provider_to_dict(provider), "edit_mode": True},
    )

@router.post("/{provider_id}/update", response_class=HTMLResponse)
async def update_provider(
    request: Request,
    provider_id: int,
    display_name: str = Form(""),
    api_key: str = Form(...),
    model_name: str = Form(...),
    base_url: str = Form(""),
    api_type: str = Form("openai"),
    extra_headers: str = Form(""),
    max_tokens: int = Form(1000),
    temperature: float = Form(0.7),
    daily_token_limit: int = Form(None),
    priority_order: int = Form(1),
    notes: str = Form(""),
    db: Session = Depends(get_db),
):
    provider = db.query(LLMProvider).filter(LLMProvider.id == provider_id).first()
    if not provider:
        return HTMLResponse("<p class='text-red-500'>Provider tidak ditemukan.</p>", status_code=404)

    provider.display_name = display_name.strip() or provider.provider_name
    provider.api_key = api_key.strip()
    provider.model_name = model_name.strip()
    provider.base_url = base_url.strip() or None
    provider.api_type = api_type.strip()
    provider.extra_headers = extra_headers.strip() or None
    provider.max_tokens = max_tokens
    provider.temperature = temperature
    provider.daily_token_limit = daily_token_limit if daily_token_limit else None
    provider.priority_order = priority_order
    provider.notes = notes.strip() or None

    db.commit()
    logger.info(f"Updated LLM provider id={provider_id}")

    providers = db.query(LLMProvider).order_by(LLMProvider.priority_order).all()
    return templates.TemplateResponse(
        request=request,
        name="settings/providers_list.html",
        context={"request": request, "providers": [_provider_to_dict(p) for p in providers], "success": "Provider berhasil diupdate!"},
    )

@router.post("/{provider_id}/delete", response_class=HTMLResponse)
async def delete_provider(request: Request, provider_id: int, db: Session = Depends(get_db)):
    provider = db.query(LLMProvider).filter(LLMProvider.id == provider_id).first()
    if provider:
        db.delete(provider)
        db.commit()
        logger.info(f"Deleted LLM provider id={provider_id}")

    providers = db.query(LLMProvider).order_by(LLMProvider.priority_order).all()
    return templates.TemplateResponse(
        request=request,
        name="settings/providers_list.html",
        context={"request": request, "providers": [_provider_to_dict(p) for p in providers], "success": "Provider dihapus."},
    )

@router.post("/{provider_id}/toggle", response_class=HTMLResponse)
async def toggle_provider(request: Request, provider_id: int, db: Session = Depends(get_db)):
    provider = db.query(LLMProvider).filter(LLMProvider.id == provider_id).first()
    if not provider:
        return HTMLResponse("", status_code=404)

    provider.is_active = not provider.is_active
    db.commit()

    providers = db.query(LLMProvider).order_by(LLMProvider.priority_order).all()
    return templates.TemplateResponse(
        request=request,
        name="settings/providers_list.html",
        context={"request": request, "providers": [_provider_to_dict(p) for p in providers]},
    )

@router.post("/test", response_class=HTMLResponse)
async def test_provider(
    request: Request,
    provider_name: str = Form(...),
    api_key: str = Form(...),
    model_name: str = Form(...),
    base_url: str = Form(""),
    api_type: str = Form("openai"),
    db: Session = Depends(get_db),
):
    """Test a provider configuration without saving it."""
    from litellm import completion as llm_completion
    try:
        kwargs = {
            "model": f"{provider_name}/{model_name}",
            "messages": [{"role": "user", "content": "Reply with exactly: OK"}],
            "api_key": api_key,
            "max_tokens": 10,
            "temperature": 0,
        }
        if base_url:
            kwargs["base_url"] = base_url

        response = llm_completion(**kwargs)
        reply = response.choices[0].message.content.strip()
        return HTMLResponse(
            f'<div class="text-green-600 text-sm font-medium p-2 bg-green-50 rounded-lg border border-green-200">'
            f'<i class="fa-solid fa-check-circle"></i> Koneksi berhasil! Response: "{reply}"</div>'
        )
    except Exception as e:
        return HTMLResponse(
            f'<div class="text-red-600 text-sm font-medium p-2 bg-red-50 rounded-lg border border-red-200">'
            f'<i class="fa-solid fa-xmark-circle"></i> Koneksi gagal: {str(e)[:200]}</div>'
        )
