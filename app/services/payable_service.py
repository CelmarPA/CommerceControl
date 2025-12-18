# app/services/payable_service.py

from sqlalchemy.orm import Session
from fastapi import HTTPException
from decimal import Decimal
from datetime import datetime, timezone


from app.models.payable import Payable
from app.models.payable_payment import PayablePayment
from app.services.cash_flow_service import CashFlowService


class PayableService:

    def __init__(self, db: Session):
        self.db = db
        self.cash_flow_service = CashFlowService(db)

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
    def pay_payable(self, payable_id: int, amount: Decimal, user_id: int | None = None) -> PayablePayment:

        payable = self.db.query(Payable).filter(Payable.id == payable_id).first()

        if not payable:
            raise HTTPException(status_code=404, detail="Payable not found")

        if payable.status == "paid":
            raise HTTPException(status_code=404, detail="Payable already paid")

        if amount <= 0:
            raise HTTPException(status_code=400, detail="Invalid payment amount")

        remaining = Decimal(payable.amount) - Decimal(payable.paid_amount or 0)
        pay_amount = min(remaining, amount)

        try:
            with self.db.begin_nested():
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

                self.cash_flow_service.register(
                    flow_type="OUT",
                    category="payable_payment",
                    amount=pay_amount,
                    reference_type="payable",
                    reference_id=payable.id,
                    description=f"Payment AP #{payable.id}",
                )

            return payment

        except Exception as e:
            self.db.rollback()

            raise HTTPException(status_code=500, detail=f"Failed to pay payable: {str(e)}")
