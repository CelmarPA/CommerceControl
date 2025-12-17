# app/services/payable_service.py

from sqlalchemy.orm import Session
from fastapi import HTTPException
from decimal import Decimal
from datetime import datetime, timezone


from app.models.payable import Payable
from app.models.payable_payment import PayablePayment


class PayableService:

    def __init__(self, db: Session):
        self.db = db

    # ============================================================
    # CREATE PAYABLE
    # ============================================================
    def create(self, data: Payable) -> Payable:
        payable = Payable(**data.dict())

        self.db.add(payable)
        self.db.commit()
        self.db.refresh(payable)

        return payable

    # ============================================================
    # PAY PAYABLE
    # ============================================================
    def pay(self, payable_id: int, amount: Decimal, user_id: int | None = None) -> PayablePayment:

        payable = self.db.query(Payable).filter(Payable.id == payable_id).first()

        if not payable:
            raise HTTPException(status_code=404, detail="Payable not found")

        if payable.status == "paid":
            raise HTTPException(status_code=404, detail="Payable already paid")

        remaining = Decimal(payable.amount) - Decimal(payable.paid_amount or 0)
        pay_amount = min(remaining, amount)

        payment = PayablePayment(
            payable_id=payable.id,
            user_id=user_id,
            amount=pay_amount
        )

        self.db.add(payment)

        payable.paid_amount = (Decimal(payable.paid_amount or 0) + pay_amount)

        if payable.paid_amount > payable.amount:
            payable.status = "paid"
            payable.paid_at = datetime.now(timezone.utc)

        else:
            payable.status = "partial"

        self.db.add(payable)
        self.db.commit()
        self.db.refresh(payable)

        return payment
