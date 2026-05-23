I'll build a complete TUI (Terminal User Interface) dashboard for personal finance management using Python with Textual, along with tests and configuration files.

```python
# pyproject.toml
[build-system]
requires = ["setuptools>=65.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "finance-tui"
version = "0.1.0"
description = "A TUI dashboard for managing personal finances"
readme = "README.md"
requires-python = ">=3.10"
license = {text = "MIT"}
authors = [
    {name = "Finance TUI", email = "dev@example.com"}
]

dependencies = [
    "textual[dev]>=0.40.0",
    "sqlalchemy>=2.0.0",
    "pydantic>=2.0.0",
    "python-dateutil>=2.8.2",
    "typer>=0.9.0",
    "rich>=13.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "pytest-asyncio>=0.21.0",
    "pytest-cov>=4.0.0",
]

[project.scripts]
finance-tui = "finance_tui.cli:main"

[tool.setuptools.packages.find]
where = ["."]
include = ["finance_tui*"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

```python
# finance_tui/__init__.py
"""Personal Finance TUI Dashboard"""

__version__ = "0.1.0"
```

```python
# finance_tui/cli.py
"""Command-line interface for Finance TUI"""

import typer
from pathlib import Path
from finance_tui.app import FinanceApp

app = typer.Typer()


@app.command()
def main(
    db_path: Path = typer.Option(
        Path.home() / ".finance_tui" / "finance.db",
        "--db",
        help="Path to the SQLite database"
    ),
) -> None:
    """Launch the Finance TUI dashboard"""
    import asyncio
    
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    finance_app = FinanceApp(str(db_path))
    asyncio.run(finance_app.run_async())


if __name__ == "__main__":
    app()
```

```python
# finance_tui/models.py
"""Data models for finance tracking"""

from datetime import datetime
from enum import Enum
from decimal import Decimal

from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Enum as SQLEnum,
    ForeignKey, create_engine, Index
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, Session

Base = declarative_base()


class TransactionType(str, Enum):
    """Type of transaction"""
    INCOME = "income"
    EXPENSE = "expense"
    TRANSFER = "transfer"


class Account(Base):
    """Financial account"""
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), unique=True, nullable=False)
    account_type = Column(String(50), nullable=False)  # checking, savings, credit, etc
    balance = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    transactions = relationship("Transaction", back_populates="account")
    debts = relationship("Debt", back_populates="account")

    def __repr__(self) -> str:
        return f"<Account {self.name}: ${self.balance:.2f}>"


class Transaction(Base):
    """Individual financial transaction"""
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    type = Column(SQLEnum(TransactionType), nullable=False)
    amount = Column(Float, nullable=False)
    category = Column(String(100), nullable=False)
    description = Column(String(255))
    date = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    account = relationship("Account", back_populates="transactions")
    
    __table_args__ = (
        Index("idx_account_date", "account_id", "date"),
        Index("idx_category_date", "category", "date"),
    )

    def __repr__(self) -> str:
        return f"<Transaction {self.type.value}: ${self.amount:.2f} ({self.category})>"


class Budget(Base):
    """Budget for a spending category"""
    __tablename__ = "budgets"

    id = Column(Integer, primary_key=True)
    category = Column(String(100), unique=True, nullable=False)
    monthly_limit = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<Budget {self.category}: ${self.monthly_limit:.2f}/month>"


