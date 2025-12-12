# app/repositories/receivable_repository.py

from sqlalchemy.orm import Session
from typing import List, Optional, Any

from app.models.account_receivable import AccountReceivable
from app.models.receivable_payment import ReceivablePayment


class ReceivableRepository:

    def __init__(self, db: Session):
        self.db = db

    def create(self, ar: AccountReceivable) -> AccountReceivable:
        self.db.add(ar)
        self.db.flush()
        self.db.refresh(ar)

        return ar

    def get(self, ar_id: int) -> Optional[AccountReceivable]:
        return self.db.query(AccountReceivable).filter(AccountReceivable.id == ar_id).first()

    def list_by_customer(self, customer_id: int) -> List[AccountReceivable]:
        return self.db.query(AccountReceivable).filter(AccountReceivable.customer_id == customer_id).all()

    def list_overdue(self):
        return self.db.query(AccountReceivable).filter(AccountReceivable.status == 'overdue').all()

    def list_open(self, customer_id: int):
        return (
            self.db.query(AccountReceivable)
            .filter(
                AccountReceivable.customer_id == customer_id,
                AccountReceivable.status.in_(["open", "partial"])
            )
            .all()
        )

    def add_payment(self, receivable_payment: ReceivablePayment) -> ReceivablePayment:
        self.db.add(receivable_payment)
        self.db.flush()
        self.db.refresh(receivable_payment)

        return receivable_payment

    def update(self, obj) -> Any:
        self.db.flush()
        self.db.refresh(obj)

        return obj
