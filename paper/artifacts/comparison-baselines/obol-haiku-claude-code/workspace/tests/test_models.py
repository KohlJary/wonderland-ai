"""Tests for data models."""
import pytest
import tempfile
import os
from datetime import date
from finance_dashboard.models import init_db, Account, Transaction, BudgetCategory, Debt


@pytest.fixture
def temp_db():
    """Create a temporary database."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    session_maker = init_db(path)
    yield session_maker
    os.unlink(path)


@pytest.fixture
def session(temp_db):
    """Create a database session."""
    return temp_db()


def test_create_account(session):
    """Test account creation."""
    account = Account(name="Checking", account_type="checking", balance=1000.0)
    session.add(account)
    session.commit()

    retrieved = session.query(Account).filter(Account.name == "Checking").first()
    assert retrieved is not None
    assert retrieved.balance == 1000.0
    assert retrieved.account_type == "checking"


def test_account_relationships(session):
    """Test account relationships with transactions and budgets."""
    account = Account(name="Main", account_type="checking", balance=5000.0)
    session.add(account)
    session.flush()

    txn = Transaction(
        account_id=account.id,
        amount=-50.0,
        category="food",
        description="Groceries"
    )
    session.add(txn)
    session.commit()

    retrieved = session.query(Account).filter(Account.id == account.id).first()
    assert len(retrieved.transactions) == 1
    assert retrieved.transactions[0].category == "food"


def test_transaction_creation(session):
    """Test transaction creation."""
    account = Account(name="Test", account_type="checking", balance=1000.0)
    session.add(account)
    session.flush()

    txn = Transaction(
        account_id=account.id,
        amount=-25.50,
        category="dining",
        description="Restaurant"
    )
    session.add(txn)
    session.commit()

    retrieved = session.query(Transaction).filter(Transaction.id == txn.id).first()
    assert retrieved.amount == -25.50
    assert retrieved.description == "Restaurant"


def test_budget_category(session):
    """Test budget category."""
    account = Account(name="Test", account_type="checking")
    session.add(account)
    session.flush()

    budget = BudgetCategory(
        account_id=account.id,
        name="Groceries",
        monthly_limit=400.0,
        weekly_limit=100.0
    )
    session.add(budget)
    session.commit()

    retrieved = session.query(BudgetCategory).filter(BudgetCategory.id == budget.id).first()
    assert retrieved.name == "Groceries"
    assert retrieved.monthly_limit == 400.0


def test_debt_creation(session):
    """Test debt creation."""
    account = Account(name="Test", account_type="checking")
    session.add(account)
    session.flush()

    debt = Debt(
        account_id=account.id,
        creditor_name="Credit Card Inc",
        original_amount=5000.0,
        current_amount=3000.0,
        interest_rate=18.5,
        monthly_payment=150.0
    )
    session.add(debt)
    session.commit()

    retrieved = session.query(Debt).filter(Debt.id == debt.id).first()
    assert retrieved.creditor_name == "Credit Card Inc"
    assert retrieved.current_amount == 3000.0
    assert retrieved.interest_rate == 18.5


def test_debt_paydown_progress(session):
    """Test debt paydown progress calculation."""
    account = Account(name="Test", account_type="checking")
    session.add(account)
    session.flush()

    debt = Debt(
        account_id=account.id,
        creditor_name="Loan",
        original_amount=1000.0,
        current_amount=500.0,
        interest_rate=5.0,
        monthly_payment=50.0
    )
    session.add(debt)
    session.commit()

    assert debt.paydown_progress == 50.0


def test_account_deletion_cascades(session):
    """Test that deleting account cascades to transactions."""
    account = Account(name="Test", account_type="checking")
    session.add(account)
    session.flush()

    txn = Transaction(
        account_id=account.id,
        amount=-10.0,
        category="test",
        description="Test"
    )
    session.add(txn)
    session.commit()

    account_id = account.id
    session.delete(account)
    session.commit()

    retrieved = session.query(Account).filter(Account.id == account_id).first()
    assert retrieved is None

    txn_count = session.query(Transaction).filter(Transaction.account_id == account_id).count()
    assert txn_count == 0
