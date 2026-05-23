# Finance TUI Dashboard

A terminal user interface (TUI) dashboard for managing personal finances. Think "htop for money" - monitor all your accounts, transactions, budgets, and debts in real-time from the terminal.

## Features

- **Account Management**: Track checking, savings, and credit card accounts with real-time balances
- **Transaction Ledger**: Record and categorize all transactions with detailed history
- **Budget Tracking**: Set monthly budgets by category and monitor spending progress
- **Weekly/Monthly Summaries**: View spending patterns across time periods
- **Debt Management**: Track debts, monitor paydown progress, and manage monthly payments
- **Dashboard Statistics**: Quick overview of net worth, total balance, and total debt

## Architecture

### Backend
- **Framework**: FastAPI
- **Database**: SQLite with SQLAlchemy ORM
- **API**: RESTful endpoints for all operations

### Frontend
- **Framework**: Textual (modern TUI framework for Python)
- **Client**: AsyncIO HTTP client for API communication
- **Auto-refresh**: Real-time updates every 30 seconds

## Installation

### Requirements
- Python 3.10+
- pip or pipenv

### Setup

1. Install dependencies:
```bash
pip install -e ".[dev]"
```

2. Initialize the database with sample data:
```bash
python scripts/init_sample_data.py
```

## Running the Application

### Start the Backend Server
```bash
python run_backend.py
```

The API will be available at `http://localhost:8000`. You can view the API documentation at `http://localhost:8000/docs`.

### Start the Frontend (in another terminal)
```bash
python run_frontend.py
```

The TUI dashboard will display:
- Dashboard statistics (total balance, debt, net worth)
- All accounts with current balances
- Recent transactions with categories
- Monthly budget summaries with progress bars
- Debt tracking with paydown progress

## Keyboard Shortcuts

- `q`: Quit the application
- `r`: Manually refresh all data
- Arrow keys: Navigate (when applicable)

## API Endpoints

### Accounts
- `GET /api/accounts` - List all accounts
- `GET /api/accounts/{id}` - Get account details
- `POST /api/accounts` - Create account
- `PUT /api/accounts/{id}` - Update account balance

### Transactions
- `GET /api/transactions` - List all transactions
- `GET /api/accounts/{id}/transactions` - Get account transactions
- `POST /api/transactions` - Record transaction

### Budgets
- `GET /api/budgets` - List all budgets
- `POST /api/budgets` - Create budget
- `PUT /api/budgets/{category}` - Update budget
- `GET /api/budgets/summary/monthly` - Monthly summary
- `GET /api/budgets/summary/weekly` - Weekly summary

### Debts
- `GET /api/debts` - List all debts
- `GET /api/debts/{id}` - Get debt details
- `POST /api/debts` - Create debt
- `PUT /api/debts/{id}` - Update debt

### Dashboard
- `GET /api/dashboard/stats` - Get dashboard statistics

## Transaction Categories

- `income` - Income transactions
- `groceries` - Grocery shopping
- `dining` - Restaurants and food delivery
- `transportation` - Gas, public transit, ride shares
- `utilities` - Bills and utilities
- `entertainment` - Movies, games, hobbies
- `healthcare` - Medical expenses
- `shopping` - Retail purchases
- `debt_payment` - Debt payments
- `savings` - Savings transfers
- `other` - Miscellaneous

## Account Types

- `checking` - Checking account
- `savings` - Savings account
- `credit_card` - Credit card account

## Testing

Run the test suite:
```bash
pytest tests/ -v
```

With coverage:
```bash
pytest tests/ --cov=src --cov-report=html
```

## Database

The application uses SQLite for persistence. The database file (`finance.db`) is created automatically in the project root.

### Models

- **Account**: Bank/credit accounts with balance tracking
- **Transaction**: Individual transactions with category and date
- **Budget**: Monthly spending limits by category
- **Debt**: Debt tracking with principal, remaining, interest rate, and payment amount

## Development

### Code Style
- Black for formatting
- Ruff for linting
- MyPy for type checking

### Type Safety
The codebase uses Python type hints throughout for better code quality and IDE support.

## Data Persistence

All data is stored locally in SQLite. The database schema is automatically created on first run.

## Example Usage

### Create an Account
```bash
curl -X POST http://localhost:8000/api/accounts \
  -H "Content-Type: application/json" \
  -d '{"name": "Checking", "account_type": "checking", "balance": 5000}'
```

### Record a Transaction
```bash
curl -X POST http://localhost:8000/api/transactions \
  -H "Content-Type: application/json" \
  -d '{
    "account_id": 1,
    "amount": 50.0,
    "category": "groceries",
    "description": "Grocery shopping"
  }'
```

### Create a Budget
```bash
curl -X POST http://localhost:8000/api/budgets \
  -H "Content-Type: application/json" \
  -d '{"category": "groceries", "monthly_limit": 500}'
```

### Track a Debt
```bash
curl -X POST http://localhost:8000/api/debts \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Student Loan",
    "principal": 50000,
    "interest_rate": 4.5,
    "monthly_payment": 450,
    "description": "Federal student loan"
  }'
```

## Limitations

- Single-user local application (no authentication/authorization)
- No data sync across devices (local SQLite only)
- No automatic transaction import from banks
- No data export to CSV/PDF
- Terminal must support ANSI color codes

## Future Enhancements

- Bank account integration via API
- Data export functionality
- Multi-user support with authentication
- Mobile app companion
- Advanced reporting and analytics
- Forecast and projection features
- Category rules and automatic tagging
