# app/services/credit_report_service.py
from typing import List

from sqlalchemy import func
from sqlalchemy.orm import Session
from decimal import Decimal
from fastapi import HTTPException

from app.models import Customer, AccountReceivable, CashSession, CashMovement


class CreditReportService:

    def __init__(self, db: Session):
        self.db = db

    def overdue(self, days_overdue:int = 0) -> List[Customer]:

        q = (
            self.db.query(Customer)
            .join(AccountReceivable, AccountReceivable.customer_id == Customer.id)
            .filter(AccountReceivable.status == "open", AccountReceivable.due_date <= func.datetime('now', f'-{days_overdue} day'))
            .all()
        )

        return q

    def limit_exceeded(self) -> List[Customer]:

        customers = (self.db.query(Customer)
                     .filter((Customer.credit_used or 0) > (Customer.credit_limit or 0))
                     .all()
        )

        return customers

    def top_risk(self, limit: int = 20):
        # simple risk score: overdue count + credit_used/limit + low score

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

    # ============================================================
    # CASH SESSION REPORT
    # ============================================================
    def session_report(self, session_id: int) -> dict:

        session = self.db.query(CashSession).filter(
            CashSession.id == session_id
        ).first()

        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        # --------------------------------------------------------
        # Aggregated movements
        # --------------------------------------------------------
        totals = (
            self.db.query(
                CashMovement.movement_type,
                func.coalesce(func.sum(CashMovement.amount), 0)
            )
            .filter(CashMovement.cash_session_id == session_id)
            .group_by(CashMovement.movement_type)
            .all()
        )

        data = {t[0]: Decimal(t[1]) for t in totals}

        total_sales = data.get("sale", Decimal(0))
        total_supplies = data.get("supply", Decimal(0))
        total_withdrawals = data.get("withdrawal", Decimal(0))
        total_refunds = data.get("refund", Decimal(0))
        total_adjustments = data.get("adjustment", Decimal(0))

        expected_closing = (
            Decimal(session.opening_balance)
            + total_sales
            + total_supplies
            - total_withdrawals
            - total_refunds
            + total_adjustments
        )

        closing_balance = Decimal(session.closing_balance  or 0)
        difference = closing_balance - expected_closing

        return {
            "session_id": session.id,
            "cash_register_id": session.cash_register_id,
            "user_id": session.user_id,
            "opened_at": session.opened_at,
            "closed_at": session.closed_at,
            "status": session.status,

            "opening_balance": session.opening_balance,

            "total_sales": total_sales,
            "total_supplies": total_supplies,
            "total_withdrawals": total_withdrawals,
            "total_refunds": total_refunds,
            "total_adjustments": total_adjustments,

            "expected_closing": expected_closing,
            "closing_balance": closing_balance,
            "difference": difference
        }
