"""Tests for database models."""
import tempfile
from datetime import datetime
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.backend.database import Account, Base, Budget, Debt, Transaction, TransactionCategory


@pytest.fixture
def db():
    """Create a test database."""
    db_file = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
    db_path = db_file.name
    db_file.close()

    engine = create_engine(f"sqlite:///{db_path}")
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    yield session

    session.close()
    Path(db_path).unlink()


def test_create_account(db):
    """Test creating an account."""
    account = Account(name="Checking", account_type="checking", balance=1000.0)
    db.add(account)
    db.commit()

    assert account.id is not None
    assert account.name == "Checking"
    assert account.balance == 1000.0


def test_create_transaction(db):
    """Test creating a transaction."""
    account = Account(name="Checking", account_type="checking", balance=1000.0)
    db.add(account)
    db.commit()

    txn = Transaction(
        account_id=account.id,
        amount=50.0,
        category=TransactionCategory.GROCERIES,
        description="Grocery shopping",
    )
    db.add(txn)
    db.commit()

    assert txn.id is not None
    assert txn.account_id == account.id
    assert txn.amount == 50.0


def test_create_budget(db):
    """Test creating a budget."""
    budget = Budget(
        category=TransactionCategory.GROCERIES,
        monthly_limit=500.0,
    )
    db.add(budget)
    db.commit()

    assert budget.id is not None
    assert budget.category == TransactionCategory.GROCERIES
    assert budget.monthly_limit == 500.0


def test_create_debt(db):
    """Test creating a debt."""
    debt = Debt(
        name="Student Loan",
        principal=10000.0,
        remaining=8000.0,
        interest_rate=5.0,
        monthly_payment=200.0,
    )
    db.add(debt)
    db.commit()

    assert debt.id is not None
    assert debt.name == "Student Loan"
    assert debt.remaining == 8000.0
    assert debt.monthly_payment == 200.0
