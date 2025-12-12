# app/repositories/credit_history_repository.py

from sqlalchemy.orm import Session
from typing import List

from app.models.credit_history import CreditHistory


class CreditHistoryRepository:

    def __init__(self, db: Session):
        self.db = db

    def create(self, ch: CreditHistory) -> CreditHistory:
        self.db.add(ch)
        self.db.commit()
        self.db.refresh(ch)

        return ch

    def list_for_customer(self, customer_id: int) -> List[CreditHistory]:
        return (
            self.db.query(CreditHistory)
            .filter(CreditHistory.customer_id == customer_id)
            .order_by(CreditHistory.created_at.desc())
            .all()
        )
