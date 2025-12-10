# app/services/credit_engine.py

from decimal import Decimal
from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.customer import Customer
from app.models.credit_policy import CreditPolicy
from app.models.account_receivable import AccountReceivable
from app.services.credit_policy_service import CreditPolicyService


class CreditEngine:

    def __init__(self, db: Session):
        self.db = db

    def load_policy_for_customer(self, customer: Customer) -> CreditPolicy:
        service = CreditPolicyService(self.db)
        profile = (customer.credit_profile or "BRONZE").upper()
        policy = service.get_by_profile(profile)

        if not policy:
            policy = service.get_by_profile("BRONZE")

        return policy

    def outstanding_amount(self, customer_id: int) -> Decimal:
        # sum of open ARs (status != 'paid' and != 'cancelled'
        val = (
            self.db.query(func.coalesce(func.sum(AccountReceivable.amount - AccountReceivable.paid_amount), 0))
            .filter(
                AccountReceivable.customer_id == customer_id,
                AccountReceivable.status.notin_(["paid", "canceled"])
            )
            .scalar()
        )

        return Decimal(val or 0)

    def overdue_info(self, customer_id: int) -> dict:
        # retorn (count_overdue, max_days_overdue)
        from datetime import datetime, timezone

        ars = (
            self.db.query(AccountReceivable)
            .filter(AccountReceivable.customer_id == customer_id, AccountReceivable.status == "open")
            .all()
        )

        count_overdue = 0
        max_days_overdue = 0,

        for ar in ars:
            if ar.due_date:
                delta = (datetime.now(timezone.utc) - ar.due_date).days

                if delta > 0:
                    count_overdue += 1
                    max_days_overdue = max(max_days_overdue, delta)

        return {
            "count_overdue": count_overdue,
            "max_days_overdue": max_days_overdue
        }

    def validate_sale(self, customer_id: int, sale_total: Decimal, installments: int | None = None) -> bool:
        """
        Raises HTTPException on validation failure.
        """

        customer = self.db.query(Customer).filter(Customer.id == customer_id).first()

        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")

        policy = self.load_policy_for_customer(customer)

        if not policy.allow_credit:
            raise HTTPException(status_code=400, detail="Customer is not allowed to use credit")


        # 1) Max installments
        n = installments or 1

        if policy.max_installments and n > policy.max_installments:
            raise HTTPException(status_code=400, detail=f"Max installments allowed: {policy.max_installments}")

        # 2) Max sale amount per policy
        if policy.max_sale_amount is not None and Decimal(sale_total) > Decimal(policy.max_sale_amount):
            raise HTTPException(status_code=400, detail=f"Sale exceeds max allowed for profile {policy.profile}")

        # 3) Check credit limit usage
        outstanding = self.outstanding_amount(customer_id)
        limit = Decimal(customer.credit_limit or 0)

        # calculate allowed percent of limit
        allowed_percent = Decimal(policy.max_percentage_of_limit or 100) / Decimal(100)
        effective_limit = limit * allowed_percent

        if (outstanding + Decimal(sale_total)) > effective_limit:
            raise HTTPException(status_code=400, detail="Customer credit limit exceeded")

        # 4) Overdue checks
        overdue = self.overdue_info(customer_id)

        if overdue["count_overdue"] > 0 and overdue["max_days_overdue"] > policy.max_delay_days:
            raise HTTPException(status_code=400, detail="Customer has overdue invoices exceeding allowed days")

        # 5) Additional custom checks (score)
        if customer.credit_score is not None:
            # Example: block if score < 400
            if customer.credit_score < 300:
                raise HTTPException(status_code=400, detail="Customer credit score too low")

        # Passed all checks
        return True

    def get_score(self, customer_id: int) -> dict:
        customer = self.db.query(Customer).filter(Customer.id == customer_id).first()

        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")

        return {
            "customer_id": customer.id,
            "name": customer.name,
            "credit_score": customer.credit_score,
            "profile": customer.credit_profile
        }

    def get_limit(self, customer_id: int) -> dict:
        customer = self.db.query(Customer).filter(Customer.id == customer_id).first()

        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")

        outstanding = self.outstanding_amount(customer_id)
        total_limit = Decimal(customer.credit_limit or 0)
        available = total_limit - outstanding

        return {
            "customer_id": customer.id,
            "total_limit": total_limit,
            "used": outstanding,
            "available": available
        }

    def check_customer_status(self, customer_id: int) -> dict:
        customer = self.db.query(Customer).filter(Customer.id == customer_id).first()

        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")

        overdue = self.overdue_info(customer_id)
        outstanding = self.outstanding_amount(customer_id)
        total_limit = Decimal(customer.credit_limit or 0)
        available = total_limit - outstanding

        return {
            "customer_id": customer.id,
            "name": customer.name,
            "credit_profile": customer.credit_profile,
            "credit_score": customer.credit_score,
            "limit_total": total_limit,
            "outstanding": outstanding,
            "available": available,
            "overdue": overdue
        }
