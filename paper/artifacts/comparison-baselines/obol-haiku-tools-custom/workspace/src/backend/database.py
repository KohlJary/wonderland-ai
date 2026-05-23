"""Database models and initialization."""
from datetime import datetime
from decimal import Decimal
from enum import Enum
from pathlib import Path

from sqlalchemy import (
    Column,
    DateTime,
    Enum as SQLEnum,
    Float,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()

DATABASE_PATH = Path(__file__).parent.parent.parent / "finance.db"
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"


class TransactionCategory(str, Enum):
    """Transaction category enumeration."""
    INCOME = "income"
    GROCERIES = "groceries"
    DINING = "dining"
    TRANSPORTATION = "transportation"
    UTILITIES = "utilities"
    ENTERTAINMENT = "entertainment"
    HEALTHCARE = "healthcare"
    SHOPPING = "shopping"
    DEBT_PAYMENT = "debt_payment"
    SAVINGS = "savings"
    OTHER = "other"


class Account(Base):
    """Account model."""
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    account_type = Column(String(50), nullable=False)  # checking, savings, credit_card
    balance = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Transaction(Base):
    """Transaction model."""
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True)
    account_id = Column(Integer, nullable=False)
    amount = Column(Float, nullable=False)
    category = Column(SQLEnum(TransactionCategory), nullable=False)
    description = Column(String(255), nullable=False)
    date = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)


class Budget(Base):
    """Budget model."""
    __tablename__ = "budgets"

    id = Column(Integer, primary_key=True)
    category = Column(SQLEnum(TransactionCategory), nullable=False, unique=True)
    monthly_limit = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Debt(Base):
    """Debt tracking model."""
    __tablename__ = "debts"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    principal = Column(Float, nullable=False)
    remaining = Column(Float, nullable=False)
    interest_rate = Column(Float, default=0.0)
    monthly_payment = Column(Float, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


def get_engine():
    """Create database engine."""
    return create_engine(DATABASE_URL, echo=False)


def get_session_factory():
    """Create session factory."""
    engine = get_engine()
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Initialize database tables."""
    engine = get_engine()
    Base.metadata.create_all(bind=engine)


def get_db():
    """Get database session."""
    SessionLocal = get_session_factory()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
