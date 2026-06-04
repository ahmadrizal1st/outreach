import random
from datetime import date
from litellm import completion
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, asc

from app.models.prospect import LLMProvider as LLMProviderModel

class LLMProvider:
    def __init__(self, db: Session, manual_provider: str = None):
        self.db = db
        self.manual_provider = manual_provider
        self.last_used_provider = None
        self.last_used_model = None

    def get_active_provider(self):
        if self.manual_provider:
            return self._get_provider(self.manual_provider)
        return self._get_auto_provider()

    def _get_auto_provider(self):
        # Reset token harian jika hari baru
        self._reset_daily_tokens_if_needed()

        # Ambil semua provider yang masih available
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

        # Pilih random dari yang available jika ada yang prioritasnya sama, tapi karena order_by, kita bisa ambil yang prioritas teratas
        # Tapi berdasarkan specs, random dari yang available? Kita pakai choice untuk saat ini atau ambil yang pertama.
        # "Pilih random dari yang available"
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
            response = completion(
                model=f"{provider.provider_name}/{provider.model_name}",
                messages=messages,
                api_key=provider.api_key,
                temperature=0.7,
                max_tokens=1000
            )

            # Update token usage
            tokens_used = response.usage.total_tokens
            self._update_token_usage(provider.id, tokens_used)

            return response.choices[0].message.content

        except Exception as e:
            # Mark provider unavailable & fallback
            self._mark_unavailable(provider.id)
            return await self._fallback(messages)

    async def _fallback(self, messages: list):
        # Coba provider lain
        provider = self._get_auto_provider()
        if not provider:
            raise Exception("Tidak ada provider yang tersedia untuk fallback")

        self.last_used_provider = provider.provider_name
        self.last_used_model = provider.model_name

        response = completion(
            model=f"{provider.provider_name}/{provider.model_name}",
            messages=messages,
            api_key=provider.api_key,
            temperature=0.7,
            max_tokens=1000
        )
        
        tokens_used = response.usage.total_tokens
        self._update_token_usage(provider.id, tokens_used)

        return response.choices[0].message.content

    def _update_token_usage(self, provider_id: int, tokens: int):
        provider = self.db.query(LLMProviderModel).filter(LLMProviderModel.id == provider_id).first()
        if provider:
            if provider.tokens_used_today is None:
                provider.tokens_used_today = 0
            provider.tokens_used_today += tokens
            from datetime import datetime
            provider.last_used_at = datetime.utcnow()
            self.db.commit()

    def _mark_unavailable(self, provider_id: int):
        provider = self.db.query(LLMProviderModel).filter(LLMProviderModel.id == provider_id).first()
        if provider:
            provider.is_available = False
            self.db.commit()

    def _reset_daily_tokens_if_needed(self):
        from datetime import date
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
