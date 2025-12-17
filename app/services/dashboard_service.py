# app/services/dashboard_service.py

from sqlalchemy.orm import Session
from sqlalchemy import func
from decimal import Decimal
from datetime import date

from app.models.cash_session import CashSession
from app.models.cash_movement import CashMovement
from app.models.sale import Sale
from app.models.account_receivable import AccountReceivable
from app.models.customer import Customer


class DashboardService:

    def __init__(self, db: Session):
        self.db = db

    # ============================================================
    # MAIN DASHBOARD
    # ============================================================
    def get_dashboard(self) -> dict:
        today = date.today()

        return {
            "cash": self.cash_kpis(today),
            "sales": self.sales_kpis(today),
            "credit": self.credit_kpis()
        }

    # ============================================================
    # CASH KPIs
    # ============================================================
    def cash_kpis(self, day: date) -> dict:

        sessions = self.db.query(CashSession).filter(
            func.date(CashSession.opened_at) == day
        ).all()

        sessions_id = [session.id for session in sessions]

        movements = (
            self.db.query(
                CashMovement.movement_type
            )
            .filter(CashMovement.cash_session_id.in_(sessions_id))
            .group_by(CashMovement.movement_type)
            .all()
        )

        totals = {movement: Decimal(0) for movement in [
            "sale", "cash_supply", "withdrawal", "refund", "adjustment"
        ]}

        for total, value in movements:
            if total in totals:
                totals[total] = Decimal(value)

        opening = sum(session.opening_balance for session in sessions)
        closing = sum(session.closing_balance for session in sessions if session.status == "closed")

        expected_balance = (
            Decimal(opening)
            + totals["sale"]
            + totals["chash_supply"]
            - totals["withdrawal"]
            - totals["refund"]
            + totals["adjustment"]
        )

        return {
            "sessions_open": len([session for session in sessions if session.status == "open"]),
            "expected_balance": expected_balance,
            "difference": Decimal(closing) - expected_balance,
            "withdrawals": totals["withdrawal"],
            "supplies": totals["cash_supply"]
        }

    # ============================================================
    # SALES KPIs
    # ============================================================
    def sales_kpis(self, day: date) -> dict:

        total_today = (
            self.db.query(func.coalesce(func.sum(Sale.total), 0))
            .filter(func.date(Sale.created_at) == day)
            .scalar()
        )

        count_today = (
            self.db.query(func.count(Sale.id))
            .filter(func.date(Sale.created_at) == day)
            .scalar()
        )

        mount_total = (
            self.db.query(func.coalesce(func.sum(Sale.total), 0))
            .filter(func.date_trunc("month", Sale.created_at) == func.date_trunc("month", func.now()))
            .scalar()
        )

        ticket = (Decimal(total_today) / count_today) if count_today else Decimal(0)

        return {
            "total_today": Decimal(total_today),
            "month_total": Decimal(mount_total),
            "sales_count": count_today,
            "ticket_avg": ticket
        }

    # ============================================================
    # CREDIT KPIs
    # ============================================================
    def credit_kpis(self) -> dict:

        receivable_total = (
            self.db.query(func.coalesce(func.sum(AccountReceivable.amount), 0))
            .scalar()
        )

        overdue_total = (
            self.db.query(func.coalesce(func.sum(AccountReceivable.amount), 0))
            .filter(AccountReceivable.status == "overdue")
            .scalar()
        )

        risk_customers = (
            self.db.query(Customer)
            .filter(Customer.credit_score < 400)
            .count()
        )

        return {
            "receivable_total": Decimal(receivable_total),
            "overdue_total": Decimal(overdue_total),
            "high_risk_customers": risk_customers
        }
