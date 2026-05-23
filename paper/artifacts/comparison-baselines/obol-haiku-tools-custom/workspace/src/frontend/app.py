"""Finance TUI Dashboard Application."""
import asyncio
from datetime import datetime, timedelta
from typing import Optional

import httpx
from textual.app import ComposeResult, on
from textual.containers import Container, Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import (
    Button,
    DataTable,
    Footer,
    Header,
    Input,
    Label,
    Select,
    Static,
    TabbedContent,
    TabPane,
    TextArea,
)

from src.backend.database import TransactionCategory

API_BASE_URL = "http://localhost:8000/api"


class APIClient:
    """HTTP client for API communication."""

    def __init__(self, base_url: str = API_BASE_URL):
        """Initialize API client."""
        self.base_url = base_url
        self.client = httpx.AsyncClient(base_url=base_url, timeout=10.0)

    async def get(self, endpoint: str, **params):
        """Make GET request."""
        try:
            response = await self.client.get(endpoint, params=params)
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as e:
            raise Exception(f"API request failed: {e}")

    async def post(self, endpoint: str, json_data: dict):
        """Make POST request."""
        try:
            response = await self.client.post(endpoint, json=json_data)
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as e:
            raise Exception(f"API request failed: {e}")

    async def put(self, endpoint: str, json_data: dict):
        """Make PUT request."""
        try:
            response = await self.client.put(endpoint, json=json_data)
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as e:
            raise Exception(f"API request failed: {e}")

    async def close(self):
        """Close client."""
        await self.client.aclose()


class DashboardWidget(Static):
    """Dashboard statistics widget."""

    def __init__(self, api_client: APIClient):
        """Initialize dashboard widget."""
        super().__init__()
        self.api_client = api_client
        self.stats = None

    async def on_mount(self) -> None:
        """Load dashboard stats on mount."""
        await self.refresh_stats()

    async def refresh_stats(self) -> None:
        """Refresh dashboard statistics."""
        try:
            self.stats = await self.api_client.get("/dashboard/stats")
            self.update(self._render_stats())
        except Exception as e:
            self.update(f"Error loading dashboard: {e}")

    def _render_stats(self) -> str:
        """Render dashboard statistics."""
        if not self.stats:
            return "Loading..."

        s = self.stats
        net_worth_color = "green" if s["net_worth"] >= 0 else "red"

        return f"""
╔════════════════════════════════════════════╗
║         FINANCIAL DASHBOARD                 ║
╠════════════════════════════════════════════╣
║ Total Balance:    ${s['total_balance']:>15.2f}   ║
║ Total Debt:       ${s['total_debt']:>15.2f}   ║
║ Net Worth:        ${s['net_worth']:>15.2f}   ║
║                                             ║
║ Accounts:         {s['accounts_count']:>15}   ║
║ Transactions:     {s['transactions_count']:>15}   ║
╚════════════════════════════════════════════╝
"""

    def render(self) -> str:
        """Render the widget."""
        return self._render_stats() if self.stats else "Loading..."


class AccountsWidget(Static):
    """Accounts display widget."""

    def __init__(self, api_client: APIClient):
        """Initialize accounts widget."""
        super().__init__()
        self.api_client = api_client
        self.accounts = []

    async def on_mount(self) -> None:
        """Load accounts on mount."""
        await self.refresh_accounts()

    async def refresh_accounts(self) -> None:
        """Refresh accounts list."""
        try:
            self.accounts = await self.api_client.get("/accounts")
            self.update(self._render_accounts())
        except Exception as e:
            self.update(f"Error loading accounts: {e}")

    def _render_accounts(self) -> str:
        """Render accounts list."""
        if not self.accounts:
            return "No accounts found."

        header = "╔═══════════════════════════════════════════════════════════╗\n"
        header += "║ ACCOUNTS                                                  ║\n"
        header += "╠═════════════════════╦════════════════╦═══════════════════╣\n"
        header += "║ Name                ║ Type           ║ Balance           ║\n"
        header += "╠═════════════════════╬════════════════╬═══════════════════╣\n"

        rows = ""
        for acc in self.accounts:
            name = acc["name"][:19].ljust(19)
            acc_type = acc["account_type"][:14].ljust(14)
            balance = f"${acc['balance']:>13.2f}".rjust(17)
            rows += f"║ {name} ║ {acc_type} ║ {balance} ║\n"

        footer = "╚═════════════════════╩════════════════╩═══════════════════╝\n"

        return header + rows + footer

    def render(self) -> str:
        """Render the widget."""
        return self._render_accounts()


