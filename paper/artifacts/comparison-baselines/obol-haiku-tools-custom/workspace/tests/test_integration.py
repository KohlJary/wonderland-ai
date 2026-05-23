"""Integration tests for the entire system."""
import tempfile
from datetime import datetime
from pathlib import Path

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
    """Create test client with test database."""
    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)


class TestFullWorkflow:
    """Test complete finance management workflow."""

    def test_complete_workflow(self, client, db):
        """Test creating accounts, transactions, budgets, and debts."""
        # 1. Create an account
        response = client.post(
            "/api/accounts",
            json={"name": "Checking", "account_type": "checking", "balance": 5000.0},
        )
        assert response.status_code == 200
        account = response.json()
        account_id = account["id"]
        assert account["balance"] == 5000.0

        # 2. Create budgets
        response = client.post(
            "/api/budgets",
            json={"category": "groceries", "monthly_limit": 500.0},
        )
        assert response.status_code == 200
        assert response.json()["monthly_limit"] == 500.0

        # 3. Create transactions
        response = client.post(
            "/api/transactions",
            json={
                "account_id": account_id,
                "amount": 50.0,
                "category": "groceries",
                "description": "Whole Foods",
            },
        )
        assert response.status_code == 200
        assert response.json()["amount"] == 50.0

        # Check account balance was updated
        response = client.get(f"/api/accounts/{account_id}")
        assert response.json()["balance"] == 4950.0

        # 4. Create debt
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
        debt = response.json()
        assert debt["paydown_progress"] == 0.0

        # 5. Pay down debt
        response = client.put(
            f"/api/debts/{debt['id']}",
            json={"remaining": 8000.0, "monthly_payment": 250.0},
        )
        assert response.status_code == 200
        updated_debt = response.json()
        assert updated_debt["remaining"] == 8000.0
        assert updated_debt["paydown_progress"] == 20.0

        # 6. Check dashboard
        response = client.get("/api/dashboard/stats")
        assert response.status_code == 200
        stats = response.json()
        assert stats["total_balance"] == 4950.0
        assert stats["total_debt"] == 8000.0
        assert stats["accounts_count"] == 1
        assert stats["transactions_count"] == 1

    def test_budget_summary(self, client, db):
        """Test monthly budget summary."""
        # Create account
        response = client.post(
            "/api/accounts",
            json={"name": "Checking", "account_type": "checking", "balance": 5000.0},
        )
        account_id = response.json()["id"]

        # Create budget
        client.post(
            "/api/budgets",
            json={"category": "groceries", "monthly_limit": 500.0},
        )
        client.post(
            "/api/budgets",
            json={"category": "dining", "monthly_limit": 300.0},
        )

        # Create transactions
        client.post(
            "/api/transactions",
            json={
                "account_id": account_id,
                "amount": 100.0,
                "category": "groceries",
                "description": "Groceries",
            },
        )
        client.post(
            "/api/transactions",
            json={
                "account_id": account_id,
                "amount": 50.0,
                "category": "dining",
                "description": "Restaurant",
            },
        )

        # Get summary
        now = datetime.utcnow()
        response = client.get(
            "/api/budgets/summary/monthly",
            params={"year": now.year, "month": now.month},
        )
        assert response.status_code == 200
        summary = response.json()
        assert len(summary) == 2

        # Find groceries and dining
        groceries = next(s for s in summary if s["category"] == "groceries")
        dining = next(s for s in summary if s["category"] == "dining")

        assert groceries["spent"] == 100.0
        assert groceries["limit"] == 500.0
        assert groceries["remaining"] == 400.0
        assert groceries["percentage"] == 20.0

        assert dining["spent"] == 50.0
        assert dining["limit"] == 300.0
        assert dining["remaining"] == 250.0
        assert dining["percentage"] == pytest.approx(16.67, abs=0.1)

    def test_multiple_accounts(self, client):
        """Test managing multiple accounts."""
        # Create multiple accounts
        accounts = []
        for i, (name, balance) in enumerate([
            ("Checking", 5000.0),
            ("Savings", 20000.0),
            ("Emergency Fund", 10000.0),
        ]):
            response = client.post(
                "/api/accounts",
                json={"name": name, "account_type": "savings", "balance": balance},
            )
            accounts.append(response.json())

        # Get all accounts
        response = client.get("/api/accounts")
        assert response.status_code == 200
        assert len(response.json()) == 3

        # Check dashboard total
        response = client.get("/api/dashboard/stats")
        stats = response.json()
        assert stats["total_balance"] == 35000.0
        assert stats["accounts_count"] == 3

    def test_debt_payoff_tracking(self, client):
        """Test tracking multiple debts and total."""
        # Create debts
        debts_to_create = [
            ("Student Loan", 50000.0, 4.5, 450.0),
            ("Credit Card", 5000.0, 18.5, 200.0),
            ("Auto Loan", 25000.0, 5.2, 350.0),
        ]

        created_debts = []
        for name, principal, rate, payment in debts_to_create:
            response = client.post(
                "/api/debts",
                json={
                    "name": name,
                    "principal": principal,
                    "interest_rate": rate,
                    "monthly_payment": payment,
                },
            )
            created_debts.append(response.json())

        # Get all debts
        response = client.get("/api/debts")
        assert response.status_code == 200
        debts = response.json()
        assert len(debts) == 3

        # Check dashboard
        response = client.get("/api/dashboard/stats")
        stats = response.json()
        assert stats["total_debt"] == 80000.0

        # Pay down first debt
        response = client.put(
            f"/api/debts/{created_debts[0]['id']}",
            json={"remaining": 40000.0, "monthly_payment": 500.0},
        )
        assert response.status_code == 200
        updated = response.json()
        assert updated["paydown_progress"] == 20.0

        # Check updated dashboard
        response = client.get("/api/dashboard/stats")
        stats = response.json()
        assert stats["total_debt"] == 70000.0
