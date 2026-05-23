"""Database access layer for finance dashboard."""
from datetime import datetime, date, timedelta
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from .models import Account, Transaction, BudgetCategory, Debt


class FinanceDB:
    """High-level database interface for financial operations."""

    def __init__(self, session: Session):
        self.session = session

    # Account operations
    def create_account(self, name: str, account_type: str, initial_balance: float = 0.0) -> Account:
        """Create a new account."""
        account = Account(name=name, account_type=account_type, balance=initial_balance)
        self.session.add(account)
        self.session.commit()
        return account

    def get_account(self, account_id: int) -> Optional[Account]:
        """Get account by ID."""
        return self.session.query(Account).filter(Account.id == account_id).first()

    def get_account_by_name(self, name: str) -> Optional[Account]:
        """Get account by name."""
        return self.session.query(Account).filter(Account.name == name).first()

    def list_accounts(self) -> List[Account]:
        """List all accounts."""
        return self.session.query(Account).all()

    def update_account_balance(self, account_id: int, new_balance: float) -> None:
        """Update account balance."""
        account = self.get_account(account_id)
        if account:
            account.balance = new_balance
            self.session.commit()

    def delete_account(self, account_id: int) -> None:
        """Delete account and all related data."""
        account = self.get_account(account_id)
        if account:
            self.session.delete(account)
            self.session.commit()

    # Transaction operations
    def add_transaction(self, account_id: int, amount: float, category: str,
                       description: str, transaction_date: Optional[date] = None) -> Transaction:
        """Add a transaction."""
        if transaction_date is None:
            transaction_date = date.today()

        transaction = Transaction(
            account_id=account_id,
            amount=amount,
            category=category,
            description=description,
            transaction_date=transaction_date
        )
        self.session.add(transaction)

        # Update account balance
        account = self.get_account(account_id)
        if account:
            account.balance += amount

        self.session.commit()
        return transaction

    def get_transactions(self, account_id: int, days: int = 30) -> List[Transaction]:
        """Get transactions for account in last N days."""
        cutoff_date = date.today() - timedelta(days=days)
        return self.session.query(Transaction).filter(
            Transaction.account_id == account_id,
            Transaction.transaction_date >= cutoff_date
        ).order_by(Transaction.transaction_date.desc()).all()

    def get_transactions_by_category(self, account_id: int, category: str, days: int = 30) -> List[Transaction]:
        """Get transactions for specific category."""
        cutoff_date = date.today() - timedelta(days=days)
        return self.session.query(Transaction).filter(
            Transaction.account_id == account_id,
            Transaction.category == category,
            Transaction.transaction_date >= cutoff_date
        ).order_by(Transaction.transaction_date.desc()).all()

    def delete_transaction(self, transaction_id: int) -> None:
        """Delete transaction and update account balance."""
        transaction = self.session.query(Transaction).filter(Transaction.id == transaction_id).first()
        if transaction:
            account = transaction.account
            account.balance -= transaction.amount
            self.session.delete(transaction)
            self.session.commit()

    # Budget operations
    def create_budget_category(self, account_id: int, name: str,
                              monthly_limit: float, weekly_limit: float) -> BudgetCategory:
        """Create a budget category."""
        category = BudgetCategory(
            account_id=account_id,
            name=name,
            monthly_limit=monthly_limit,
            weekly_limit=weekly_limit
        )
        self.session.add(category)
        self.session.commit()
        return category

    def get_budget_categories(self, account_id: int) -> List[BudgetCategory]:
        """Get all budget categories for an account."""
        return self.session.query(BudgetCategory).filter(BudgetCategory.account_id == account_id).all()

    def get_budget_category(self, category_id: int) -> Optional[BudgetCategory]:
        """Get budget category by ID."""
        return self.session.query(BudgetCategory).filter(BudgetCategory.id == category_id).first()

    def delete_budget_category(self, category_id: int) -> None:
        """Delete budget category."""
        category = self.get_budget_category(category_id)
        if category:
            self.session.delete(category)
            self.session.commit()

    def get_spending_summary(self, account_id: int, category: str) -> Tuple[float, float]:
        """Get weekly and monthly spending for category.

        Returns: (weekly_total, monthly_total)
        """
        today = date.today()
        week_start = today - timedelta(days=today.weekday())
        month_start = today.replace(day=1)

        weekly_trans = self.session.query(Transaction).filter(
            Transaction.account_id == account_id,
            Transaction.category == category,
            Transaction.transaction_date >= week_start
        ).all()

        monthly_trans = self.session.query(Transaction).filter(
            Transaction.account_id == account_id,
            Transaction.category == category,
            Transaction.transaction_date >= month_start
        ).all()

        weekly_total = sum(abs(t.amount) for t in weekly_trans if t.amount < 0)
        monthly_total = sum(abs(t.amount) for t in monthly_trans if t.amount < 0)

        return weekly_total, monthly_total

    # Debt operations
    def create_debt(self, account_id: int, creditor_name: str, original_amount: float,
                   current_amount: float, interest_rate: float, monthly_payment: float) -> Debt:
        """Create a new debt."""
        debt = Debt(
            account_id=account_id,
            creditor_name=creditor_name,
            original_amount=original_amount,
            current_amount=current_amount,
            interest_rate=interest_rate,
            monthly_payment=monthly_payment
        )
        self.session.add(debt)
        self.session.commit()
        return debt

    def get_debts(self, account_id: int) -> List[Debt]:
        """Get all debts for account."""
        return self.session.query(Debt).filter(Debt.account_id == account_id).all()

    def get_debt(self, debt_id: int) -> Optional[Debt]:
        """Get debt by ID."""
        return self.session.query(Debt).filter(Debt.id == debt_id).first()

    def update_debt(self, debt_id: int, current_amount: float) -> None:
        """Update debt current amount."""
        debt = self.get_debt(debt_id)
        if debt:
            debt.current_amount = current_amount
            self.session.commit()

    def delete_debt(self, debt_id: int) -> None:
        """Delete debt."""
        debt = self.get_debt(debt_id)
        if debt:
            self.session.delete(debt)
            self.session.commit()

    def get_total_debt(self, account_id: int) -> float:
        """Get total outstanding debt."""
        debts = self.get_debts(account_id)
        return sum(d.current_amount for d in debts)
