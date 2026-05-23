"""Main Textual TUI application for finance dashboard."""
from datetime import date, timedelta
from typing import Optional
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.reactive import reactive
from textual.widgets import (
    Static, Label, Input, Button, DataTable, Select, TextArea
)
from textual.screen import Screen
from textual.binding import Binding
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from sqlalchemy.orm import Session

from .models import init_db
from .db import FinanceDB


class AccountBalanceWidget(Static):
    """Display account balances."""

    db: Optional[FinanceDB] = None
    selected_account_id: reactive[Optional[int]] = reactive(None)

    def render(self) -> str:
        if not self.db or self.selected_account_id is None:
            return "[dim]No account selected[/dim]"

        account = self.db.get_account(self.selected_account_id)
        if not account:
            return "[dim]Account not found[/dim]"

        total_debt = self.db.get_total_debt(self.selected_account_id)
        net_worth = account.balance - total_debt

        display = f"""
[bold cyan]{account.name}[/bold cyan] ({account.account_type})
Balance: [bold green]${account.balance:,.2f}[/bold green]
Total Debt: [bold red]${total_debt:,.2f}[/bold red]
Net Worth: [bold yellow]${net_worth:,.2f}[/bold yellow]
"""
        return display.strip()

    def watch_selected_account_id(self) -> None:
        self.update(self.render())


class TransactionLedgerWidget(Static):
    """Display recent transactions."""

    db: Optional[FinanceDB] = None
    selected_account_id: reactive[Optional[int]] = reactive(None)

    def render(self) -> str:
        if not self.db or self.selected_account_id is None:
            return "[dim]No account selected[/dim]"

        transactions = self.db.get_transactions(self.selected_account_id, days=30)
        if not transactions:
            return "[dim]No transactions[/dim]"

        table = Table(title="Recent Transactions (30 days)")
        table.add_column("Date", style="cyan")
        table.add_column("Description", style="white")
        table.add_column("Category", style="yellow")
        table.add_column("Amount", style="green")

        for txn in transactions[:10]:  # Show last 10
            amount_style = "green" if txn.amount > 0 else "red"
            table.add_row(
                str(txn.transaction_date),
                txn.description or "N/A",
                txn.category,
                f"${txn.amount:,.2f}",
                style=amount_style
            )

        return str(table)

    def watch_selected_account_id(self) -> None:
        self.update(self.render())


class BudgetWidget(Static):
    """Display budget summary."""

    db: Optional[FinanceDB] = None
    selected_account_id: reactive[Optional[int]] = reactive(None)

    def render(self) -> str:
        if not self.db or self.selected_account_id is None:
            return "[dim]No account selected[/dim]"

        categories = self.db.get_budget_categories(self.selected_account_id)
        if not categories:
            return "[dim]No budget categories defined[/dim]"

        table = Table(title="Budget Summary (Weekly/Monthly)")
        table.add_column("Category", style="cyan")
        table.add_column("Weekly Spent", style="yellow")
        table.add_column("Weekly Limit", style="white")
        table.add_column("Monthly Spent", style="yellow")
        table.add_column("Monthly Limit", style="white")

        for cat in categories:
            weekly_spent, monthly_spent = self.db.get_spending_summary(
                self.selected_account_id, cat.name
            )

            weekly_style = "red" if weekly_spent > cat.weekly_limit else "green"
            monthly_style = "red" if monthly_spent > cat.monthly_limit else "green"

            table.add_row(
                cat.name,
                f"${weekly_spent:,.2f}",
                f"${cat.weekly_limit:,.2f}",
                f"${monthly_spent:,.2f}",
                f"${cat.monthly_limit:,.2f}",
                style="white"
            )

        return str(table)

    def watch_selected_account_id(self) -> None:
        self.update(self.render())


class DebtWidget(Static):
    """Display debt paydown progress."""

    db: Optional[FinanceDB] = None
    selected_account_id: reactive[Optional[int]] = reactive(None)

    def render(self) -> str:
        if not self.db or self.selected_account_id is None:
            return "[dim]No account selected[/dim]"

        debts = self.db.get_debts(self.selected_account_id)
        if not debts:
            return "[dim]No debts[/dim]"

        table = Table(title="Debt Paydown Progress")
        table.add_column("Creditor", style="cyan")
        table.add_column("Original", style="white")
        table.add_column("Remaining", style="yellow")
        table.add_column("Rate", style="white")
        table.add_column("Progress", style="green")

        for debt in debts:
            table.add_row(
                debt.creditor_name,
                f"${debt.original_amount:,.2f}",
                f"${debt.current_amount:,.2f}",
                f"{debt.interest_rate:.1f}%",
                f"{debt.paydown_progress:.1f}%"
            )

        return str(table)

    def watch_selected_account_id(self) -> None:
        self.update(self.render())


