# app/services/cash_session_service.py

from sqlalchemy import func
from sqlalchemy.orm import Session
from fastapi import HTTPException
from decimal import Decimal
from datetime import datetime, timezone

from app.models.cash_session import CashSession
from app.repositories.cash_session_repository import CashSessionRepository
from app.models.cash_movement import CashMovement


class CashSessionService:

    def __init__(self, db: Session):
        self.db = db
        self.repo = CashSessionRepository(db)

    # ============================================================
    # OPEN CASH SESSION
    # ============================================================
    def open_session(self, cash_register_id: int, user_id: int, opening_balance: Decimal) -> CashSession:

        # 1️⃣ User already has an open session?
        if self.repo.get_open_by_user(user_id):
            raise HTTPException(status_code=400, detail="User already has an open cash session")

        # 2️⃣ Cash register already in use?
        if self.repo.get_open_by_register(cash_register_id):
            raise HTTPException(status_code=400, detail="Cash register already has an open session")

        session = CashSession(
            cash_register_id=cash_register_id,
            user_id=user_id,
            opening_balance=opening_balance,
            status="open"
        )

        return self.repo.create(session)

    # ============================================================
    # CLOSE CASH SESSION
    # ============================================================
    def close_session(self, session_id: int, closing_balance: Decimal) -> CashSession:

        session = self.db.query(CashSession).filter(CashSession.id == session_id).first()

        if not session:
            raise HTTPException(status_code=404, detail="Cash session not found")

        if session.status != "open":
            raise HTTPException(status_code=400, detail="Cash session already closed")

        # -------------------------------------------------
        # 1️⃣ Aggregate movements
        # -------------------------------------------------
        movements = (
            self.db.query(
                CashMovement.movement_type,
                func.sum(CashMovement.amount).label("total")
            )
            .filter(CashMovement.cash_session_id == session.id)
            .group_by(CashMovement.movement_type)
            .all()
        )

        totals = {movement.movement_type: Decimal(movement.total) for movement in movements}

        opening = Decimal(session.opening_balance)

        sales= totals.get("sale", Decimal(0))
        supplies = totals.get("supply", Decimal(0))
        withdrawals = totals.get("withdrawal", Decimal(0))
        refunds = totals.get("refund", Decimal(0))
        adjustments = totals.get("adjustment", Decimal(0))

        expected_balance = (
            opening
            + sales
            + supplies
            + withdrawals
            + refunds
            + adjustments
        )

        difference = closing_balance - expected_balance

        # -------------------------------------------------
        # 1️⃣ Aggregate movements
        # -------------------------------------------------
        session.closed_at = datetime.now(timezone.utc)
        session.closing_balance = closing_balance
        session.status = "closed"

        self.db.add(session)
        self.db.commit()

        # -------------------------------------------------
        # 3️⃣ Attach audit info (virtual, not stored)
        # ------------------------------------------------
        session.expected_balance = expected_balance
        session.difference = difference

        return session
