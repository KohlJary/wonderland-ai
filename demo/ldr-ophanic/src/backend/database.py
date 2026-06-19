"""
SQLAlchemy ORM models and database configuration.
"""
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Integer, ForeignKey, Index, Float, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class User(Base):
    """
    User account model.
    
    Invariants enforced:
    - email is UNIQUE (constraint in DB)
    - id is stable across password changes, profile updates
    - created_at is immutable (set on creation, never updated)
    - password_hash is never exposed in API responses
    """
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    partner_profile = relationship(
        "PartnerProfile",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )
    
    def __repr__(self):
        return f"<User id={self.id} email={self.email}>"


class PartnerProfile(Base):
    """
    User's partner profile (one-to-one with User for v1).
    
    Invariants enforced:
    - user_id is UNIQUE (one user, one partner profile)
    - user_id is NOT NULL (profile always belongs to a user)
    - city + country identify the partner's location
    - timezone, lat, lon are resolved from city+country (server-side)
    """
    __tablename__ = "partner_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), 
                     nullable=False, unique=True, index=True)
    display_name = Column(String(255), nullable=False)
    city = Column(String(255), nullable=False)
    country = Column(String(255), nullable=False)
    timezone = Column(String(64), nullable=True)  # IANA timezone string
    latitude = Column(String(20), nullable=True)  # Decimal as string for precision
    longitude = Column(String(20), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="partner_profile")
    
    def __repr__(self):
        return f"<PartnerProfile id={self.id} user_id={self.user_id} city={self.city}>"


class WeatherCache(Base):
    """
    Cached weather data for partner locations, populated by hourly polling job.
    
    Invariants enforced:
    - user_id is NOT NULL (cache belongs to a user)
    - user_id is UNIQUE (one cache entry per user)
    - temperature_f is a float, can be null only if fetch failed
    - cached_at is immutable (set at cache time, never updated)
    - condition_code and condition_description are always set together
    """
    __tablename__ = "weather_cache"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), 
                     nullable=False, unique=True, index=True)
    temperature_f = Column(Float, nullable=True)  # Nullable if fetch failed
    condition_code = Column(Integer, nullable=True)  # WMO weather code from Open-Meteo
    condition_description = Column(String(255), nullable=True)  # Human-readable description
    cached_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    last_fetch_attempt_at = Column(DateTime, nullable=True)  # Track when we last tried to fetch
    last_successful_fetch_at = Column(DateTime, nullable=True)  # Track when we last successfully fetched
    
    def __repr__(self):
        return f"<WeatherCache id={self.id} user_id={self.user_id} temp={self.temperature_f}>"


class NewsCache(Base):
    """
    Cached news headlines for partner locations, populated by daily polling job.
    
    Stores parsed headlines from Austrian RSS feeds (Der Standard + ORF).
    Each row holds up to 6 headlines (3 per feed).
    
    Invariants enforced:
    - user_id is NOT NULL (cache belongs to a user)
    - user_id is UNIQUE (one cache entry per user)
    - headlines_json stores array of {title, url, source} objects as JSON
    - cached_at is immutable (set at cache time, never updated)
    - last_successful_fetch_at tracks successful fetch (feeds may differ between attempts)
    """
    __tablename__ = "news_cache"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), 
                     nullable=False, unique=True, index=True)
    headlines_json = Column(Text, nullable=True)  # JSON-serialized list of headlines
    cached_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    last_fetch_attempt_at = Column(DateTime, nullable=True)  # Track when we last tried to fetch
    last_successful_fetch_at = Column(DateTime, nullable=True)  # Track when we last successfully fetched
    
    def __repr__(self):
        return f"<NewsCache id={self.id} user_id={self.user_id}>"
