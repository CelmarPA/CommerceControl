# app/services/cash_daily_report_service.py

from sqlalchemy.orm import Session
from sqlalchemy import func
from decimal import Decimal
from datetime import date

from app.models.cash_session import CashSession
from app.models.cash_movement import CashMovement


class CashDailyReportService:

    def __init__(self, db: Session):
        self.db = db

    # ============================================================
    # DAILY CONSOLIDATED REPORT
    # ============================================================
    def daily_report(self, day: date) -> dict:

        sessions = (
            self.db.query(CashSession)
            .filter(func.date(CashSession.opened_at) == day)
            .all()
        )

        session_ids = [session.id for session in sessions]

        # -----------------------------
        # Opening / Closing
        # -----------------------------
        opening_total = sum(
            (session.opening_balance or 0) for session in sessions
        )

        closing_total = sum(
            (session.closing_balance or 0) for session in sessions if session.status == "closed"
        )

        # -----------------------------
        # Movements
        # ----------------------------
        movements = (
            self.db.query(
                CashMovement.movement_type,
                func.coalesce(func.sum(CashMovement.amount), 0)
            )
            .filter(CashMovement.cash_session_id.in_(session_ids))
            .group_by(CashMovement.movement_type)
            .all()
        )

        totals = {
            "sale": Decimal(0),
            "cash_supply": Decimal(0),
            "withdrawal": Decimal(0),
            "refund": Decimal(0),
            "adjustment": Decimal(0)
        }

        for mov_type, total in movements:
            if mov_type in totals:
                totals[mov_type] += Decimal(total)

        expected_balance = (
            Decimal(opening_total)
            + totals["sale"]
            + totals["cash_supply"]
            - totals["withdrawal"]
            - totals["refund"]
            + totals["adjustment"]
        )

        difference = Decimal(closing_total) - expected_balance

        return {
            "date": day,
            "sessions": len(sessions),
            "sessions_closed": len([session for session in sessions if session.status == "closed"]),

            "opening_total": opening_total,
            "closing_total": closing_total,

            "sales_total": totals["sale"],
            "supplies_total": totals["cash_supply"],
            "withdrawals_total": totals["withdrawal"],
            "refunds_total": totals["refund"],
            "adjustments_total": totals["adjustment"],

            "expected_balance": expected_balance,
            "difference": difference
        }