class TransactionsWidget(Static):
    """Transactions display widget."""

    def __init__(self, api_client: APIClient):
        """Initialize transactions widget."""
        super().__init__()
        self.api_client = api_client
        self.transactions = []
        self.page = 0
        self.per_page = 10

    async def on_mount(self) -> None:
        """Load transactions on mount."""
        await self.refresh_transactions()

    async def refresh_transactions(self) -> None:
        """Refresh transactions list."""
        try:
            all_txns = await self.api_client.get("/transactions")
            self.transactions = sorted(all_txns, key=lambda x: x["date"], reverse=True)
            self.page = 0
            self.update(self._render_transactions())
        except Exception as e:
            self.update(f"Error loading transactions: {e}")

    def _render_transactions(self) -> str:
        """Render transactions list."""
        if not self.transactions:
            return "No transactions found."

        start = self.page * self.per_page
        end = start + self.per_page
        page_txns = self.transactions[start:end]

        header = "╔════════════════════════════════════════════════════════════════════════════╗\n"
        header += "║ TRANSACTIONS                                                               ║\n"
        header += "╠═══════════════════════╦═════════════════╦══════════════╦═════════════════╣\n"
        header += "║ Date                  ║ Description     ║ Category     ║ Amount          ║\n"
        header += "╠═══════════════════════╬═════════════════╬══════════════╬═════════════════╣\n"

        rows = ""
        for txn in page_txns:
            date_str = datetime.fromisoformat(txn["date"]).strftime("%Y-%m-%d %H:%M")[:21].ljust(21)
            desc = txn["description"][:15].ljust(15)
            cat = txn["category"][:12].ljust(12)
            amount = f"${txn['amount']:>12.2f}".rjust(15)
            rows += f"║ {date_str} ║ {desc} ║ {cat} ║ {amount} ║\n"

        footer = "╚═══════════════════════╩═════════════════╩══════════════╩═════════════════╝\n"
        info = f"Page {self.page + 1} of {(len(self.transactions) + self.per_page - 1) // self.per_page}"

        return header + rows + footer + info

    def render(self) -> str:
        """Render the widget."""
        return self._render_transactions()


class BudgetWidget(Static):
    """Budget display widget."""

    def __init__(self, api_client: APIClient):
        """Initialize budget widget."""
        super().__init__()
        self.api_client = api_client
        self.budgets = []
        self.current_date = datetime.now()

    async def on_mount(self) -> None:
        """Load budgets on mount."""
        await self.refresh_budgets()

    async def refresh_budgets(self) -> None:
        """Refresh budgets list."""
        try:
            summary = await self.api_client.get(
                "/budgets/summary/monthly",
                year=self.current_date.year,
                month=self.current_date.month,
            )
            self.budgets = summary
            self.update(self._render_budgets())
        except Exception as e:
            self.update(f"Error loading budgets: {e}")

    def _render_budgets(self) -> str:
        """Render budgets."""
        if not self.budgets:
            return "No budgets configured."

        header = f"╔══════════════════════════════════════════════════════════════╗\n"
        header += f"║ BUDGET ({self.current_date.strftime('%B %Y')})                   \n"
        header += f"╠════════════════╦═════════════╦═════════════╦═════════════════╣\n"
        header += f"║ Category       ║ Spent       ║ Limit       ║ Progress        ║\n"
        header += f"╠════════════════╬═════════════╬═════════════╬═════════════════╣\n"

        rows = ""
        for budget in self.budgets:
            cat = budget["category"][:14].ljust(14)
            spent = f"${budget['spent']:>10.2f}".rjust(11)
            limit = f"${budget['limit']:>10.2f}".rjust(11)
            pct = budget["percentage"]
            bar_len = 13
            filled = int(bar_len * pct / 100)
            bar = "█" * filled + "░" * (bar_len - filled)
            progress = f"{pct:>5.0f}%".rjust(15)
            rows += f"║ {cat} ║ {spent} ║ {limit} ║ {bar} {progress} ║\n"

        footer = "╚════════════════╩═════════════╩═════════════╩═════════════════╝\n"

        return header + rows + footer

    def render(self) -> str:
        """Render the widget."""
        return self._render_budgets()


