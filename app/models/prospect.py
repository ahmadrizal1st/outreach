from datetime import datetime

from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Date, ForeignKey
from sqlalchemy.types import TypeDecorator
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from cryptography.fernet import Fernet
from app.core.database import Base
from app.core.config import settings

class EncryptedString(TypeDecorator):
    impl = String
    cache_ok = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not settings.ENCRYPTION_KEY:
            raise ValueError("ENCRYPTION_KEY is required for EncryptedString")
        self.fernet = Fernet(settings.ENCRYPTION_KEY)

    def process_bind_param(self, value, dialect):
        if value is not None:
            return self.fernet.encrypt(value.encode('utf-8')).decode('utf-8')
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            try:
                return self.fernet.decrypt(value.encode('utf-8')).decode('utf-8')
            except Exception:
                # Fallback untuk plain text lama
                return value
        return value

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
    instagram_url = Column(String)
    wa_valid = Column(Boolean, default=False)
    
    is_claimed = Column(Boolean, default=True)
    about_summary = Column(String)

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

    # Relationships
    score = relationship("ProspectScore", back_populates="prospect", uselist=False, cascade="all, delete-orphan")
    pipeline = relationship("Pipeline", back_populates="prospect", uselist=False, cascade="all, delete-orphan")
    website_review = relationship("WebsiteReview", back_populates="prospect", uselist=False, cascade="all, delete-orphan")
    messages = relationship("Message", back_populates="prospect", cascade="all, delete-orphan")
    followups = relationship("Followup", back_populates="prospect", cascade="all, delete-orphan")

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

    prospect = relationship("Prospect", back_populates="score")

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

    prospect = relationship("Prospect", back_populates="website_review")

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

    prospect = relationship("Prospect", back_populates="messages")

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

    prospect = relationship("Prospect", back_populates="followups")

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

    prospect = relationship("Prospect", back_populates="pipeline")

# Models moved to app/models/settings.py
