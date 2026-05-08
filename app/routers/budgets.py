from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.routers.auth import get_current_user
from app.schemas.budget import (
    BudgetAlert,
    BudgetCreate,
    BudgetResponse,
    BudgetUpdate,
)
from app.services.budget_service import (
    create_budget,
    delete_budget,
    list_alerts,
    list_budgets,
    update_budget,
)

router = APIRouter(prefix="/budgets", tags=["budgets"])


@router.post("", response_model=BudgetResponse)
def create_budget_route(
    data: BudgetCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return create_budget(db, current_user, data)


@router.get("", response_model=list[BudgetResponse])
def list_budgets_route(
    year: int | None = Query(default=None),
    month: int | None = Query(default=None, ge=1, le=12),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return list_budgets(db, current_user, year=year, month=month)


@router.get("/alerts", response_model=list[BudgetAlert])
def list_alerts_route(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return list_alerts(db, current_user)


@router.put("/{budget_id}", response_model=BudgetResponse)
def update_budget_route(
    budget_id: UUID,
    data: BudgetUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return update_budget(db, current_user, budget_id, data)


@router.delete("/{budget_id}")
def delete_budget_route(
    budget_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    delete_budget(db, current_user, budget_id)
    return {"message": "Presupuesto eliminado correctamente"}
