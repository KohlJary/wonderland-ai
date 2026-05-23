"""FastAPI backend server."""
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session

from src.backend.database import TransactionCategory, get_db, init_db
from src.backend.schemas import (
    AccountCreate,
    AccountResponse,
    AccountUpdate,
    BudgetCreate,
    BudgetResponse,
    BudgetUpdate,
    DashboardStats,
    DebtCreate,
    DebtResponse,
    DebtUpdate,
    MonthlyBudgetSummary,
    TransactionCreate,
    TransactionResponse,
    WeeklyBudgetSummary,
)
from src.backend.services import (
    AccountService,
    BudgetService,
    DebtService,
    TransactionService,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database on startup."""
    init_db()
    yield


app = FastAPI(title="Finance TUI API", version="0.1.0", lifespan=lifespan)


# ============================================================================
# Accounts Endpoints
# ============================================================================


@app.get("/api/accounts", response_model=list[AccountResponse])
def get_accounts(db: Session = Depends(get_db)):
    """Get all accounts."""
    return AccountService.get_all_accounts(db)


@app.get("/api/accounts/{account_id}", response_model=AccountResponse)
def get_account(account_id: int, db: Session = Depends(get_db)):
    """Get account by ID."""
    account = AccountService.get_account(db, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    return account


@app.post("/api/accounts", response_model=AccountResponse)
def create_account(data: AccountCreate, db: Session = Depends(get_db)):
    """Create a new account."""
    try:
        return AccountService.create_account(db, data.name, data.account_type, data.balance)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.put("/api/accounts/{account_id}", response_model=AccountResponse)
def update_account(account_id: int, data: AccountUpdate, db: Session = Depends(get_db)):
    """Update account balance."""
    account = AccountService.update_account_balance(db, account_id, data.balance)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    return account


# ============================================================================
# Transactions Endpoints
# ============================================================================


@app.get("/api/transactions", response_model=list[TransactionResponse])
def get_transactions(db: Session = Depends(get_db)):
    """Get all transactions."""
    return TransactionService.get_all_transactions(db)


@app.get("/api/accounts/{account_id}/transactions", response_model=list[TransactionResponse])
def get_account_transactions(account_id: int, db: Session = Depends(get_db)):
    """Get transactions for an account."""
    return TransactionService.get_account_transactions(db, account_id)


@app.post("/api/transactions", response_model=TransactionResponse)
def create_transaction(data: TransactionCreate, db: Session = Depends(get_db)):
    """Create a new transaction."""
    account = AccountService.get_account(db, data.account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    try:
        return TransactionService.create_transaction(
            db,
            data.account_id,
            data.amount,
            data.category,
            data.description,
            data.date,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# Budgets Endpoints
# ============================================================================


@app.get("/api/budgets", response_model=list[BudgetResponse])
def get_budgets(db: Session = Depends(get_db)):
    """Get all budgets."""
    return BudgetService.get_all_budgets(db)


@app.post("/api/budgets", response_model=BudgetResponse)
def create_budget(data: BudgetCreate, db: Session = Depends(get_db)):
    """Create a new budget."""
    existing = BudgetService.get_budget(db, data.category)
    if existing:
        raise HTTPException(status_code=400, detail="Budget for this category already exists")

    try:
        return BudgetService.create_budget(db, data.category, data.monthly_limit)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.put("/api/budgets/{category}", response_model=BudgetResponse)
def update_budget(category: str, data: BudgetUpdate, db: Session = Depends(get_db)):
    """Update budget."""
    try:
        cat = TransactionCategory(category)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid category")

    budget = BudgetService.update_budget(db, cat, data.monthly_limit)
    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")
    return budget


@app.get("/api/budgets/summary/monthly", response_model=list[MonthlyBudgetSummary])
def get_monthly_summary(year: int, month: int, db: Session = Depends(get_db)):
    """Get monthly budget summary."""
    try:
        return BudgetService.get_monthly_summary(db, year, month)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/budgets/summary/weekly", response_model=WeeklyBudgetSummary)
def get_weekly_summary(week_start: str, db: Session = Depends(get_db)):
    """Get weekly budget summary."""
    try:
        from datetime import datetime
        ws = datetime.fromisoformat(week_start)
        return BudgetService.get_weekly_summary(db, ws)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# Debts Endpoints
# ============================================================================


@app.get("/api/debts", response_model=list[DebtResponse])
def get_debts(db: Session = Depends(get_db)):
    """Get all debts."""
    debts = DebtService.get_all_debts(db)
    return [DebtResponse.from_orm(d) for d in debts]


@app.get("/api/debts/{debt_id}", response_model=DebtResponse)
def get_debt(debt_id: int, db: Session = Depends(get_db)):
    """Get debt by ID."""
    debt = DebtService.get_debt(db, debt_id)
    if not debt:
        raise HTTPException(status_code=404, detail="Debt not found")
    return DebtResponse.from_orm(debt)


@app.post("/api/debts", response_model=DebtResponse)
def create_debt(data: DebtCreate, db: Session = Depends(get_db)):
    """Create a new debt."""
    try:
        debt = DebtService.create_debt(
            db,
            data.name,
            data.principal,
            data.interest_rate,
            data.monthly_payment,
            data.description,
        )
        return DebtResponse.from_orm(debt)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.put("/api/debts/{debt_id}", response_model=DebtResponse)
def update_debt(debt_id: int, data: DebtUpdate, db: Session = Depends(get_db)):
    """Update debt."""
    debt = DebtService.get_debt(db, debt_id)
    if not debt:
        raise HTTPException(status_code=404, detail="Debt not found")

    try:
        debt = DebtService.update_debt_remaining(db, debt_id, data.remaining)
        debt = DebtService.update_debt_payment(db, debt_id, data.monthly_payment)
        return DebtResponse.from_orm(debt)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# Dashboard Endpoints
# ============================================================================


@app.get("/api/dashboard/stats", response_model=DashboardStats)
def get_dashboard_stats(db: Session = Depends(get_db)):
    """Get dashboard statistics."""
    total_balance = AccountService.get_total_balance(db)
    total_debt = DebtService.get_total_debt(db)
    accounts = AccountService.get_all_accounts(db)
    transactions = TransactionService.get_all_transactions(db)

    return DashboardStats(
        total_balance=total_balance,
        total_debt=total_debt,
        net_worth=total_balance - total_debt,
        accounts_count=len(accounts),
        transactions_count=len(transactions),
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
