# Finance Dashboard TUI

A terminal user interface dashboard for managing personal finances. Think "htop for money".

## Features

- **Account Management**: Multiple accounts with different types (checking, savings, credit card, loan)
- **Transaction Ledger**: Track transactions with categorization
- **Budgeting**: Set weekly and monthly spending limits per category
- **Debt Tracking**: Monitor debts with paydown progress visualization
- **Balance Summary**: Real-time view of account balances and net worth

## Architecture

### Core Components

- **models.py**: SQLAlchemy ORM models for Account, Transaction, BudgetCategory, and Debt
- **db.py**: High-level database access layer with business logic
- **app.py**: Textual TUI application with multiple screens

### Data Models

- **Account**: Stores account information and balance
- **Transaction**: Individual transactions with category and amount
- **BudgetCategory**: Spending limits (weekly/monthly) per category
- **Debt**: Debt entries with paydown tracking

### Key Features

1. **Multi-pane Dashboard**: 
   - Account balances and net worth
   - Recent transaction ledger
   - Budget summary with spending limits
   - Debt paydown progress

2. **Modal Forms**: Separate screens for creating accounts, transactions, budgets, and debts

3. **Dynamic Updates**: Reactive widgets automatically refresh when account selection changes

4. **Data Validation**: Input validation with default values for numeric fields

## Stack

- **TUI Framework**: Textual (built on Rich)
- **Database**: SQLite with SQLAlchemy ORM
- **Testing**: pytest with pytest-asyncio
- **Python**: 3.9+

## Installation

```bash
pip install -e .
pip install -e ".[test]"  # For testing
```

## Usage

```bash
python main.py
```

### Keyboard Controls

- `q` - Quit
- `n` - New Account
- `t` - Add Transaction
- `b` - Add Budget Category
- `d` - Add Debt
- `ESC` - Cancel dialog

## Testing

```bash
pytest tests/
```

Tests cover:
- Model creation and relationships
- Database CRUD operations
- Budget calculations
- Transaction filtering
- Debt paydown tracking

## Design Decisions

1. **Textual for TUI**: Rich ecosystem, responsive, handles complex layouts
2. **SQLAlchemy ORM**: Type-safe, handles relationships automatically, easy to extend
3. **SQLite**: Zero-config persistence, suitable for single-user local application
4. **Reactive widgets**: Textual's reactive decorator pattern keeps UI in sync with data
5. **Separate DB layer**: FinanceDB provides business logic abstraction

## Known Limitations

1. No multi-user support (single-user local application)
2. No data export/import (CSV, etc.)
3. No recurring transactions
4. No investment tracking
5. Interest calculation is manual (not automatic)
6. No backup/restore functionality

## Security Considerations

- SQLAlchemy parameterized queries prevent SQL injection
- Input validation on all numeric fields
- No network connectivity (local-only)
- SQLite database stored in working directory
