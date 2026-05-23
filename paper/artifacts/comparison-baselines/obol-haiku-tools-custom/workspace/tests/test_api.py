"""Tests for FastAPI endpoints."""
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.backend.database import Account, Base, Budget, Debt, Transaction, TransactionCategory
from src.backend.main import app, get_db


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


@pytest.fixture
def client(db):
    """Create test client."""
    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)


class TestAccountEndpoints:
    """Test account endpoints."""

    def test_create_account(self, client):
        """Test creating an account."""
        response = client.post(
            "/api/accounts",
            json={"name": "Checking", "account_type": "checking", "balance": 1000.0},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Checking"
        assert data["balance"] == 1000.0

    def test_get_accounts(self, client):
        """Test getting all accounts."""
        client.post(
            "/api/accounts",
            json={"name": "Checking", "account_type": "checking", "balance": 1000.0},
        )
        response = client.get("/api/accounts")
        assert response.status_code == 200
        accounts = response.json()
        assert len(accounts) == 1

    def test_get_account(self, client):
        """Test getting a specific account."""
        create_resp = client.post(
            "/api/accounts",
            json={"name": "Checking", "account_type": "checking", "balance": 1000.0},
        )
        account_id = create_resp.json()["id"]
        response = client.get(f"/api/accounts/{account_id}")
        assert response.status_code == 200
        assert response.json()["name"] == "Checking"

    def test_update_account(self, client):
        """Test updating an account."""
        create_resp = client.post(
            "/api/accounts",
            json={"name": "Checking", "account_type": "checking", "balance": 1000.0},
        )
        account_id = create_resp.json()["id"]
        response = client.put(f"/api/accounts/{account_id}", json={"balance": 1500.0})
        assert response.status_code == 200
        assert response.json()["balance"] == 1500.0


class TestTransactionEndpoints:
    """Test transaction endpoints."""

    def test_create_transaction(self, client, db):
        """Test creating a transaction."""
        # Create account first
        account = Account(name="Checking", account_type="checking", balance=1000.0)
        db.add(account)
        db.commit()

        response = client.post(
            "/api/transactions",
            json={
                "account_id": account.id,
                "amount": 50.0,
                "category": "groceries",
                "description": "Groceries",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["amount"] == 50.0
        assert data["category"] == "groceries"

    def test_get_transactions(self, client, db):
        """Test getting all transactions."""
        account = Account(name="Checking", account_type="checking", balance=1000.0)
        db.add(account)
        db.commit()

        client.post(
            "/api/transactions",
            json={
                "account_id": account.id,
                "amount": 50.0,
                "category": "groceries",
                "description": "Groceries",
            },
        )
        response = client.get("/api/transactions")
        assert response.status_code == 200
        transactions = response.json()
        assert len(transactions) == 1


class TestBudgetEndpoints:
    """Test budget endpoints."""

    def test_create_budget(self, client):
        """Test creating a budget."""
        response = client.post(
            "/api/budgets",
            json={"category": "groceries", "monthly_limit": 500.0},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["category"] == "groceries"
        assert data["monthly_limit"] == 500.0

    def test_get_budgets(self, client):
        """Test getting all budgets."""
        client.post(
            "/api/budgets",
            json={"category": "groceries", "monthly_limit": 500.0},
        )
        response = client.get("/api/budgets")
        assert response.status_code == 200
        budgets = response.json()
        assert len(budgets) == 1

    def test_update_budget(self, client):
        """Test updating a budget."""
        client.post(
            "/api/budgets",
            json={"category": "groceries", "monthly_limit": 500.0},
        )
        response = client.put(
            "/api/budgets/groceries",
            json={"monthly_limit": 600.0},
        )
        assert response.status_code == 200
        assert response.json()["monthly_limit"] == 600.0

    def test_monthly_summary(self, client, db):
        """Test getting monthly budget summary."""
        account = Account(name="Checking", account_type="checking", balance=1000.0)
        db.add(account)
        db.commit()

        client.post(
            "/api/budgets",
            json={"category": "groceries", "monthly_limit": 500.0},
        )

        now = datetime.utcnow()
        response = client.get(
            "/api/budgets/summary/monthly",
            params={"year": now.year, "month": now.month},
        )
        assert response.status_code == 200


class TestDebtEndpoints:
    """Test debt endpoints."""

    def test_create_debt(self, client):
        """Test creating a debt."""
        response = client.post(
            "/api/debts",
            json={
                "name": "Student Loan",
                "principal": 10000.0,
                "interest_rate": 5.0,
                "monthly_payment": 200.0,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Student Loan"
        assert data["principal"] == 10000.0

    def test_get_debts(self, client):
        """Test getting all debts."""
        client.post(
            "/api/debts",
            json={
                "name": "Student Loan",
                "principal": 10000.0,
                "interest_rate": 5.0,
                "monthly_payment": 200.0,
            },
        )
        response = client.get("/api/debts")
        assert response.status_code == 200
        debts = response.json()
        assert len(debts) == 1

    def test_update_debt(self, client):
        """Test updating a debt."""
        create_resp = client.post(
            "/api/debts",
            json={
                "name": "Student Loan",
                "principal": 10000.0,
                "interest_rate": 5.0,
                "monthly_payment": 200.0,
            },
        )
        debt_id = create_resp.json()["id"]

        response = client.put(
            f"/api/debts/{debt_id}",
            json={"remaining": 8000.0, "monthly_payment": 250.0},
        )
        assert response.status_code == 200
        assert response.json()["remaining"] == 8000.0


class TestDashboardEndpoints:
    """Test dashboard endpoints."""

    def test_dashboard_stats(self, client, db):
        """Test dashboard stats endpoint."""
        account = Account(name="Checking", account_type="checking", balance=1000.0)
        db.add(account)
        db.commit()

        response = client.get("/api/dashboard/stats")
        assert response.status_code == 200
        stats = response.json()
        assert stats["total_balance"] == 1000.0
        assert stats["accounts_count"] == 1
