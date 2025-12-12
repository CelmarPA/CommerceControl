# app/services/credit_score_service.py

from sqlalchemy.orm import Session
from decimal import Decimal
from datetime import datetime, timezone
from typing import List

from app.models.customer import Customer
from app.models.account_receivable import AccountReceivable
from app.models.credit_history import CreditHistory


class CreditScoreService:

    def __init__(self, db: Session):
        self.db = db

    # ================================================
    # MAIN ENTRY: UPDATE SCORE AND SAVE ON CUSTOMER
    # ================================================
    def update_score(self, customer_id: int) -> int:
        score = self.compute_score(customer_id)

        customer = self.db.query(Customer).filter(Customer.id == customer_id).first()
        customer.credit_score = score

        self.db.add(customer)
        self.db.commit()
        self.db.refresh(customer)

        return score

    # ================================================
    # COMPUTE SCORE BASED ON CUSTOMER BEHAVIOR
    # ================================================
    def compute_score(self, customer_id: int) -> int :
        customer = self.db.query(Customer).filter(Customer.id == customer_id).first()

        if not customer:
            return 0

        base_score = 500

        # --------------------------------------------
        # HISTORICAL PAYMENTS
        # --------------------------------------------
        payments = (
            self.db.query(CreditHistory)
            .filter(CreditHistory.customer_id == customer_id, CreditHistory.event_type == "payment")
            .all()
        )

        on_time_count = 0
        late_count = 0

        for payment in payments:
            if payment.amount >= 0:
                # history doesn't track delay directly, so we infer from receivables
                receivable = (
                    self.db.query(AccountReceivable)
                    .filter(AccountReceivable.id == payment.notes)
                    .first()
                )

                if receivable and receivable.due_date and receivable.paid_at:
                    delay = (receivable.paid_at - receivable.due_date).days

                    if delay <= 0:
                        on_time_count += 1

                    else:
                        late_count += 1

        # POSITIVES
        base_score += on_time_count * 5

        # NEGATIVES
        base_score -= late_count * 10

        # --------------------------------------------
        # CHECK OPEN AND OVERDUE ACCOUNTS
        # --------------------------------------------
        ars = (
            self.db.query(AccountReceivable)
            .filter(AccountReceivable.customer_id == customer_id)
            .all()
        )

        overdue = 0
        overdue_60_plus = 0
        outstanding = Decimal(0)

        for ar in ars:
            if ar.status not in ("paid", "canceled"):
                outstanding += Decimal(ar.amount) - Decimal(ar.paid_amount or 0)

            if ar.due_date:
                delta = (datetime.now(timezone.utc) - ar.due_date).days

                if delta > 0:
                    overdue += 1

                if delta > 60:
                    overdue_60_plus += 1

        base_score -= overdue * 20

        if overdue_60_plus > 0:
            base_score -= 150

        # --------------------------------------------
        # LIMIT USAGE
        # --------------------------------------------
        limit = Decimal(customer.credit_limit or 0)

        if limit > 0 and outstanding > (limit *  Decimal("0.5")):
            base_score -= 100

        # --------------------------------------------
        # CUSTOMER AGE BONUS
        # --------------------------------------------
        if customer.created_at:
            days = (datetime.now(timezone.utc) - customer.created_at).days

            if days > 365:
                base_score += 50

            # --------------------------------------------
            # NEVER LATE BONUS
            # --------------------------------------------
            if late_count == 0 and overdue == 0:
                base_score += 100

            # FINAL RAGE 0-1000
            score = max(0, min(1000, base_score))

            return score

        return 0

    # ================================================
    # MASS RECALCULATION
    # ================================================
    def recalc_all_customers(self) -> List[dict]:
        customers = self.db.query(Customer).all()

        results = []

        for customer in customers:
            score = self.update_score(customer.id)
            results.append({"customer_id": customer.id, "score": score})

        return results