class MainScreen(Screen):
    """Main dashboard screen."""

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("n", "new_account", "New Account"),
        Binding("t", "new_transaction", "Add Transaction"),
        Binding("b", "new_budget", "Add Budget"),
        Binding("d", "new_debt", "Add Debt"),
    ]

    def __init__(self, session_maker):
        super().__init__()
        self.session = session_maker()
        self.db = FinanceDB(self.session)
        self.selected_account_id: Optional[int] = None

    def compose(self) -> ComposeResult:
        yield Label("[bold cyan]Finance Dashboard[/bold cyan]", id="title")
        with Horizontal(id="top"):
            yield Label("Select Account:", id="account-label")
            yield Select(
                [(acc.name, acc.id) for acc in self.db.list_accounts()],
                id="account-select"
            )
        yield AccountBalanceWidget(id="balance")
        with Horizontal(id="content"):
            with Vertical(id="left"):
                yield TransactionLedgerWidget(id="ledger")
            with Vertical(id="right"):
                yield BudgetWidget(id="budget")
        yield DebtWidget(id="debt")

    def on_mount(self) -> None:
        """Initialize the screen."""
        select = self.query_one("#account-select", Select)
        if self.db.list_accounts():
            select.focus()
        else:
            self.action_new_account()

    def on_select_changed(self, event: Select.Changed) -> None:
        """Handle account selection."""
        if event.value != Select.BLANK:
            self.selected_account_id = event.value
            self.update_widgets()

    def update_widgets(self) -> None:
        """Update all widgets with selected account."""
        balance_widget = self.query_one("#balance", AccountBalanceWidget)
        balance_widget.selected_account_id = self.selected_account_id

        ledger_widget = self.query_one("#ledger", TransactionLedgerWidget)
        ledger_widget.selected_account_id = self.selected_account_id

        budget_widget = self.query_one("#budget", BudgetWidget)
        budget_widget.selected_account_id = self.selected_account_id

        debt_widget = self.query_one("#debt", DebtWidget)
        debt_widget.selected_account_id = self.selected_account_id

    def action_new_account(self) -> None:
        """Create a new account."""
        self.app.push_screen(NewAccountScreen(self.db))

    def action_new_transaction(self) -> None:
        """Add a new transaction."""
        if not self.selected_account_id:
            return
        self.app.push_screen(NewTransactionScreen(self.db, self.selected_account_id))

    def action_new_budget(self) -> None:
        """Create a budget category."""
        if not self.selected_account_id:
            return
        self.app.push_screen(NewBudgetScreen(self.db, self.selected_account_id))

    def action_new_debt(self) -> None:
        """Create a debt entry."""
        if not self.selected_account_id:
            return
        self.app.push_screen(NewDebtScreen(self.db, self.selected_account_id))


class NewAccountScreen(Screen):
    """Screen for creating a new account."""

    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
    ]

    def __init__(self, db: FinanceDB):
        super().__init__()
        self.db = db

    def compose(self) -> ComposeResult:
        yield Label("[bold]Create New Account[/bold]")
        yield Label("Name:")
        yield Input(id="name")
        yield Label("Type (checking/savings/credit_card/loan):")
        yield Input(id="type", value="checking")
        yield Label("Initial Balance:")
        yield Input(id="balance", value="0.00")
        with Horizontal():
            yield Button("Create", id="create", variant="primary")
            yield Button("Cancel", id="cancel", variant="default")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press."""
        if event.button.id == "create":
            name = self.query_one("#name", Input).value.strip()
            account_type = self.query_one("#type", Input).value.strip()
            try:
                balance = float(self.query_one("#balance", Input).value)
            except ValueError:
                balance = 0.0

            if name:
                self.db.create_account(name, account_type, balance)
                self.app.pop_screen()
        elif event.button.id == "cancel":
            self.app.pop_screen()

    def action_cancel(self) -> None:
        """Cancel creation."""
        self.app.pop_screen()


class NewTransactionScreen(Screen):
    """Screen for adding a transaction."""

    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
    ]

    def __init__(self, db: FinanceDB, account_id: int):
        super().__init__()
        self.db = db
        self.account_id = account_id

    def compose(self) -> ComposeResult:
        yield Label("[bold]Add Transaction[/bold]")
        yield Label("Description:")
        yield Input(id="description")
        yield Label("Category:")
        yield Input(id="category")
        yield Label("Amount (negative for expense):")
        yield Input(id="amount", value="0.00")
        with Horizontal():
            yield Button("Add", id="add", variant="primary")
            yield Button("Cancel", id="cancel", variant="default")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press."""
        if event.button.id == "add":
            description = self.query_one("#description", Input).value.strip()
            category = self.query_one("#category", Input).value.strip()
            try:
                amount = float(self.query_one("#amount", Input).value)
            except ValueError:
                amount = 0.0

            if description and category:
                self.db.add_transaction(
                    self.account_id,
                    amount,
                    category,
                    description
                )
                self.app.pop_screen()
        elif event.button.id == "cancel":
            self.app.pop_screen()

    def action_cancel(self) -> None:
        """Cancel."""
        self.app.pop_screen()