class DebtWidget(Static):
    """Debt display widget."""

    def __init__(self, api_client: APIClient):
        """Initialize debt widget."""
        super().__init__()
        self.api_client = api_client
        self.debts = []

    async def on_mount(self) -> None:
        """Load debts on mount."""
        await self.refresh_debts()

    async def refresh_debts(self) -> None:
        """Refresh debts list."""
        try:
            self.debts = await self.api_client.get("/debts")
            self.update(self._render_debts())
        except Exception as e:
            self.update(f"Error loading debts: {e}")

    def _render_debts(self) -> str:
        """Render debts."""
        if not self.debts:
            return "No debts tracked."

        header = "╔════════════════════════════════════════════════════════════════════════════════════╗\n"
        header += "║ DEBTS & PAYDOWN PROGRESS                                                         ║\n"
        header += "╠═══════════════════╦═══════════════╦═══════════════╦═══════════════╦════════════════╣\n"
        header += "║ Name              ║ Remaining     ║ Payment       ║ Rate (%)      ║ Progress       ║\n"
        header += "╠═══════════════════╬═══════════════╬═══════════════╬═══════════════╬════════════════╣\n"

        rows = ""
        for debt in self.debts:
            name = debt["name"][:17].ljust(17)
            remaining = f"${debt['remaining']:>11.2f}".rjust(13)
            payment = f"${debt['monthly_payment']:>11.2f}".rjust(13)
            rate = f"{debt['interest_rate']:>11.2f}".rjust(13)
            progress = debt["paydown_progress"]
            bar_len = 12
            filled = int(bar_len * progress / 100)
            bar = "█" * filled + "░" * (bar_len - filled)
            prog_str = f"{progress:>5.1f}%".rjust(14)
            rows += f"║ {name} ║ {remaining} ║ {payment} ║ {rate} ║ {bar} {prog_str} ║\n"

        footer = "╚═══════════════════╩═══════════════╩═══════════════╩═══════════════╩════════════════╝\n"

        return header + rows + footer

    def render(self) -> str:
        """Render the widget."""
        return self._render_debts()


