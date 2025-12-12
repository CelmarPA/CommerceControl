# app/services/credit_history_service.py

from sqlalchemy.orm import Session
from decimal import Decimal
from typing import List

from app.models.credit_history import CreditHistory
from app.repositories.credit_history_repository import CreditHistoryRepository


class CreditHistoryService:

    def __init__(self, db: Session):
        self.db = db
        self.repo = CreditHistoryRepository(db)

    def record(self, customer_id: int, event_type: str, amount: Decimal, balance_after: Decimal, notes: str | None = None) -> CreditHistory:
        """
        Creates a history entry for a credit event.
        """
        history = CreditHistory(
            customer_id=customer_id,
            event_type=event_type,
            amount=amount,
            balance_after=Decimal(balance_after),
            notes=notes
        )

        return self.repo.create(history)

    def list_for_customer(self, customer_id: int) -> List[CreditHistory]:
        return self.repo.list_for_customer(customer_id)
