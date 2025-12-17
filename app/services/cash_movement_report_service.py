# app/services/cash_movement_report_service.py
from typing import List

from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models.cash_movement import CashMovement
from app.models.cash_session import CashSession


class CashMovementReportService:

    def __init__(self, db: Session):
        self.db = db

    # ============================================================
    # AUDIT REPORT (MOVEMENTS)
    # ============================================================
    def list_by_session(self, session_id: int) -> List[CashMovement]:

        session = self.db.query(CashSession).filter(
            CashSession.id == session_id
        ).first()

        if not session:
            raise HTTPException(status_code=404, detail="Session not found")


        movements = (
            self.db.query(CashMovement)
            .filter(CashMovement.cash_session_id == session_id)
            .order_by(CashMovement.created_at.asc())
            .all()
        )

        return movements
