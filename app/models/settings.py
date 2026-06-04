from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Date
from sqlalchemy.sql import func
from app.core.database import Base
from app.models.prospect import EncryptedString

class LLMProvider(Base):
    __tablename__ = "llm_providers"

    id = Column(Integer, primary_key=True, index=True)
    provider_name = Column(String, nullable=False)
    display_name = Column(String)
    api_key = Column(EncryptedString, nullable=False)
    model_name = Column(String, nullable=False)
    base_url = Column(String)
    api_type = Column(String, default="openai")
    extra_headers = Column(String)
    max_tokens = Column(Integer, default=1000)
    temperature = Column(Float, default=0.7)
    notes = Column(String)
    is_active = Column(Boolean, default=True)
    priority_order = Column(Integer, default=1)
    daily_token_limit = Column(Integer)
    tokens_used_today = Column(Integer, default=0)
    last_used_at = Column(DateTime)
    last_reset_at = Column(Date)
    is_available = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())

class ScraperConfig(Base):
    __tablename__ = "scraper_config"

    id = Column(Integer, primary_key=True, index=True)
    keywords = Column(String)
    target_categories = Column(String)
    target_cities = Column(String)
    max_per_day = Column(Integer, default=20)
    delay_min_seconds = Column(Integer, default=3)
    delay_max_seconds = Column(Integer, default=7)
    is_active = Column(Boolean, default=True)
    last_run_at = Column(DateTime)
    created_at = Column(DateTime, default=func.now())

class ScraperProgress(Base):
    __tablename__ = "scraper_progress"

    id = Column(Integer, primary_key=True, index=True)
    keyword = Column(String)
    city = Column(String)
    total_found = Column(Integer, default=0)
    total_saved = Column(Integer, default=0)
    scraped_at = Column(DateTime, default=func.now())
    status = Column(String, default="completed")

class ScraperSession(Base):
    """Log detail per sesi scraping (Item 46)."""
    __tablename__ = "scraper_sessions"

    id = Column(Integer, primary_key=True, index=True)
    started_at = Column(DateTime, default=func.now())
    completed_at = Column(DateTime)
    status = Column(String, default="running")
    total_processed = Column(Integer, default=0)
    total_saved = Column(Integer, default=0)
    error_message = Column(String)

class AppSetting(Base):
    """Key-value store untuk konfigurasi aplikasi yang bisa diubah dari UI."""
    __tablename__ = "app_settings"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, nullable=False, index=True)
    value = Column(String)
    description = Column(String)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
