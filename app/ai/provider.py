from datetime import datetime
import json as _json
import random
from datetime import date
from litellm import completion
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, asc

from app.models.settings import LLMProvider as LLMProviderModel, AppSetting

class LLMProvider:
    def __init__(self, db: Session, manual_provider: str = None):
        self.db = db
        self.manual_provider = manual_provider
        self.last_used_provider = None
        self.last_used_model = None

    def get_active_provider(self):
        # Override dengan parameter function jika ada
        if self.manual_provider:
            return self._get_provider(self.manual_provider)

        # Jika tidak, baca dari AppSetting
        mode_setting = self.db.query(AppSetting).filter(AppSetting.key == "llm_mode").first()
        llm_mode = mode_setting.value if mode_setting else "auto"

        if llm_mode == "manual":
            provider_setting = self.db.query(AppSetting).filter(AppSetting.key == "manual_provider_id").first()
            if provider_setting and provider_setting.value:
                provider = self.db.query(LLMProviderModel).filter(LLMProviderModel.id == int(provider_setting.value)).first()
                if provider and provider.is_active:
                    return provider
        
        # Fallback ke auto
        return self._get_auto_provider()

    def _get_auto_provider(self):
        
        self._reset_daily_tokens_if_needed()

        providers = self.db.query(LLMProviderModel).filter(
            LLMProviderModel.is_active == True,
            LLMProviderModel.is_available == True,
            or_(
                LLMProviderModel.daily_token_limit == None,
                LLMProviderModel.tokens_used_today < LLMProviderModel.daily_token_limit
            )
        ).order_by(asc(LLMProviderModel.priority_order)).all()

        if not providers:
            raise Exception("Semua provider habis quota hari ini")

        return random.choice(providers)

    def _get_provider(self, name: str):
        provider = self.db.query(LLMProviderModel).filter(
            LLMProviderModel.provider_name == name,
            LLMProviderModel.is_active == True
        ).first()

        if not provider:
            raise Exception(f"Provider {name} tidak ditemukan")
        return provider

    async def complete(self, messages: list):
        provider = self.get_active_provider()
        self.last_used_provider = provider.provider_name
        self.last_used_model = provider.model_name

        try:
            extra_headers = {}
            if provider.extra_headers:
                try:
                    extra_headers = _json.loads(provider.extra_headers)
                except Exception:
                    pass

            kwargs = {
                "model": f"{provider.provider_name}/{provider.model_name}",
                "messages": messages,
                "api_key": provider.api_key,
                "temperature": provider.temperature or 0.7,
                "max_tokens": provider.max_tokens or 1000,
            }

            if provider.base_url:
                kwargs["base_url"] = provider.base_url

            if extra_headers:
                kwargs["extra_headers"] = extra_headers

            response = completion(**kwargs)

            tokens_used = response.usage.total_tokens if response.usage else 0
            self._update_token_usage(provider.id, tokens_used)

            return response.choices[0].message.content

        except Exception as e:
            
            self._mark_unavailable(provider.id)
            return await self._fallback(messages, exclude_id=provider.id)

    async def _fallback(self, messages: list, exclude_id: int = None):
        """Try another provider when the primary fails."""
        
        query = self.db.query(LLMProviderModel).filter(
            LLMProviderModel.is_active == True,
            LLMProviderModel.is_available == True,
        )
        if exclude_id:
            query = query.filter(LLMProviderModel.id != exclude_id)

        provider = query.order_by(asc(LLMProviderModel.priority_order)).first()
        if not provider:
            raise Exception("Tidak ada provider yang tersedia untuk fallback")

        self.last_used_provider = provider.provider_name
        self.last_used_model = provider.model_name

        extra_headers = {}
        if provider.extra_headers:
            try:
                extra_headers = _json.loads(provider.extra_headers)
            except Exception:
                pass

        kwargs = {
            "model": f"{provider.provider_name}/{provider.model_name}",
            "messages": messages,
            "api_key": provider.api_key,
            "temperature": provider.temperature or 0.7,
            "max_tokens": provider.max_tokens or 1000,
        }
        if provider.base_url:
            kwargs["base_url"] = provider.base_url
        if extra_headers:
            kwargs["extra_headers"] = extra_headers

        response = completion(**kwargs)

        tokens_used = response.usage.total_tokens if response.usage else 0
        self._update_token_usage(provider.id, tokens_used)

        return response.choices[0].message.content

    def _update_token_usage(self, provider_id: int, tokens: int):
        provider = self.db.query(LLMProviderModel).filter(LLMProviderModel.id == provider_id).first()
        if provider:
            if provider.tokens_used_today is None:
                provider.tokens_used_today = 0
            provider.tokens_used_today += tokens
            provider.last_used_at = datetime.utcnow()
            self.db.commit()

    def _mark_unavailable(self, provider_id: int):
        provider = self.db.query(LLMProviderModel).filter(LLMProviderModel.id == provider_id).first()
        if provider:
            provider.is_available = False
            self.db.commit()

    def _reset_daily_tokens_if_needed(self):
        today = date.today()
        
        providers = self.db.query(LLMProviderModel).filter(
            or_(
                LLMProviderModel.last_reset_at < today,
                LLMProviderModel.last_reset_at == None
            )
        ).all()
        
        for provider in providers:
            provider.tokens_used_today = 0
            provider.is_available = True
            provider.last_reset_at = today
            
        if providers:
            self.db.commit()