class NewBudgetScreen(Screen):
    """Screen for creating a budget category."""

    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
    ]

    def __init__(self, db: FinanceDB, account_id: int):
        super().__init__()
        self.db = db
        self.account_id = account_id

    def compose(self) -> ComposeResult:
        yield Label("[bold]Create Budget Category[/bold]")
        yield Label("Category Name:")
        yield Input(id="name")
        yield Label("Weekly Limit:")
        yield Input(id="weekly", value="100.00")
        yield Label("Monthly Limit:")
        yield Input(id="monthly", value="400.00")
        with Horizontal():
            yield Button("Create", id="create", variant="primary")
            yield Button("Cancel", id="cancel", variant="default")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press."""
        if event.button.id == "create":
            name = self.query_one("#name", Input).value.strip()
            try:
                weekly = float(self.query_one("#weekly", Input).value)
                monthly = float(self.query_one("#monthly", Input).value)
            except ValueError:
                weekly = monthly = 0.0

            if name:
                self.db.create_budget_category(self.account_id, name, monthly, weekly)
                self.app.pop_screen()
        elif event.button.id == "cancel":
            self.app.pop_screen()

    def action_cancel(self) -> None:
        """Cancel."""
        self.app.pop_screen()


class NewDebtScreen(Screen):
    """Screen for creating a debt entry."""

    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
    ]

    def __init__(self, db: FinanceDB, account_id: int):
        super().__init__()
        self.db = db
        self.account_id = account_id

    def compose(self) -> ComposeResult:
        yield Label("[bold]Add Debt[/bold]")
        yield Label("Creditor Name:")
        yield Input(id="creditor")
        yield Label("Original Amount:")
        yield Input(id="original", value="0.00")
        yield Label("Current Amount:")
        yield Input(id="current", value="0.00")
        yield Label("Interest Rate (%):")
        yield Input(id="rate", value="0.0")
        yield Label("Monthly Payment:")
        yield Input(id="payment", value="100.00")
        with Horizontal():
            yield Button("Add", id="add", variant="primary")
            yield Button("Cancel", id="cancel", variant="default")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press."""
        if event.button.id == "add":
            creditor = self.query_one("#creditor", Input).value.strip()
            try:
                original = float(self.query_one("#original", Input).value)
                current = float(self.query_one("#current", Input).value)
                rate = float(self.query_one("#rate", Input).value)
                payment = float(self.query_one("#payment", Input).value)
            except ValueError:
                original = current = rate = payment = 0.0

            if creditor:
                self.db.create_debt(
                    self.account_id,
                    creditor,
                    original,
                    current,
                    rate,
                    payment
                )
                self.app.pop_screen()
        elif event.button.id == "cancel":
            self.app.pop_screen()

    def action_cancel(self) -> None:
        """Cancel."""
        self.app.pop_screen()


class FinanceDashboard:
    """Main application class."""

    def __init__(self, db_path: str = "finance.db"):
        self.session_maker = init_db(db_path)

    def run(self) -> None:
        """Run the TUI application."""
        from textual.app import App

        class DashboardApp(App):
            CSS = """
            Screen {
                layout: vertical;
                background: $surface;
                color: $text;
            }
            #title {
                dock: top;
                height: 1;
                background: $boost;
            }
            #top {
                dock: top;
                height: 3;
                border: solid $primary;
            }
            #balance {
                dock: top;
                height: 5;
                border: solid $accent;
            }
            #content {
                height: 1fr;
            }
            #left {
                width: 1fr;
            }
            #right {
                width: 1fr;
            }
            #ledger {
                height: 100%;
                border: solid $primary;
            }
            #budget {
                height: 100%;
                border: solid $primary;
            }
            #debt {
                dock: bottom;
                height: 10;
                border: solid $primary;
            }
            Input {
                margin: 0 1;
            }
            Button {
                margin: 0 1;
            }
            """

            def on_mount(self) -> None:
                self.push_screen(MainScreen(self.session_maker))

        app = DashboardApp()
        app.run()


if __name__ == "__main__":
    dashboard = FinanceDashboard()
    dashboard.run()