class FinanceApp(Screen):
    """Main Finance TUI Application."""

    CSS = """
    Screen {
        layout: vertical;
        background: $surface;
        color: $text;
    }

    DashboardWidget {
        width: 100%;
        height: auto;
        border: solid $accent;
    }

    AccountsWidget {
        width: 100%;
        height: auto;
        border: solid $accent;
    }

    TransactionsWidget {
        width: 100%;
        height: auto;
        border: solid $accent;
    }

    BudgetWidget {
        width: 100%;
        height: auto;
        border: solid $accent;
    }

    DebtWidget {
        width: 100%;
        height: auto;
        border: solid $accent;
    }

    Header {
        dock: top;
        height: 3;
    }

    Footer {
        dock: bottom;
        height: 1;
    }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("r", "refresh", "Refresh"),
    ]

    def __init__(self):
        """Initialize the application."""
        super().__init__()
        self.api_client = APIClient()
        self.refresh_task = None

    async def on_mount(self) -> None:
        """Set up widgets on mount."""
        # Create widgets
        dashboard = DashboardWidget(self.api_client)
        accounts = AccountsWidget(self.api_client)
        transactions = TransactionsWidget(self.api_client)
        budgets = BudgetWidget(self.api_client)
        debts = DebtWidget(self.api_client)

        # Mount in container
        self.mount(
            Header(),
            dashboard,
            accounts,
            transactions,
            budgets,
            debts,
            Footer(),
        )

        # Start auto-refresh
        self.refresh_task = asyncio.create_task(self._auto_refresh())

    async def _auto_refresh(self) -> None:
        """Auto-refresh data every 30 seconds."""
        while True:
            try:
                await asyncio.sleep(30)
                await self.action_refresh()
            except asyncio.CancelledError:
                break

    def action_refresh(self) -> None:
        """Refresh all widgets."""
        for widget in self.query("*"):
            if hasattr(widget, "refresh_accounts"):
                asyncio.create_task(widget.refresh_accounts())
            if hasattr(widget, "refresh_stats"):
                asyncio.create_task(widget.refresh_stats())
            if hasattr(widget, "refresh_transactions"):
                asyncio.create_task(widget.refresh_transactions())
            if hasattr(widget, "refresh_budgets"):
                asyncio.create_task(widget.refresh_budgets())
            if hasattr(widget, "refresh_debts"):
                asyncio.create_task(widget.refresh_debts())

    def action_quit(self) -> None:
        """Quit the application."""
        if self.refresh_task:
            self.refresh_task.cancel()
        self.app.exit()


class FinanceTUIApp:
    """Main TUI Application."""

    def __init__(self):
        """Initialize TUI app."""
        from textual.app import App

        class FinanceScreen(App):
            """Textual Finance App."""

            TITLE = "Finance Dashboard"
            CSS = """
            Screen {
                background: $surface;
                color: $text;
            }
            """

            def __init__(self):
                """Initialize."""
                super().__init__()
                self.api_client = APIClient()

            async def on_mount(self) -> None:
                """Mount widgets."""
                dashboard = DashboardWidget(self.api_client)
                accounts = AccountsWidget(self.api_client)
                transactions = TransactionsWidget(self.api_client)
                budgets = BudgetWidget(self.api_client)
                debts = DebtWidget(self.api_client)

                from textual.containers import ScrollableContainer

                container = ScrollableContainer(
                    dashboard,
                    accounts,
                    transactions,
                    budgets,
                    debts,
                )

                self.mount(
                    Header(show_clock=True),
                    container,
                    Footer(),
                )

                # Auto-refresh
                self.call_later(self._auto_refresh)

            async def _auto_refresh(self) -> None:
                """Auto-refresh every 30 seconds."""
                while True:
                    try:
                        await asyncio.sleep(30)
                        for widget in self.query("*"):
                            if hasattr(widget, "refresh_accounts"):
                                await widget.refresh_accounts()
                            if hasattr(widget, "refresh_stats"):
                                await widget.refresh_stats()
                            if hasattr(widget, "refresh_transactions"):
                                await widget.refresh_transactions()
                            if hasattr(widget, "refresh_budgets"):
                                await widget.refresh_budgets()
                            if hasattr(widget, "refresh_debts"):
                                await widget.refresh_debts()
                    except asyncio.CancelledError:
                        break

            BINDINGS = [
                ("q", "quit", "Quit"),
                ("r", "refresh", "Refresh"),
            ]

            def action_quit(self) -> None:
                """Quit."""
                self.exit()

            def action_refresh(self) -> None:
                """Manual refresh."""
                self.call_later(self._trigger_refresh)

            async def _trigger_refresh(self) -> None:
                """Trigger refresh."""
                for widget in self.query("*"):
                    if hasattr(widget, "refresh_accounts"):
                        await widget.refresh_accounts()
                    if hasattr(widget, "refresh_stats"):
                        await widget.refresh_stats()
                    if hasattr(widget, "refresh_transactions"):
                        await widget.refresh_transactions()
                    if hasattr(widget, "refresh_budgets"):
                        await widget.refresh_budgets()
                    if hasattr(widget, "refresh_debts"):
                        await widget.refresh_debts()

        self.app = FinanceScreen()

    def run(self) -> None:
        """Run the application."""
        self.app.run()


if __name__ == "__main__":
    app = FinanceTUIApp()
    app.run()
