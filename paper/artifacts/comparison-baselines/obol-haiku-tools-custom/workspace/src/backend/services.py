"""Business logic services."""
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.orm import Session

from src.backend.database import Account, Budget, Debt, Transaction, TransactionCategory
from src.backend.schemas import (
    MonthlyBudgetSummary,
    WeeklyBudgetSummary,
)


class AccountService:
    """Account management service."""

    @staticmethod
    def get_all_accounts(db: Session) -> list[Account]:
        """Get all accounts."""
        return db.query(Account).all()

    @staticmethod
    def get_account(db: Session, account_id: int) -> Optional[Account]:
        """Get account by ID."""
        return db.query(Account).filter(Account.id == account_id).first()

    @staticmethod
    def create_account(db: Session, name: str, account_type: str, balance: float = 0.0) -> Account:
        """Create a new account."""
        account = Account(name=name, account_type=account_type, balance=balance)
        db.add(account)
        db.commit()
        db.refresh(account)
        return account

    @staticmethod
    def update_account_balance(db: Session, account_id: int, balance: float) -> Optional[Account]:
        """Update account balance."""
        account = db.query(Account).filter(Account.id == account_id).first()
        if account:
            account.balance = balance
            account.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(account)
        return account

    @staticmethod
    def get_total_balance(db: Session) -> float:
        """Get total balance across all accounts."""
        accounts = db.query(Account).all()
        return sum(acc.balance for acc in accounts)


class TransactionService:
    """Transaction management service."""

    @staticmethod
    def create_transaction(
        db: Session,
        account_id: int,
        amount: float,
        category: TransactionCategory,
        description: str,
        date: Optional[datetime] = None,
    ) -> Transaction:
        """Create a new transaction."""
        transaction = Transaction(
            account_id=account_id,
            amount=amount,
            category=category,
            description=description,
            date=date or datetime.utcnow(),
        )
        db.add(transaction)

        # Update account balance
        account = db.query(Account).filter(Account.id == account_id).first()
        if account:
            if category == TransactionCategory.INCOME:
                account.balance += amount
            else:
                account.balance -= amount
            account.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(transaction)
        return transaction

    @staticmethod
    def get_all_transactions(db: Session) -> list[Transaction]:
        """Get all transactions."""
        return db.query(Transaction).order_by(Transaction.date.desc()).all()

    @staticmethod
    def get_account_transactions(db: Session, account_id: int) -> list[Transaction]:
        """Get transactions for an account."""
        return (
            db.query(Transaction)
            .filter(Transaction.account_id == account_id)
            .order_by(Transaction.date.desc())
            .all()
        )

    @staticmethod
    def get_transactions_by_month(db: Session, year: int, month: int) -> list[Transaction]:
        """Get transactions for a specific month."""
        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1)
        else:
            end_date = datetime(year, month + 1, 1)

        return (
            db.query(Transaction)
            .filter(Transaction.date >= start_date, Transaction.date < end_date)
            .order_by(Transaction.date.desc())
            .all()
        )

    @staticmethod
    def get_transactions_by_week(db: Session, week_start: datetime) -> list[Transaction]:
        """Get transactions for a specific week."""
        week_end = week_start + timedelta(days=7)
        return (
            db.query(Transaction)
            .filter(Transaction.date >= week_start, Transaction.date < week_end)
            .order_by(Transaction.date.desc())
            .all()
        )


