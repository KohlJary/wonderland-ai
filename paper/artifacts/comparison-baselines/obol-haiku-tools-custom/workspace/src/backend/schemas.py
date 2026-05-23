"""Pydantic schemas for API validation."""
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from src.backend.database import TransactionCategory


class AccountCreate(BaseModel):
    """Account creation schema."""
    name: str = Field(..., min_length=1, max_length=100)
    account_type: str = Field(..., pattern="^(checking|savings|credit_card)$")
    balance: float = Field(default=0.0, ge=0)


class AccountUpdate(BaseModel):
    """Account update schema."""
    balance: float = Field(..., ge=0)


class AccountResponse(BaseModel):
    """Account response schema."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    account_type: str
    balance: float
    created_at: datetime
    updated_at: datetime


class TransactionCreate(BaseModel):
    """Transaction creation schema."""
    account_id: int
    amount: float = Field(..., gt=0)
    category: TransactionCategory
    description: str = Field(..., min_length=1, max_length=255)
    date: datetime = Field(default_factory=datetime.utcnow)


class TransactionResponse(BaseModel):
    """Transaction response schema."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    account_id: int
    amount: float
    category: TransactionCategory
    description: str
    date: datetime
    created_at: datetime


class BudgetCreate(BaseModel):
    """Budget creation schema."""
    category: TransactionCategory
    monthly_limit: float = Field(..., gt=0)


class BudgetUpdate(BaseModel):
    """Budget update schema."""
    monthly_limit: float = Field(..., gt=0)


class BudgetResponse(BaseModel):
    """Budget response schema."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    category: TransactionCategory
    monthly_limit: float
    created_at: datetime
    updated_at: datetime


class DebtCreate(BaseModel):
    """Debt creation schema."""
    name: str = Field(..., min_length=1, max_length=100)
    principal: float = Field(..., gt=0)
    interest_rate: float = Field(default=0.0, ge=0, le=100)
    monthly_payment: float = Field(..., gt=0)
    description: str | None = None


class DebtUpdate(BaseModel):
    """Debt update schema."""
    remaining: float = Field(..., ge=0)
    monthly_payment: float = Field(..., gt=0)


class DebtResponse(BaseModel):
    """Debt response schema."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    principal: float
    remaining: float
    interest_rate: float
    monthly_payment: float
    description: str | None
    created_at: datetime
    updated_at: datetime
    paydown_progress: float

    @classmethod
    def from_orm(cls, debt):
        """Convert ORM model to schema with computed paydown_progress."""
        data = {
            "id": debt.id,
            "name": debt.name,
            "principal": debt.principal,
            "remaining": debt.remaining,
            "interest_rate": debt.interest_rate,
            "monthly_payment": debt.monthly_payment,
            "description": debt.description,
            "created_at": debt.created_at,
            "updated_at": debt.updated_at,
            "paydown_progress": max(0, min(100, ((debt.principal - debt.remaining) / debt.principal * 100))) if debt.principal > 0 else 0,
        }
        return cls(**data)


class MonthlyBudgetSummary(BaseModel):
    """Monthly budget summary schema."""
    category: TransactionCategory
    spent: float
    limit: float
    remaining: float
    percentage: float


class WeeklyBudgetSummary(BaseModel):
    """Weekly budget summary schema."""
    week_start: str
    week_end: str
    total_spent: float
    categories: dict[str, float]


class DashboardStats(BaseModel):
    """Dashboard statistics schema."""
    total_balance: float
    total_debt: float
    net_worth: float
    accounts_count: int
    transactions_count: int
