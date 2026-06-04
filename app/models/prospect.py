from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Date, ForeignKey
from sqlalchemy.sql import func
from app.core.database import Base

class Prospect(Base):
    __tablename__ = "prospects"

    id = Column(Integer, primary_key=True, index=True)
    place_id = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    category = Column(String)
    subcategory = Column(String)

    address = Column(String)
    city = Column(String)
    province = Column(String)
    latitude = Column(Float)
    longitude = Column(Float)
    google_maps_url = Column(String)

    phone_raw = Column(String)
    phone_normalized = Column(String)
    website = Column(String)
    email = Column(String)
    wa_valid = Column(Boolean, default=False)

    rating = Column(Float)
    review_count = Column(Integer)
    price_level = Column(String)

    hours = Column(String)
    is_open = Column(Boolean)
    is_permanently_closed = Column(Boolean, default=False)

    photo_urls = Column(String)
    total_photos = Column(Integer)

    scraped_at = Column(DateTime)
    source_keyword = Column(String)
    source_city = Column(String)
    status = Column(String, default="raw")

    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class ProspectScore(Base):
    __tablename__ = "prospect_scores"

    id = Column(Integer, primary_key=True, index=True)
    prospect_id = Column(Integer, ForeignKey("prospects.id"))
    priority_score = Column(Float)
    priority_tier = Column(String)
    score_reasoning = Column(String)
    recommended_service = Column(String)
    pitch_angle = Column(String)
    relevant_keywords = Column(String)
    scored_at = Column(DateTime, default=func.now())


class WebsiteReview(Base):
    __tablename__ = "website_reviews"

    id = Column(Integer, primary_key=True, index=True)
    prospect_id = Column(Integer, ForeignKey("prospects.id"))

    website_status = Column(String)
    is_mobile_friendly = Column(Boolean)
    has_ssl = Column(Boolean)
    has_ecommerce = Column(Boolean)
    has_booking = Column(Boolean)
    has_contact_form = Column(Boolean)
    speed_score = Column(Integer)
    design_quality_score = Column(Integer)
    website_issues = Column(String)
    website_summary = Column(String)

    manual_reviewed = Column(Boolean, default=False)
    manual_reviewed_at = Column(DateTime)
    opportunity_type = Column(String)
    opportunity_notes = Column(String)
    estimated_value = Column(String)
    urgency = Column(String)

    created_at = Column(DateTime, default=func.now())


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    prospect_id = Column(Integer, ForeignKey("prospects.id"))
    sequence = Column(Integer, default=0)
    content = Column(String)
    tone = Column(String)
    provider_used = Column(String)
    model_used = Column(String)
    generated_at = Column(DateTime, default=func.now())
    sent_at = Column(DateTime)
    status = Column(String, default="draft")


class Followup(Base):
    __tablename__ = "followups"

    id = Column(Integer, primary_key=True, index=True)
    prospect_id = Column(Integer, ForeignKey("prospects.id"))
    sequence = Column(Integer, default=1)
    scheduled_date = Column(Date)
    sent_at = Column(DateTime)
    status = Column(String, default="pending")
    notes = Column(String)
    created_at = Column(DateTime, default=func.now())


class Pipeline(Base):
    __tablename__ = "pipeline"

    id = Column(Integer, primary_key=True, index=True)
    prospect_id = Column(Integer, ForeignKey("prospects.id"))
    contact_status = Column(String, default="belum_dihubungi")
    contacted_at = Column(DateTime)
    last_followup_at = Column(DateTime)
    followup_count = Column(Integer, default=0)
    next_followup_date = Column(Date)
    is_blacklisted = Column(Boolean, default=False)
    blacklisted_at = Column(DateTime)
    blacklist_reason = Column(String)
    notes = Column(String)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class Preview(Base):
    __tablename__ = "previews"

    id = Column(Integer, primary_key=True, index=True)
    prospect_id = Column(Integer, ForeignKey("prospects.id"))
    file_path = Column(String)
    industry_template = Column(String)
    generated_at = Column(DateTime, default=func.now())
    expired_at = Column(Date)
    open_count = Column(Integer, default=0)
    last_opened_at = Column(DateTime)
    status = Column(String, default="active")


class LLMProvider(Base):
    __tablename__ = "llm_providers"

    id = Column(Integer, primary_key=True, index=True)
    provider_name = Column(String, nullable=False)
    api_key = Column(String, nullable=False)
    model_name = Column(String, nullable=False)
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
