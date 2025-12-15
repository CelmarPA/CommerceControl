# app/repositories/credit_history_repository.py

from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from app.models.credit_history import CreditHistory


class CreditHistoryRepository:

    def __init__(self, db: Session):
        self.db = db

    def create(self, history: CreditHistory) -> CreditHistory:
        self.db.add(history)
        self.db.commit()
        self.db.refresh(history)

        return history

    def list_by_customer(
            self,
            customer_id: int,
            event_type: str | None = None,
            start: datetime | None = None,
            end: datetime | None = None
    ) -> List[CreditHistory]:
        q = self.db.query(CreditHistory).filter(CreditHistory.customer_id == customer_id)

        if event_type:
            q = q.filter(CreditHistory.event_type == event_type)

        if start:
            q = q.filter(CreditHistory.created_at >= start)

        if end:
            q = q.filter(CreditHistory.created_at <= end)

        return q.order_by(CreditHistory.created_at.desc())
