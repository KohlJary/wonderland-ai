"""Tests for database access layer."""
import pytest
import tempfile
import os
from datetime import date, timedelta
from finance_dashboard.models import init_db
from finance_dashboard.db import FinanceDB


@pytest.fixture
def temp_db():
    """Create a temporary database."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    session_maker = init_db(path)
    yield session_maker
    os.unlink(path)


@pytest.fixture
def db(temp_db):
    """Create a database access layer."""
    session = temp_db()
    return FinanceDB(session)


def test_create_account(db):
    """Test account creation."""
    account = db.create_account("Checking", "checking", 1000.0)
    assert account.name == "Checking"
    assert account.balance == 1000.0
    assert account.account_type == "checking"


def test_get_account(db):
    """Test retrieving account."""
    created = db.create_account("Savings", "savings", 5000.0)
    retrieved = db.get_account(created.id)
    assert retrieved.name == "Savings"
    assert retrieved.balance == 5000.0


def test_get_account_by_name(db):
    """Test retrieving account by name."""
    db.create_account("Main", "checking", 2000.0)
    account = db.get_account_by_name("Main")
    assert account is not None
    assert account.balance == 2000.0


def test_list_accounts(db):
    """Test listing accounts."""
    db.create_account("Account1", "checking", 1000.0)
    db.create_account("Account2", "savings", 5000.0)
    accounts = db.list_accounts()
    assert len(accounts) == 2


def test_add_transaction(db):
    """Test adding transaction."""
    account = db.create_account("Test", "checking", 100.0)
    txn = db.add_transaction(account.id, -25.0, "food", "Groceries")
    assert txn.amount == -25.0
    assert txn.category == "food"

    # Check balance was updated
    updated = db.get_account(account.id)
    assert updated.balance == 75.0


def test_get_transactions(db):
    """Test retrieving transactions."""
    account = db.create_account("Test", "checking", 1000.0)
    db.add_transaction(account.id, -50.0, "food", "Restaurant")
    db.add_transaction(account.id, 100.0, "income", "Paycheck")
    db.add_transaction(account.id, -25.0, "transport", "Gas")

    txns = db.get_transactions(account.id)
    assert len(txns) == 3


def test_get_transactions_by_category(db):
    """Test retrieving transactions by category."""
    account = db.create_account("Test", "checking", 1000.0)
    db.add_transaction(account.id, -50.0, "food", "Restaurant")
    db.add_transaction(account.id, -60.0, "food", "Groceries")
    db.add_transaction(account.id, -25.0, "transport", "Gas")

    food_txns = db.get_transactions_by_category(account.id, "food")
    assert len(food_txns) == 2
    assert all(t.category == "food" for t in food_txns)


def test_delete_transaction(db):
    """Test deleting transaction."""
    account = db.create_account("Test", "checking", 100.0)
    txn = db.add_transaction(account.id, -25.0, "food", "Groceries")
    initial_balance = account.balance

    db.delete_transaction(txn.id)
    updated = db.get_account(account.id)
    assert updated.balance == initial_balance + 25.0


def test_create_budget_category(db):
    """Test creating budget category."""
    account = db.create_account("Test", "checking", 1000.0)
    category = db.create_budget_category(account.id, "Dining", 200.0, 50.0)
    assert category.name == "Dining"
    assert category.monthly_limit == 200.0
    assert category.weekly_limit == 50.0


def test_get_budget_categories(db):
    """Test listing budget categories."""
    account = db.create_account("Test", "checking", 1000.0)
    db.create_budget_category(account.id, "Food", 400.0, 100.0)
    db.create_budget_category(account.id, "Transport", 200.0, 50.0)

    categories = db.get_budget_categories(account.id)
    assert len(categories) == 2


def test_get_spending_summary(db):
    """Test spending summary calculation."""
    account = db.create_account("Test", "checking", 1000.0)
    db.create_budget_category(account.id, "Food", 400.0, 100.0)

    # Add transactions this week
    db.add_transaction(account.id, -30.0, "Food", "Groceries")
    db.add_transaction(account.id, -20.0, "Food", "Restaurant")

    weekly, monthly = db.get_spending_summary(account.id, "Food")
    assert weekly == 50.0
    assert monthly == 50.0


def test_spending_summary_with_old_transactions(db):
    """Test spending summary excludes old transactions."""
    account = db.create_account("Test", "checking", 1000.0)
    db.create_budget_category(account.id, "Food", 400.0, 100.0)

    # Add recent transaction
    db.add_transaction(account.id, -30.0, "Food", "Recent")

    # Add old transaction (last month)
    old_date = date.today().replace(day=1) - timedelta(days=1)
    db.add_transaction(account.id, -100.0, "Food", "Old", old_date)

    weekly, monthly = db.get_spending_summary(account.id, "Food")
    assert weekly == 30.0  # Only recent
    assert monthly == 30.0  # Only current month


def test_create_debt(db):
    """Test creating debt."""
    account = db.create_account("Test", "checking", 1000.0)
    debt = db.create_debt(
        account.id,
        "Credit Card Inc",
        5000.0,
        3000.0,
        18.5,
        150.0
    )
    assert debt.creditor_name == "Credit Card Inc"
    assert debt.current_amount == 3000.0


def test_get_debts(db):
    """Test listing debts."""
    account = db.create_account("Test", "checking", 1000.0)
    db.create_debt(account.id, "Card1", 5000.0, 3000.0, 18.5, 150.0)
    db.create_debt(account.id, "Card2", 2000.0, 1500.0, 15.0, 100.0)

    debts = db.get_debts(account.id)
    assert len(debts) == 2


def test_update_debt(db):
    """Test updating debt amount."""
    account = db.create_account("Test", "checking", 1000.0)
    debt = db.create_debt(account.id, "Loan", 1000.0, 900.0, 5.0, 50.0)

    db.update_debt(debt.id, 800.0)
    updated = db.get_debt(debt.id)
    assert updated.current_amount == 800.0


def test_get_total_debt(db):
    """Test total debt calculation."""
    account = db.create_account("Test", "checking", 1000.0)
    db.create_debt(account.id, "Card1", 5000.0, 2000.0, 18.5, 150.0)
    db.create_debt(account.id, "Card2", 2000.0, 500.0, 15.0, 100.0)

    total = db.get_total_debt(account.id)
    assert total == 2500.0


def test_delete_debt(db):
    """Test deleting debt."""
    account = db.create_account("Test", "checking", 1000.0)
    debt = db.create_debt(account.id, "Loan", 1000.0, 900.0, 5.0, 50.0)

    db.delete_debt(debt.id)
    retrieved = db.get_debt(debt.id)
    assert retrieved is None


def test_update_account_balance(db):
    """Test updating account balance."""
    account = db.create_account("Test", "checking", 100.0)
    db.update_account_balance(account.id, 500.0)

    updated = db.get_account(account.id)
    assert updated.balance == 500.0


def test_delete_account(db):
    """Test deleting account."""
    account = db.create_account("Test", "checking", 1000.0)
    account_id = account.id

    db.delete_account(account_id)
    retrieved = db.get_account(account_id)
    assert retrieved is None
