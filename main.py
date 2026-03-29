from fastapi import FastAPI, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.routers.auth import router as auth_router
from app.routers.accounts import router as accounts_router
from app.db.base import Base
from app.db.session import engine, get_db

from app.models.user import User
from app.models.account import Account


Base.metadata.create_all(bind=engine)

app = FastAPI(title="FinanceGO")
app.include_router(auth_router)
app.include_router(accounts_router)

@app.get("/health")
def health_check():
    return {"status": "OK"}

@app.get("/db-test")
def db_test(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {"db": "ok"}