class Debt(Base):
    """Tracked debt with paydown plan"""
    __tablename__ = "debts"

    id = Column(Integer, primary_key=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    name = Column(String(255), nullable=False)
    principal = Column(Float, nullable=False)  # Original amount
    current_balance = Column(Float, nullable=False)  # Remaining balance
    interest_rate = Column(Float, default=0.0)  # Annual percentage rate
    minimum_payment = Column(Float, nullable=False)
    due_date = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    account = relationship("Account", back_populates="debts")

    def __repr__(self) -> str:
        return f"<Debt {self.name}: ${self.current_balance:.2f} @ {self.interest_rate}%>"


class Database:
    """Database connection manager"""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.engine = create_engine(f"sqlite:///{db_path}", echo=False)
        Base.metadata.create_all(self.engine)

    def get_session(self) -> Session:
        """Get a new database session"""
        from sqlalchemy.orm import sessionmaker
        return sessionmaker(bind=self.engine)()

    def close(self) -> None:
        """Close the database connection"""
        self.engine.dispose()
```

```python
# finance_tui/service.py
"""Business logic for finance operations"""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Dict, Optional, Tuple

from sqlalchemy.orm import Session

from finance_tui.models import (
    Account, Transaction, Budget, Debt, TransactionType, Database
)


class FinanceService:
    """Service for finance operations"""

    def __init__(self, db: Database):
        self.db = db

    def get_session(self) -> Session:
        """Get a new database session"""
        return self.db.get_session()

    # Account operations
    def create_account(
        self,
        name: str,
        account_type: str,
        initial_balance: float = 0.0
    ) -> Account:
        """Create a new account"""
        session = self.get_session()
        try:
            account = Account(
                name=name,
                account_type=account_type,
                balance=initial_balance
            )
            session.add(account)
            session.commit()
            return account
        finally:
            session.close()

    def get_accounts(self) -> List[Account]:
        """Get all accounts"""
        session = self.get_session()
        try:
            return session.query(Account).all()
        finally:
            session.close()

    def get_account(self, account_id: int) -> Optional[Account]:
        """Get account by ID"""
        session = self.get_session()
        try:
            return session.query(Account).filter(Account.id == account_id).first()
        finally:
            session.close()

    def get_total_balance(self) -> float:
        """Get total balance across all accounts"""
        session = self.get_session()
        try:
            accounts = session.query(Account).all()
            return sum(a.balance for a in accounts)
        finally:
            session.close()

    # Transaction operations
    def add_transaction(
        self,
        account_id: int,
        trans_type: TransactionType,
        amount: float,
        category: str,
        description: str = "",
        date: Optional[datetime] = None
    ) -> Transaction:
        """Add a transaction"""
        session = self.get_session()
        try:
            if date is None:
                date = datetime.utcnow()

            transaction = Transaction(
                account_id=account_id,
                type=trans_type,
                amount=amount,
                category=category,
                description=description,
                date=date
            )
            session.add(transaction)

            # Update account balance
            account = session.query(Account).filter(
                Account.id == account_id
            ).first()
            if account:
                if trans_type == TransactionType.INCOME:
                    account.balance += amount
                elif trans_type == TransactionType.EXPENSE:
                    account.balance -= amount

            session.commit()
            return transaction
        finally:
            session.close()

    def get_transactions(
        self,
        account_id: Optional[int] = None,
        days: int = 30,
        category: Optional[str] = None
    ) -> List[Transaction]:
        """Get transactions"""
        session = self.get_session()
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            query = session.query(Transaction).filter(
                Transaction.date >= cutoff_date
            )

            if account_id:
                query = query.filter(Transaction.account_id == account_id)
            
            if category:
                query = query.filter(Transaction.category == category)

            return query.order_by(Transaction.date.desc()).all()
        finally:
            session.close()

    def get_expenses_by_category(
        self,
        days: int = 30
    ) -> Dict[str, float]:
        """Get total expenses grouped by category"""
        session = self.get_session()
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            transactions = session.query(Transaction).filter(
                Transaction.type == TransactionType.EXPENSE,
                Transaction.date >= cutoff_date
            ).all()

            result = {}
            for trans in transactions:
                result[trans.category] = result.get(trans.category, 0.0) + trans.amount
            return result
        finally:
            session.close()

    # Budget operations
    def set_budget(self, category: str, monthly_limit: float) -> Budget:
        """Set or update a budget"""
        session = self.get_session()
        try:
            budget = session.query(Budget).filter(
                Budget.category == category
            ).first()
            
            if budget:
                budget.monthly_limit = monthly_limit
                budget.updated_at = datetime.utcnow()
            else:
                budget = Budget(category=category, monthly_limit=monthly_limit)
                session.add(budget)
            
            session.commit()
            return budget
        finally:
            session.close()

    def get_budgets(self) -> List[Budget]:
        """Get all budgets"""
        session = self.get_session()
        try:
            return session.query(Budget).all()
        finally:
            session.close()

    def get_budget_status(self) -> Dict[str, Dict[str, float]]:
        """Get current spending vs budget for each category"""
        session = self.get_session()
        try:
            budgets = session.query(Budget).all()
            cutoff_date = datetime.utcnow() - timedelta(days=30)
            
            result = {}
            for budget in budgets:
                spent = session.query(Transaction).filter(
                    Transaction.category == budget.category,
                    Transaction.type == TransactionType.EXPENSE,
                    Transaction.date >= cutoff_date
                ).all()
                
                total_spent = sum(t.amount for t in spent)
                result[budget.category] = {
                    "limit": budget.monthly_limit,
                    "spent": total_spent,
                    "remaining": budget.monthly_limit - total_spent,
                    "percentage": (total_spent / budget.monthly_limit * 100) if budget.monthly_limit > 0 else 0
                }
            
            return result
        finally:
            session.close()

    # Debt operations
    def create_debt(
        self,
        account_id: int,
        name: str,
        principal: float,
        interest_rate: float = 0.0,
        minimum_payment: float = 0.0,
        due_date: Optional[datetime] = None
    ) -> Debt:
        """Create a new debt"""
        session = self.get_session()
        try:
            debt = Debt(
                account_id=account_id,
                name=name,
                principal=principal,
                current_balance=principal,
                interest_rate=interest_rate,
                minimum_payment=minimum_payment,
                due_date=due_date
            )
            session.add(debt)
            session.commit()
            return debt
        finally:
            session.close()

    def get_debts(self, account_id: Optional[int] = None) -> List[Debt]:
        """Get debts"""
        session = self.get_session()
        try:
            query = session.query(Debt)
            if account_id:
                query = query.filter(Debt.account_id == account_id)
            return query.all()
        finally:
            session.close()

    def pay_debt(
        self,
        debt_id: int,
        payment_amount: float
    ) -> Debt:
        """Make a debt payment"""
        session = self.get_session()
        try:
            debt = session.query(Debt).filter(Debt.id == debt_id).first()
            if debt:
                debt.current_balance -= payment_amount
                debt.current_balance = max(0, debt.current_balance)
                debt.updated_at = datetime.utcnow()
                session.commit()
            return debt
        finally:
            session.close()

    def get_total_debt(self) -> float:
        """Get total debt across all accounts"""
        session = self.get_session()
        try:
            debts = session.query(Debt).all()
            return sum(d.current_balance for d in debts)
        finally:
            session.close()

    def get_debt_paydown_progress(self, debt_id: int) -> Dict[str, float]:
        """Get paydown progress for a debt"""
        session = self.get_session()
        try:
            debt = session.query(Debt).filter(Debt.id == debt_id).first()
            if not debt:
                return {}
            
            return {
                "original": debt.principal,
                "remaining": debt.current_balance,
                "paid_off": debt.principal - debt.current_balance,
                "percentage": (
                    (debt.principal - debt.current_balance) / debt.principal * 100
                    if debt.principal > 0 else 0
                )
            }
        finally:
            session.close()
```

```python
# finance_tui/app.py
"""Main TUI application"""

from datetime import datetime
from textual.app import ComposeResult
from textual.containers import Container, Vertical, Horizontal
from textual.screen import Screen
from textual.widgets import Header, Footer, Static, Button, DataTable, Input, Select
from textual.binding import Binding
from textual.reactive import reactive

from finance_tui.models import Database, TransactionType
from finance_tui.service import FinanceService
from finance_tui.widgets import (
    AccountsPanel, TransactionsPanel, BudgetPanel,
    DebtsPanel, DashboardSummary, ModalDialog
)


class FinanceApp:
    """Main finance TUI application"""

    def __init__(self, db_path: str):
        self.db = Database(db_path)
        self.service = FinanceService(self.db)
        
        # Initialize with sample data if empty
        if not self.service.get_accounts():
            self._init_sample_data()

    def _init_sample_data(self) -> None:
        """Initialize with sample data"""
        checking = self.service.create_account("Checking", "checking", 2500.0)
        savings = self.service.create_account("Savings", "savings", 5000.0)
        credit = self.service.create_account("Credit Card", "credit", 0.0)

        # Add transactions
        now = datetime.utcnow()
        self.service.add_transaction(
            checking.id,
            TransactionType.INCOME,
            3500.0,
            "Salary",
            "Monthly salary",
            now
        )
        self.service.add_transaction(
            checking.id,
            TransactionType.EXPENSE,
            1200.0,
            "Rent",
            "Monthly rent",
            now
        )
        self.service.add_transaction(
            checking.id,
            TransactionType.EXPENSE,
            150.0,
            "Groceries",
            "Weekly groceries",
            now
        )
        self.service.add_transaction(
            checking.id,
            TransactionType.EXPENSE,
            50.0,
            "Entertainment",
            "Streaming services",
            now
        )

        # Add budgets
        self.service.set_budget("Groceries", 400.0)
        self.service.set_budget("Entertainment", 100.0)
        self.service.set_budget("Rent", 1500.0)

        # Add debt
        self.service.create_debt(
            credit.id,
            "Credit Card Balance",
            2000.0,
            interest_rate=18.5,
            minimum_payment=100.0
        )

    async def run_async(self) -> None:
        """Run the application asynchronously"""
        from finance_tui.tui import MainScreen
        
        screen = MainScreen(self.service)
        await screen.run_async()


# Import TUI components - they're defined in their own module
```

```python
# finance_tui/widgets.py
"""Textual widgets for the finance TUI"""

from datetime import datetime, timedelta
from textual.widgets import Static, DataTable, Button, Input, Label
from textual.containers import Horizontal, Vertical, Container, ScrollableContainer
from textual.reactive import reactive
from rich.table import Table
from rich.text import Text
from rich.panel import Panel

from finance_tui.service import FinanceService
from finance_tui.models import TransactionType


class DashboardSummary(Static):
    """Dashboard summary widget showing key metrics"""

    service: FinanceService = reactive(None)

    def __init__(self, service: FinanceService, **kwargs):
        super().__init__(**kwargs)
        self.service = service
        self.update_content()

    def update_content(self) -> None:
        """Update dashboard summary"""
        if not self.service:
            return

        total_balance = self.service.get_total_balance()
        total_debt = self.service.get_total_debt()
        net_worth = total_balance - total_debt

        # Get this month's summary
        cutoff = datetime.utcnow() - timedelta(days=30)
        transactions = self.service.get_transactions(days=30)
        
        income = sum(
            t.amount for t in transactions
            if t.type == TransactionType.INCOME
        )
        expenses = sum(
            t.amount for t in transactions
            if t.type == TransactionType.EXPENSE
        )

        summary_table = Table(title="Financial Summary", show_header=False)
        summary_table.add_row("Total Assets", f"${total_balance:,.2f}")
        summary_table.add_row("Total Debt", f"${total_debt:,.2f}")
        summary_table.add_row("Net Worth", f"${net_worth:,.2f}")
        summary_table.add_row("")
        summary_table.add_row("30-Day Income", f"${income:,.2f}")
        summary_table.add_row("30-Day Expenses", f"${expenses:,.2f}")
        summary_table.add_row("30-Day Net", f"${income - expenses:,.2f}")

        self.update(Panel(summary_table, border_style="green"))


class AccountsPanel(Static):
    """Panel showing all accounts"""

    service: FinanceService = reactive(None)

    def __init__(self, service: FinanceService, **kwargs):
        super().__init__(**kwargs)
        self.service = service
        self.update_content()

    def update_content(self) -> None:
        """Update accounts display"""
        if not self.service:
            return

        accounts = self.service.get_accounts()
        table = Table(title="Accounts", show_header=True)
        table.add_column("Name", style="cyan")
        table.add_column("Type", style="magenta")
        table.add_column("Balance", style="green", justify="right")

        for account in accounts:
            balance_color = "green" if account.balance >= 0 else "red"
            table.add_row(
                account.name,
                account.account_type,
                f"[{balance_color}]${account.balance:,.2f}[/{balance_color}]"
            )

        self.update(Panel(table, border_style="blue"))


class TransactionsPanel(Static):
    """Panel showing recent transactions"""

    service: FinanceService = reactive(None)

    def __init__(self, service: FinanceService, **kwargs):
        super().__init__(**kwargs)
        self.service = service
        self.update_content()

    def update_content(self) -> None:
        """Update transactions display"""
        if not self.service:
            return

        transactions = self.service.get_transactions(days=30)
        table = Table(title="Recent Transactions (30 days)", show_header=True)
        table.add_column("Date", style="cyan")
        table.add_column("Category", style="magenta")
        table.add_column("Description", style="white")
        table.add_column("Type", style="yellow")
        table.add_column("Amount", style="green", justify="right")

        for trans in transactions[:20]:
            type_str = trans.type.value
            type_color = "green" if trans.type == TransactionType.INCOME else "red"
            table.add_row(
                trans.date.strftime("%Y-%m-%d"),
                trans.category,
                trans.description[:30] if trans.description else "-",
                f"[{type_color}]{type_str}[/{type_color}]",
                f"[{type_color}]${trans.amount:,.2f}[/{type_color}]"
            )

        self.update(Panel(table, border_style="blue"))


class BudgetPanel(Static):
    """Panel showing budget status"""

    service: FinanceService = reactive(None)

    def __init__(self, service: FinanceService, **kwargs):
        super().__init__(**kwargs)
        self.service = service
        self.update_content()

    def update_content(self) -> None:
        """Update budget display"""
        if not self.service:
            return

        budget_status = self.service.get_budget_status()
        table = Table(title="Budget Status (30 days)", show_header=True)
        table.add_column("Category", style="cyan")
        table.add_column("Spent", style="yellow", justify="right")
        table.add_column("Limit", style="magenta", justify="right")
        table.add_column("Remaining", style="green", justify="right")
        table.add_column("Usage", style="white", justify="right")

        for category, status in sorted(budget_status.items()):
            spent = status["spent"]
            limit = status["limit"]
            remaining = status["remaining"]
            percentage = status["percentage"]

            # Color based on usage
            if percentage >= 90:
                pct_color = "red"
            elif percentage >= 70:
                pct_color = "yellow"
            else:
                pct_color = "green"

            # Create progress bar
            bar_length = 20
            filled = int(bar_length * percentage / 100)
            bar = "█" * filled + "░" * (bar_length - filled)

            table.add_row(
                category,
                f"${spent:,.2f}",
                f"${limit:,.2f}",
                f"[{'red' if remaining < 0 else 'green'}]${remaining:,.2f}[/]",
                f"[{pct_color}]{percentage:.1f}% {bar}[/{pct_color}]"
            )

        self.update(Panel(table, border_style="blue"))


class DebtsPanel(Static):
    """Panel showing debt status"""

    service: FinanceService = reactive(None)

    def __init__(self, service: FinanceService, **kwargs):
        super().__init__(**kwargs)
        self.service = service
        self.update_content()

    def update_content(self) -> None:
        """Update debts display"""
        if not self.service:
            return

        debts = self.service.get_debts()
        table = Table(title="Debts & Paydown Progress", show_header=True)
        table.add_column("Name", style="cyan")
        table.add_column("Balance", style="red", justify="right")
        table.add_column("Principal", style="magenta", justify="right")
        table.add_column("Interest", style="yellow", justify="right")
        table.add_column("Progress", style="green", justify="right")

        for debt in debts:
            progress = self.service.get_debt_paydown_progress(debt.id)
            
            # Create progress bar
            bar_length = 15
            filled = int(bar_length * progress.get("percentage", 0) / 100)
            bar = "█" * filled + "░" * (bar_length - filled)

            table.add_row(
                debt.name,
                f"[red]${debt.current_balance:,.2f}[/red]",
                f"${debt.principal:,.2f}",
                f"{debt.interest_rate:.1f}%",
                f"[green]{progress.get('percentage', 0):.1f}% {bar}[/green]"
            )

        self.update(Panel(table, border_style="blue"))


class ModalDialog(Static):
    """Modal dialog for user input"""

    def __init__(self, title: str, fields: dict, **kwargs):
        super().__init__(**kwargs)
        self.title = title
        self.fields = fields
        self.input_widgets = {}

    def compose(self):
        yield Label(self.title)
        for field_name, field_type in self.fields.items():
            yield Input(id=field_name, classes="modal-input")
        
        with Horizontal():
            yield Button("OK", id="ok-button")
            yield Button("Cancel", id="cancel-button")
```

```python
# finance_tui/tui.py
"""Main TUI screen"""

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Header, Footer, Static, Button, Label
from textual.binding import Binding

from finance_tui.service import FinanceService
from finance_tui.widgets import (
    DashboardSummary, AccountsPanel, TransactionsPanel,
    BudgetPanel, DebtsPanel
)


class MainScreen(Screen):
    """Main dashboard screen"""

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("1", "show_dashboard", "Dashboard"),
        Binding("2", "show_accounts", "Accounts"),
        Binding("3", "show_transactions", "Transactions"),
        Binding("4", "show_budgets", "Budgets"),
        Binding("5", "show_debts", "Debts"),
        Binding("a", "add_transaction", "Add Transaction"),
        Binding("r", "refresh", "Refresh"),
    ]

    def __init__(self, service: FinanceService, **kwargs):
        super().__init__(**kwargs)
        self.service = service
        self.current_view = "dashboard"

    def compose(self) -> ComposeResult:
        """Create child widgets for the screen."""
        yield Header()
        
        with Container(id="main-container"):
            with Vertical(id="content"):
                self.dashboard_summary = DashboardSummary(self.service, id="summary")
                self.accounts_panel = AccountsPanel(self.service, id="accounts")
                self.transactions_panel = TransactionsPanel(self.service, id="transactions")
                self.budget_panel = BudgetPanel(self.service, id="budgets")
                self.debts_panel = DebtsPanel(self.service, id="debts")
                
                yield self.dashboard_summary
                yield self.accounts_panel
                yield self.transactions_panel
                yield self.budget_panel
                yield self.debts_panel
        
        yield Footer()

    def on_mount(self) -> None:
        """Called when the widget is mounted."""
        self.title = "Finance TUI Dashboard"
        self.sub_title = "htop for money"

    def action_quit(self) -> None:
        """Quit the application."""
        self.app.exit()

    def action_refresh(self) -> None:
        """Refresh all displays."""
        self.dashboard_summary.update_content()
        self.accounts_panel.update_content()
        self.transactions_panel.update_content()
        self.budget_panel.update_content()
        self.debts_panel.update_content()

    def action_show_dashboard(self) -> None:
        """Show dashboard view."""
        self.current_view = "dashboard"
        self.action_refresh()

    def action_show_accounts(self) -> None:
        """Show accounts view."""
        self.current_view = "accounts"
        self.action_refresh()

    def action_show_transactions(self) -> None:
        """Show transactions view."""
        self.current_view = "transactions"
        self.action_refresh()

    def action_show_budgets(self) -> None:
        """Show budgets view."""
        self.current_view = "budgets"
        self.action_refresh()

    def action_show_debts(self) -> None:
        """Show debts view."""
        self.current_view = "debts"
        self.action_refresh()

    def action_add_transaction(self) -> None:
        """Add a new transaction."""
        # This would open a modal dialog in a full implementation
        pass
```

```css
# finance_tui/app.css
Screen {
    layout: vertical;
    background: $surface;
    color: $text;
}

#main-container {
    height: 1fr;
    background: $boost;
}

#content {
    height: 1fr;
    width