from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.core.limiter import limiter

from app.routers.auth import router as auth_router
from app.routers.accounts import router as accounts_router
from app.routers.category import router as categories_router
from app.routers.transaction import router as transactions_router
from app.routers.debts import router as debts_router
from app.routers.budgets import router as budgets_router

from app.db.base import Base
from app.db.session import engine

from app.models.user import User
from app.models.account import Account
from app.models.category import Category
from app.models.transaction import Transaction
from app.models.debt import Debt
from app.models.debt_payment import DebtPayment
from app.models.budget import Budget

Base.metadata.create_all(bind=engine)

app = FastAPI(title="FinanceGO")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "https://app.financego.cloud",
        "https://dash.financego.cloud",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(accounts_router)
app.include_router(categories_router)
app.include_router(transactions_router)
app.include_router(debts_router)
app.include_router(budgets_router)

@app.get("/health")
def health_check():
    return {"status": "OK"}
