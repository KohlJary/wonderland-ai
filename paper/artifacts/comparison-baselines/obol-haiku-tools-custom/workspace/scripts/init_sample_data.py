#!/usr/bin/env python3
"""Initialize sample data for testing."""
import sys
from pathlib import Path

# Add parent directory to path so we can import src
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import datetime, timedelta

from src.backend.database import TransactionCategory, get_session_factory, init_db
from src.backend.services import (
    AccountService,
    BudgetService,
    DebtService,
    TransactionService,
)


def init_sample_data():
    """Initialize sample data."""
    init_db()
    SessionLocal = get_session_factory()
    db = SessionLocal()

    try:
        # Create accounts
        checking = AccountService.create_account(db, "Checking", "checking", 5000.0)
        savings = AccountService.create_account(db, "Savings", "savings", 15000.0)
        credit_card = AccountService.create_account(db, "Credit Card", "credit_card", -500.0)

        print(f"✓ Created accounts: {checking.name}, {savings.name}, {credit_card.name}")

        # Create budgets
        BudgetService.create_budget(db, TransactionCategory.GROCERIES, 500.0)
        BudgetService.create_budget(db, TransactionCategory.DINING, 300.0)
        BudgetService.create_budget(db, TransactionCategory.TRANSPORTATION, 400.0)
        BudgetService.create_budget(db, TransactionCategory.UTILITIES, 200.0)
        BudgetService.create_budget(db, TransactionCategory.ENTERTAINMENT, 150.0)

        print("✓ Created budgets for: Groceries, Dining, Transportation, Utilities, Entertainment")

        # Create transactions (last 30 days)
        now = datetime.utcnow()
        transactions = [
            (checking.id, 3000.0, TransactionCategory.INCOME, "Salary", now - timedelta(days=15)),
            (checking.id, 120.0, TransactionCategory.GROCERIES, "Whole Foods", now - timedelta(days=13)),
            (checking.id, 45.0, TransactionCategory.DINING, "Restaurant", now - timedelta(days=12)),
            (checking.id, 30.0, TransactionCategory.TRANSPORTATION, "Gas", now - timedelta(days=10)),
            (checking.id, 65.0, TransactionCategory.UTILITIES, "Electric Bill", now - timedelta(days=9)),
            (checking.id, 80.0, TransactionCategory.GROCERIES, "Costco", now - timedelta(days=8)),
            (checking.id, 35.0, TransactionCategory.DINING, "Coffee", now - timedelta(days=7)),
            (checking.id, 200.0, TransactionCategory.DEBT_PAYMENT, "Credit Card Payment", now - timedelta(days=6)),
            (checking.id, 95.0, TransactionCategory.GROCERIES, "Trader Joe's", now - timedelta(days=5)),
            (checking.id, 55.0, TransactionCategory.ENTERTAINMENT, "Movie", now - timedelta(days=4)),
            (checking.id, 100.0, TransactionCategory.SHOPPING, "Clothes", now - timedelta(days=3)),
            (checking.id, 40.0, TransactionCategory.TRANSPORTATION, "Uber", now - timedelta(days=2)),
            (checking.id, 75.0, TransactionCategory.DINING, "Dinner", now - timedelta(days=1)),
        ]

        for acc_id, amount, category, desc, date in transactions:
            TransactionService.create_transaction(db, acc_id, amount, category, desc, date)

        print(f"✓ Created {len(transactions)} transactions")

        # Create debts
        student_loan = DebtService.create_debt(
            db,
            "Student Loan",
            50000.0,
            4.5,
            450.0,
            "Federal student loan for college",
        )
        student_loan = DebtService.update_debt_remaining(db, student_loan.id, 35000.0)

        credit_debt = DebtService.create_debt(
            db,
            "Credit Card Debt",
            8000.0,
            18.5,
            200.0,
            "High-interest credit card balance",
        )

        auto_loan = DebtService.create_debt(
            db,
            "Auto Loan",
            25000.0,
            5.2,
            450.0,
            "Car payment",
        )
        auto_loan = DebtService.update_debt_remaining(db, auto_loan.id, 18000.0)

        print("✓ Created 3 debts: Student Loan, Credit Card, Auto Loan")

        print("\n✓ Sample data initialized successfully!")
        print("\nYou can now run the frontend with: python run_frontend.py")

    finally:
        db.close()


if __name__ == "__main__":
    init_sample_data()
