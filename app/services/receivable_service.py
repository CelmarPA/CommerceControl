# app/services/receivable_service.py
from typing import List

from sqlalchemy.orm import Session
from fastapi import HTTPException
from decimal import Decimal
from datetime import datetime

from app.models.customer import Customer
from app.repositories.receivable_repository import ReceivableRepository
from app.models.receivable_payment import ReceivablePayment


class ReceivableService:

    def __init__(self, db: Session):
        self.db = db
        self.repo = ReceivableRepository(db)

    def pay_receivable(self, receivable_id: int, amount: Decimal, user_id: int | None = None) -> ReceivablePayment:
        receivable = self.repo.get(receivable_id)

        if not receivable:
            raise HTTPException(status_code=404, detail="Receivable not found")

        if receivable.status == "paid":
            raise HTTPException(status_code=400, detail="Receivable already paid")

        remaining = Decimal(receivable.amount) - Decimal(receivable.paid_amount or 0)

        if amount <= 0:
            raise HTTPException(status_code=400, detail= "Invalid payment amount")

        pay_amount = min(remaining, Decimal(amount))

        rp = ReceivablePayment(
            receivable_id=receivable_id,
            amount=pay_amount,
            user_id=user_id
        )

        self.repo.add_payment(rp)

        receivable.paid_amount = Decimal(receivable.paid_amount or 0) + pay_amount

        if receivable.paid_amount >= receivable.amount:
            receivable.status = "paid"
            receivable.paid_at = datetime.now()

        elif receivable.paid_amount > 0:
            receivable.status = "partial"

        self.repo.update(receivable)

        return rp

    def list_customer(self, customer_id: int) -> List[Customer]:
        return self.repo.list_by_customer(customer_id)

    def list_overdue(self):
        return self.repo.list_overdue()
