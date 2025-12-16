# app/services/cash_movement_service.py

from sqlalchemy.orm import Session
from fastapi import HTTPException
from decimal import Decimal

from app.models.cash_movement import CashMovement
from app.models.cash_session import CashSession


class CashMovementService:

    def __init__(self, db: Session):
        self.db = db

    def create(
            self,
            cash_session_id: int,
            user_id: int,
            movement_type: str,
            amount: Decimal,
            reason: str | None = None,
            reference_id: int | None = None
    ) -> CashMovement:

        session = self.db.query(CashSession).filter(
            CashSession.id == cash_session_id,
            CashSession.status == "open"
        ).first()

        if not session:
            raise HTTPException(status_code=400, detail="Session is not open")

        if amount <= 0:
            raise HTTPException(status_code=400, detail="Invalid amount")

        if movement_type in ("withdraw", "refund", "adjustment") and not reason:
            raise HTTPException(status_code=400, detail="Reason is required for this movement")

        movement = CashMovement(
            cash_session_id=cash_session_id,
            user_id=user_id,
            movement_type=movement_type,
            amount=amount,
            reason=reason,
            reference_id=reference_id
        )

        self.db.add(movement)
        self.db.flush()
        self.db.refresh(movement)

        return movement