class BudgetService:
    """Budget management service."""

    @staticmethod
    def create_budget(
        db: Session, category: TransactionCategory, monthly_limit: float
    ) -> Budget:
        """Create a new budget."""
        budget = Budget(category=category, monthly_limit=monthly_limit)
        db.add(budget)
        db.commit()
        db.refresh(budget)
        return budget

    @staticmethod
    def get_budget(db: Session, category: TransactionCategory) -> Optional[Budget]:
        """Get budget by category."""
        return db.query(Budget).filter(Budget.category == category).first()

    @staticmethod
    def get_all_budgets(db: Session) -> list[Budget]:
        """Get all budgets."""
        return db.query(Budget).all()

    @staticmethod
    def update_budget(
        db: Session, category: TransactionCategory, monthly_limit: float
    ) -> Optional[Budget]:
        """Update budget."""
        budget = db.query(Budget).filter(Budget.category == category).first()
        if budget:
            budget.monthly_limit = monthly_limit
            budget.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(budget)
        return budget

    @staticmethod
    def get_monthly_summary(db: Session, year: int, month: int) -> list[MonthlyBudgetSummary]:
        """Get monthly budget summary."""
        budgets = db.query(Budget).all()
        transactions = TransactionService.get_transactions_by_month(db, year, month)

        summary = []
        for budget in budgets:
            spent = sum(
                t.amount for t in transactions if t.category == budget.category
            )
            remaining = budget.monthly_limit - spent
            percentage = (spent / budget.monthly_limit * 100) if budget.monthly_limit > 0 else 0

            summary.append(
                MonthlyBudgetSummary(
                    category=budget.category,
                    spent=spent,
                    limit=budget.monthly_limit,
                    remaining=remaining,
                    percentage=percentage,
                )
            )

        return summary

    @staticmethod
    def get_weekly_summary(db: Session, week_start: datetime) -> WeeklyBudgetSummary:
        """Get weekly budget summary."""
        transactions = TransactionService.get_transactions_by_week(db, week_start)
        week_end = week_start + timedelta(days=6)

        category_totals = {}
        total_spent = 0.0

        for transaction in transactions:
            if transaction.category != TransactionCategory.INCOME:
                category_totals[transaction.category.value] = (
                    category_totals.get(transaction.category.value, 0.0) + transaction.amount
                )
                total_spent += transaction.amount

        return WeeklyBudgetSummary(
            week_start=week_start.strftime("%Y-%m-%d"),
            week_end=week_end.strftime("%Y-%m-%d"),
            total_spent=total_spent,
            categories=category_totals,
        )


class DebtService:
    """Debt tracking service."""

    @staticmethod
    def create_debt(
        db: Session,
        name: str,
        principal: float,
        interest_rate: float,
        monthly_payment: float,
        description: Optional[str] = None,
    ) -> Debt:
        """Create a new debt."""
        debt = Debt(
            name=name,
            principal=principal,
            remaining=principal,
            interest_rate=interest_rate,
            monthly_payment=monthly_payment,
            description=description,
        )
        db.add(debt)
        db.commit()
        db.refresh(debt)
        return debt

    @staticmethod
    def get_all_debts(db: Session) -> list[Debt]:
        """Get all debts."""
        return db.query(Debt).all()

    @staticmethod
    def get_debt(db: Session, debt_id: int) -> Optional[Debt]:
        """Get debt by ID."""
        return db.query(Debt).filter(Debt.id == debt_id).first()

    @staticmethod
    def update_debt_remaining(db: Session, debt_id: int, remaining: float) -> Optional[Debt]:
        """Update remaining debt amount."""
        debt = db.query(Debt).filter(Debt.id == debt_id).first()
        if debt:
            debt.remaining = max(0, remaining)
            debt.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(debt)
        return debt

    @staticmethod
    def update_debt_payment(db: Session, debt_id: int, monthly_payment: float) -> Optional[Debt]:
        """Update monthly payment amount."""
        debt = db.query(Debt).filter(Debt.id == debt_id).first()
        if debt:
            debt.monthly_payment = monthly_payment
            debt.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(debt)
        return debt

    @staticmethod
    def get_total_debt(db: Session) -> float:
        """Get total remaining debt."""
        debts = db.query(Debt).all()
        return sum(debt.remaining for debt in debts)

    @staticmethod
    def get_total_monthly_payments(db: Session) -> float:
        """Get total monthly debt payments."""
        debts = db.query(Debt).all()
        return sum(debt.monthly_payment for debt in debts)
