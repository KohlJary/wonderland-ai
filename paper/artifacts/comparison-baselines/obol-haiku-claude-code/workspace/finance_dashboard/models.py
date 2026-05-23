"""Data models for the finance dashboard."""
from datetime import datetime, date
from typing import Optional
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Date, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

Base = declarative_base()

class Account(Base):
    """User account for storing balances."""
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    account_type = Column(String, nullable=False)  # checking, savings, credit_card, loan
    balance = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)

    transactions = relationship("Transaction", back_populates="account", cascade="all, delete-orphan")
    budget_categories = relationship("BudgetCategory", back_populates="account", cascade="all, delete-orphan")
    debts = relationship("Debt", back_populates="account", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Account {self.name} ({self.account_type}): ${self.balance:.2f}>"


class Transaction(Base):
    """Financial transaction."""
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    amount = Column(Float, nullable=False)
    category = Column(String, nullable=False)
    description = Column(String)
    transaction_date = Column(Date, default=date.today)
    created_at = Column(DateTime, default=datetime.utcnow)

    account = relationship("Account", back_populates="transactions")

    def __repr__(self):
        return f"<Transaction {self.description}: ${self.amount:.2f} on {self.transaction_date}>"


class BudgetCategory(Base):
    """Budget category for tracking spending limits."""
    __tablename__ = "budget_categories"

    id = Column(Integer, primary_key=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    name = Column(String, nullable=False)
    monthly_limit = Column(Float, nullable=False)
    weekly_limit = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    account = relationship("Account", back_populates="budget_categories")

    def __repr__(self):
        return f"<BudgetCategory {self.name}: ${self.monthly_limit:.2f}/month>"


class Debt(Base):
    """Debt tracking with paydown progress."""
    __tablename__ = "debts"

    id = Column(Integer, primary_key=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    creditor_name = Column(String, nullable=False)
    original_amount = Column(Float, nullable=False)
    current_amount = Column(Float, nullable=False)
    interest_rate = Column(Float, default=0.0)  # percentage
    monthly_payment = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    account = relationship("Account", back_populates="debts")

    @property
    def paydown_progress(self) -> float:
        """Return paydown progress as percentage."""
        if self.original_amount == 0:
            return 0.0
        return ((self.original_amount - self.current_amount) / self.original_amount) * 100

    def __repr__(self):
        return f"<Debt to {self.creditor_name}: ${self.current_amount:.2f} ({self.paydown_progress:.1f}% paid)>"


def init_db(db_path: str = "finance.db") -> sessionmaker:
    """Initialize database and return session factory."""
    engine = create_engine(f"sqlite:///{db_path}")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)
