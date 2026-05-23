# Installation and Setup Guide

## Prerequisites

- Python 3.10 or higher
- pip (Python package manager)
- A terminal that supports ANSI colors

## Quick Start

### 1. Clone or Navigate to Project Directory

```bash
cd finance-tui
```

### 2. Create and Activate Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate it
# On Linux/macOS:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -e ".[dev]"
```

This installs all required packages including:
- FastAPI and Uvicorn for the backend API
- Textual for the TUI frontend
- SQLAlchemy for database ORM
- Pydantic for data validation
- httpx for async HTTP requests
- Testing tools (pytest, pytest-asyncio, etc.)

### 4. Initialize Sample Data

```bash
python scripts/init_sample_data.py
```

This creates:
- 3 sample accounts (Checking, Savings, Credit Card)
- 5 sample budgets (Groceries, Dining, Transportation, Utilities, Entertainment)
- 13 sample transactions from the past month
- 3 sample debts (Student Loan, Credit Card Debt, Auto Loan)

You'll see output like:
```
✓ Created accounts: Checking, Savings, Credit Card
✓ Created budgets for: Groceries, Dining, Transportation, Utilities, Entertainment
✓ Created 13 transactions
✓ Created 3 debts: Student Loan, Credit Card, Auto Loan

✓ Sample data initialized successfully!
```

### 5. Run Tests (Optional but Recommended)

```bash
pytest tests/ -v
```

All 43 tests should pass:
```
======================= 43 passed in X.XXs =======================
```

## Running the Application

### Terminal 1: Start Backend API Server

```bash
python run_backend.py
```

You'll see:
```
INFO:     Started server process [PID]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000
```

The API server is now running at `http://localhost:8000`

You can view API documentation at: `http://localhost:8000/docs`

### Terminal 2: Start TUI Frontend

In a new terminal (with venv activated):

```bash
python run_frontend.py
```

The TUI dashboard will display with:
- Dashboard statistics (top)
- Account balances
- Recent transactions
- Monthly budget tracking
- Debt paydown progress

## Using the TUI Dashboard

### Keyboard Controls

- **q**: Quit the application
- **r**: Manually refresh all data
- **Arrow Keys**: Navigate when applicable

### Dashboard Sections

1. **Dashboard Statistics**
   - Total Balance across all accounts
   - Total remaining debt
   - Net Worth (Balance - Debt)
   - Number of accounts
   - Number of transactions

2. **Accounts**
   - All accounts with current balances
   - Account types (checking, savings, credit_card)

3. **Transactions**
   - Recent transactions with dates
   - Transaction category
   - Amount
   - Organized by date (newest first)

4. **Monthly Budget**
   - Budget limits by category
   - Current spending
   - Remaining budget
   - Visual progress bars showing % spent

5. **Debts**
   - All tracked debts
   - Remaining balance
   - Monthly payment amount
   - Interest rate
   - Paydown progress percentage

### Data Refresh

The dashboard automatically refreshes every 30 seconds. You can also press **r** to manually refresh immediately.

## API Endpoints Reference

### Health Check
- `GET /docs` - Interactive API documentation
- `GET /redoc` - ReDoc API documentation

### Accounts
- `GET /api/accounts` - List all accounts
- `GET /api/accounts/{id}` - Get specific account
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
- `GET /api/budgets/summary/monthly?year=YYYY&month=MM` - Monthly summary
- `GET /api/budgets/summary/weekly?week_start=YYYY-MM-DD` - Weekly summary

### Debts
- `GET /api/debts` - List all debts
- `GET /api/debts/{id}` - Get specific debt
- `POST /api/debts` - Create debt
- `PUT /api/debts/{id}` - Update debt

### Dashboard
- `GET /api/dashboard/stats` - Get dashboard statistics

## API Examples

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
    "description": "Whole Foods"
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
    "monthly_payment": 450
  }'
```

## Database

The application uses SQLite for data persistence:
- **Database File**: `finance.db` (created automatically in project root)
- **Schema**: Automatically created on first run
- **Backup**: Simply copy `finance.db` to backup

### Database Tables

- **accounts**: Bank/credit accounts
- **transactions**: Individual transaction records
- **budgets**: Monthly spending limits by category
- **debts**: Debt tracking with paydown progress

## Configuration

### API Port

To change the API port (default: 8000), edit `run_backend.py`:

```python
uvicorn.run(app, host="127.0.0.1", port=8080)  # Change 8000 to desired port
```

Then update `API_BASE_URL` in `src/frontend/app.py`:

```python
API_BASE_URL = "http://localhost:8080/api"
```

## Troubleshooting

### Port Already in Use

If port 8000 is already in use:

```bash
# On Linux/macOS
lsof -i :8000

# On Windows
netstat -ano | findstr :8000
```

Then either:
1. Kill the process using that port
2. Change the port in `run_backend.py`

### TUI Not Displaying Correctly

Ensure your terminal:
- Supports ANSI colors
- Is not too small (minimum ~80x24 characters)
- Uses a monospace font

Try in a different terminal or terminal emulator if issues persist.

### Database Lock Issues

If you get "database is locked" errors:
- Ensure only one backend server is running
- Restart the backend server

### API Connection Issues

If the TUI shows "Error loading" in all sections:
- Verify backend is running: `curl http://localhost:8000/docs`
- Check firewall settings
- Verify API_BASE_URL in frontend/app.py matches your setup

## Development

### Running Tests

```bash
# All tests
pytest tests/ -v

# Specific test file
pytest tests/test_services.py -v

# With coverage
pytest tests/ --cov=src --cov-report=html
```

### Code Quality

```bash
# Format code
black src/ tests/

# Lint
ruff check src/ tests/

# Type checking
mypy src/
```

### Adding Features

1. Update database models in `src/backend/database.py`
2. Add business logic in `src/backend/services.py`
3. Add API endpoints in `src/backend/main.py`
4. Add validation schemas in `src/backend/schemas.py`
5. Update TUI widgets in `src/frontend/app.py`
6. Add tests in `tests/`

## Stopping the Application

To stop the application:

**In Terminal with TUI**: Press **q** to quit

**In Terminal with Backend**: Press **Ctrl+C** to stop the server

Both should shutdown gracefully.

## Next Steps

After installation:

1. **Explore the TUI**: Check out different sections and views
2. **Add Your Data**: Create your own accounts and transactions
3. **Customize Budgets**: Set monthly budgets for your spending categories
4. **Track Debts**: Add your debts and monitor paydown progress
5. **Monitor Progress**: Use the dashboard to track net worth and debt paydown

## Support

For issues or questions:

1. Check the README.md for feature overview
2. Review test files for usage examples
3. Check API documentation at `http://localhost:8000/docs`
4. Review source code comments and docstrings

Happy budgeting! 💰
