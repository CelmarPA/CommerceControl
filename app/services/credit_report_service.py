# app/services/credit_report_service.py
from typing import List

from sqlalchemy.orm import Session
from decimal import Decimal
from datetime import datetime, timezone

from app.models import Customer, AccountReceivable


class CreditReportService:

    def __init__(self, db: Session):
        self.db = db

    def overdue(self, days_overdue:int = 0) -> List[Customer]:
        from sqlalchemy import func

        q = (
            self.db.query(Customer)
            .join(AccountReceivable, AccountReceivable.customer_id == Customer.id)
            .filter(AccountReceivable.status == "open", AccountReceivable.due_date <= func.datetime('now', f'-{days_overdue} day'))
            .all()
        )

        return q

    def limit_exceeded(self) -> List[Customer]:
        from sqlalchemy import func

        customers = (self.db.query(Customer)
                     .filter((Customer.credit_used or 0) > (Customer.credit_limit or 0))
                     .all()
        )

        return customers

    def top_risk(self, limit: int = 20):
        # simple risk score: overdue count + credit_used/limit + low score
        from sqlalchemy import func

        res = []
        customers = self.db.query(Customer).all()

        for customer in customers:
            overdue_count = (self.db.query(AccountReceivable)
                             .filter(
                                AccountReceivable.customer_id == customer.id,
                                AccountReceivable.status == "open",
                                AccountReceivable.due_date < func.datetime('now')
                             )
                             .count()
            )

            ratio = 0

            if customer.credit_limit and customer.credit_limit > 0:
                ratio = float((customer.credit_used or 0) / customer.credit_limit)

                score = {
                    "customer_id": customer.id,
                    "name": getattr(customer, "name", None),
                    "overdue_count": overdue_count,
                    "credit_used": float(customer.credit_used or 0),
                    "credit_limit": float(customer.credit_limit or 0),
                    "usage_ratio": ratio,
                    "credit_score": customer.credit_score or 0
                }
                res.append(score)

        res.sort(key=lambda x: (x["overdue_count"], -x["usage_ratio"], x["credit_score"]), reverse=True)

        return res[:limit]
