"""Tests for business logic services."""
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.backend.database import Account, Base, Budget, Debt, Transaction, TransactionCategory
from src.backend.services import (
    AccountService,
    BudgetService,
    DebtService,
    TransactionService,
)


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


class TestAccountService:
    """Test AccountService."""

    def test_create_account(self, db):
        """Test creating an account."""
        account = AccountService.create_account(db, "Checking", "checking", 1000.0)
        assert account.id is not None
        assert account.name == "Checking"
        assert account.balance == 1000.0

    def test_get_account(self, db):
        """Test retrieving an account."""
        created = AccountService.create_account(db, "Checking", "checking", 1000.0)
        retrieved = AccountService.get_account(db, created.id)
        assert retrieved.id == created.id
        assert retrieved.balance == 1000.0

    def test_get_all_accounts(self, db):
        """Test retrieving all accounts."""
        AccountService.create_account(db, "Checking", "checking", 1000.0)
        AccountService.create_account(db, "Savings", "savings", 5000.0)
        accounts = AccountService.get_all_accounts(db)
        assert len(accounts) == 2

    def test_update_account_balance(self, db):
        """Test updating account balance."""
        account = AccountService.create_account(db, "Checking", "checking", 1000.0)
        updated = AccountService.update_account_balance(db, account.id, 1500.0)
        assert updated.balance == 1500.0

    def test_get_total_balance(self, db):
        """Test getting total balance."""
        AccountService.create_account(db, "Checking", "checking", 1000.0)
        AccountService.create_account(db, "Savings", "savings", 5000.0)
        total = AccountService.get_total_balance(db)
        assert total == 6000.0


class TestTransactionService:
    """Test TransactionService."""

    def test_create_income_transaction(self, db):
        """Test creating an income transaction."""
        account = AccountService.create_account(db, "Checking", "checking", 0.0)
        txn = TransactionService.create_transaction(
            db,
            account.id,
            1000.0,
            TransactionCategory.INCOME,
            "Salary",
        )
        assert txn.amount == 1000.0
        # Check account balance updated
        updated = AccountService.get_account(db, account.id)
        assert updated.balance == 1000.0

    def test_create_expense_transaction(self, db):
        """Test creating an expense transaction."""
        account = AccountService.create_account(db, "Checking", "checking", 1000.0)
        txn = TransactionService.create_transaction(
            db,
            account.id,
            50.0,
            TransactionCategory.GROCERIES,
            "Groceries",
        )
        assert txn.amount == 50.0
        # Check account balance updated
        updated = AccountService.get_account(db, account.id)
        assert updated.balance == 950.0

    def test_get_all_transactions(self, db):
        """Test retrieving all transactions."""
        account = AccountService.create_account(db, "Checking", "checking", 1000.0)
        TransactionService.create_transaction(
            db, account.id, 50.0, TransactionCategory.GROCERIES, "Groceries"
        )
        TransactionService.create_transaction(
            db, account.id, 20.0, TransactionCategory.DINING, "Dinner"
        )
        txns = TransactionService.get_all_transactions(db)
        assert len(txns) == 2

    def test_get_account_transactions(self, db):
        """Test retrieving account transactions."""
        acc1 = AccountService.create_account(db, "Checking", "checking", 1000.0)
        acc2 = AccountService.create_account(db, "Savings", "savings", 5000.0)
        TransactionService.create_transaction(
            db, acc1.id, 50.0, TransactionCategory.GROCERIES, "Groceries"
        )
        TransactionService.create_transaction(
            db, acc2.id, 100.0, TransactionCategory.UTILITIES, "Electric"
        )
        txns = TransactionService.get_account_transactions(db, acc1.id)
        assert len(txns) == 1
        assert txns[0].account_id == acc1.id

    def test_get_transactions_by_month(self, db):
        """Test retrieving transactions by month."""
        account = AccountService.create_account(db, "Checking", "checking", 1000.0)
        now = datetime.utcnow()
        TransactionService.create_transaction(
            db,
            account.id,
            50.0,
            TransactionCategory.GROCERIES,
            "Groceries",
            now,
        )
        txns = TransactionService.get_transactions_by_month(db, now.year, now.month)
        assert len(txns) == 1


