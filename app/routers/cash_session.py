# app/routers/cash_session.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from decimal import Decimal

from app.database import get_db
from app.core.permissions import admin_required
from app.models.cash_session import CashSession
from app.services.cash_session_service import CashSessionService
from app.schemas.cash_session_schema import CashSessionRead

router = APIRouter(prefix="/cash", tags=["Cash / PDV"])


@router.post("/open", response_model=CashSessionRead, dependencies=[Depends(admin_required)])
def open_cash(
        cash_register_id: int,
        opening_balance: Decimal,
        db: Session = Depends(get_db),
        user_id: int = 1
) -> CashSessionRead:
    service = CashSessionService(db)

    return service.open_session(cash_register_id, user_id, opening_balance)


@router.post("/close/{session_id}", response_model=CashSessionRead, dependencies=[Depends(admin_required)])
def close_cash(
        session_id: int,
        closing_balance: Decimal,
        db: Session = Depends(get_db)
) -> CashSessionRead:
    service = CashSessionService(db)

    return service.close_session(session_id, closing_balance)
