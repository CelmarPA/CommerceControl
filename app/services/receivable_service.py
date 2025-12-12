# app/services/receivable_service.py

from typing import List
from pygments.lexers import q
from sqlalchemy.orm import Session
from fastapi import HTTPException
from decimal import Decimal
from datetime import datetime, timezone

from app.models import AccountReceivable, SaleStatus
from app.models.customer import Customer
from app.repositories.receivable_repository import ReceivableRepository
from app.models.receivable_payment import ReceivablePayment
from app.services.credit_history_service import CreditHistoryService
from app.services.credit_engine import CreditEngine


class ReceivableService:

    def __init__(self, db: Session):
        self.db = db
        self.repo = ReceivableRepository(db)
        self.history = CreditHistoryService(db)
        self.engine = CreditEngine(db)

    # ============================================================
    # GET
    # ============================================================
    def get(self, receivable_id: int) -> AccountReceivable:
        ar = self.repo.get(receivable_id)

        if not ar:
            raise HTTPException(status_code=404, detail="Receivable not found")

        return ar

    # ============================================================
    # PAYMENT
    # ============================================================
    def pay_receivable(self, receivable_id: int, amount: Decimal, user_id: int | None = None) -> ReceivablePayment:
        ar = self.get(receivable_id)

        if ar.status == "paid":
            raise HTTPException(status_code=400, detail="Receivable already paid")

        if amount <= 0:
            raise HTTPException(status_code=400, detail="Invalid payment amount")

        remaining = Decimal(ar.amount) - Decimal(ar.paid_amount or 0)
        pay_amount = min(remaining, amount)

        try:
            with self.db.begin_nested():  # SAVEPOINT

                # 1) Create payment record
                payment = ReceivablePayment(
                    receivable_id=ar.id,
                    amount=pay_amount,
                    user_id=user_id
                )

                self.repo.add_payment(payment)

                # 2) Update AR
                ar.paid_amount = (Decimal(ar.paid_amount or 0) + pay_amount)

                if ar.paid_amount >= ar.amount:
                    ar.status = "paid"
                    ar.paid_at = datetime.now(timezone.utc)

                else:
                    ar.status = "partial"

                self.repo.update(ar)

                # 3) Update customer credit_used
                customer = self.db.query(Customer).filter(Customer.id == ar.customer_id).first()

                if not customer:
                    raise HTTPException(status_code=404, detail="Customer not found")

                customer.credit_used = max(
                    Decimal(customer.credit_used or 0) - pay_amount,
                    Decimal(0)
                )

                self.db.add(customer)

                # 4) Register credit history
                self.history.record(
                    customer_id=customer.id,
                    event_type="payment",
                    amount=pay_amount,
                    balance_after=customer.credit_used,
                    notes=f"Payment for AR #{ar.id}"
                )

                # 5) Recalculate SCORE
                new_score = self.engine.recalculate_score(customer.id)
                customer.credit_score = new_score

                # 6) Update profile (BRONZE / SILVER / GOLD / DIAMOND)
                customer.credit_profile = self.engine.assign_profile(new_score)

                self.db.add(customer)

            self.db.commit()

            return payment

        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to register payment: {str(e)}")

    # ============================================================
    # LISTS
    # ============================================================
    def list_customer(self, customer_id: int) -> List[Customer]:
        return self.repo.list_by_customer(customer_id)

    def list_overdue(self):
        return self.repo.list_overdue()

    # ============================================================
    # AUTO MARK OVERDUE
    # ============================================================
    def refresh_overdue(self) -> int:
        """Marks invoices as overdue if past due date. Returns count."""

        today = datetime.now(timezone.utc)
        count = 0

        ars = self.db.query(AccountReceivable).filter(
            AccountReceivable.status == "open",
        ).all()

        for ar in ars:
            if ar.due_date and ar.due_date < today:
                ar.status = "overdue"
                self.db.add(ar)
                count += 1

        self.db.commit()

        return count
