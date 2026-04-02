from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.routers.auth import router as auth_router
from app.routers.accounts import router as accounts_router
from app.routers.category import router as categories_router
from app.routers.transaction import router as transactions_router

from app.db.base import Base
from app.db.session import engine, get_db

from app.models.user import User
from app.models.account import Account
from app.models.category import Category
from app.models.transaction import Transaction

Base.metadata.create_all(bind=engine)

app = FastAPI(title="FinanceGO")

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

@app.get("/health")
def health_check():
    return {"status": "OK"}

@app.get("/db-test")
def db_test(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {"db": "ok"}