class TestBudgetService:
    """Test BudgetService."""

    def test_create_budget(self, db):
        """Test creating a budget."""
        budget = BudgetService.create_budget(db, TransactionCategory.GROCERIES, 500.0)
        assert budget.category == TransactionCategory.GROCERIES
        assert budget.monthly_limit == 500.0

    def test_get_budget(self, db):
        """Test retrieving a budget."""
        created = BudgetService.create_budget(db, TransactionCategory.GROCERIES, 500.0)
        retrieved = BudgetService.get_budget(db, TransactionCategory.GROCERIES)
        assert retrieved.id == created.id

    def test_get_all_budgets(self, db):
        """Test retrieving all budgets."""
        BudgetService.create_budget(db, TransactionCategory.GROCERIES, 500.0)
        BudgetService.create_budget(db, TransactionCategory.DINING, 300.0)
        budgets = BudgetService.get_all_budgets(db)
        assert len(budgets) == 2

    def test_update_budget(self, db):
        """Test updating a budget."""
        BudgetService.create_budget(db, TransactionCategory.GROCERIES, 500.0)
        updated = BudgetService.update_budget(db, TransactionCategory.GROCERIES, 600.0)
        assert updated.monthly_limit == 600.0

    def test_get_monthly_summary(self, db):
        """Test getting monthly budget summary."""
        account = AccountService.create_account(db, "Checking", "checking", 1000.0)
        BudgetService.create_budget(db, TransactionCategory.GROCERIES, 500.0)
        BudgetService.create_budget(db, TransactionCategory.DINING, 300.0)

        now = datetime.utcnow()
        TransactionService.create_transaction(
            db,
            account.id,
            50.0,
            TransactionCategory.GROCERIES,
            "Groceries",
            now,
        )
        TransactionService.create_transaction(
            db,
            account.id,
            30.0,
            TransactionCategory.DINING,
            "Dinner",
            now,
        )

        summary = BudgetService.get_monthly_summary(db, now.year, now.month)
        assert len(summary) == 2
        assert summary[0].spent == 50.0
        assert summary[1].spent == 30.0


class TestDebtService:
    """Test DebtService."""

    def test_create_debt(self, db):
        """Test creating a debt."""
        debt = DebtService.create_debt(
            db, "Student Loan", 10000.0, 5.0, 200.0, "Educational debt"
        )
        assert debt.name == "Student Loan"
        assert debt.principal == 10000.0
        assert debt.remaining == 10000.0

    def test_get_debt(self, db):
        """Test retrieving a debt."""
        created = DebtService.create_debt(db, "Student Loan", 10000.0, 5.0, 200.0)
        retrieved = DebtService.get_debt(db, created.id)
        assert retrieved.id == created.id

    def test_get_all_debts(self, db):
        """Test retrieving all debts."""
        DebtService.create_debt(db, "Student Loan", 10000.0, 5.0, 200.0)
        DebtService.create_debt(db, "Credit Card", 5000.0, 18.0, 150.0)
        debts = DebtService.get_all_debts(db)
        assert len(debts) == 2

    def test_update_debt_remaining(self, db):
        """Test updating remaining debt."""
        debt = DebtService.create_debt(db, "Student Loan", 10000.0, 5.0, 200.0)
        updated = DebtService.update_debt_remaining(db, debt.id, 8000.0)
        assert updated.remaining == 8000.0

    def test_get_total_debt(self, db):
        """Test getting total debt."""
        DebtService.create_debt(db, "Student Loan", 10000.0, 5.0, 200.0)
        DebtService.create_debt(db, "Credit Card", 5000.0, 18.0, 150.0)
        total = DebtService.get_total_debt(db)
        assert total == 15000.0

    def test_get_total_monthly_payments(self, db):
        """Test getting total monthly debt payments."""
        DebtService.create_debt(db, "Student Loan", 10000.0, 5.0, 200.0)
        DebtService.create_debt(db, "Credit Card", 5000.0, 18.0, 150.0)
        total = DebtService.get_total_monthly_payments(db)
        assert total == 350.0
