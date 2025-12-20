# app/services/cash_flow_report_service.py

from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from datetime import date
from decimal import Decimal
from typing import List

from app.models import CashSession
from app.models.cash_flow import CashFlow
from app.schemas.cash_flow_report_schema import (
    CashFlowSummaryRead,
    CashFlowByCategoryRead,
    CashFlowDailyRead,
    CashFlowMonthlyRead
)
from app.schemas.cash_flow_schema import CashFlowClosingRead


class CashFlowReportService:

    def __init__(self, db: Session):
        self.db = db

    # ============================================================
    # SUMMARY BY PERIOD
    # ============================================================
    def summary_by_period(self, start: date,  end: date) -> CashFlowSummaryRead:

        entries = (
            self.db.query(func.coalesce(func.sum(CashFlow.amount), 0))
            .filter(
                CashFlow.flow_type == "IN",
                CashFlow.date.between(start, end)
            )
            .scalar()
        )

        exits = (
            self.db.query(func.coalesce(func.sum(CashFlow.amount), 0))
            .filter(
                CashFlow.flow_type == "OUT",
                CashFlow.date.between(start, end)
            )
            .scalar()
        )

        balance = Decimal(entries) - Decimal(exits)

        return CashFlowSummaryRead(
            start_date=start,
            end_date=end,
            total_in=Decimal(entries),
            total_out=Decimal(exits),
            balance=balance
        )

    # ============================================================
    # GROUP BY CATEGORY
    # ============================================================
    def by_category(self) -> List[CashFlowByCategoryRead]:

        rows = (
            self.db.query(
                CashFlow.category,
                CashFlow.flow_type,
                func.sum(CashFlow.amount).label("total")
            )
            .filter(CashFlow.category, CashFlow.flow_type)
            .group_by(CashFlow.category)
            .all()
        )

        return [
            CashFlowByCategoryRead(
                category=r.category,
                flow_type=r.flow_type,
                total=Decimal(r.total)
            )
            for r in rows
        ]

    # ============================================================
    # DAILY FLOW
    # ============================================================
    def daily_flow(self, start: date, end: date) -> List[CashFlowDailyRead]:

        rows = (
            self.db.query(
                CashFlow.date,
                CashFlow.flow_type,
                func.sum(CashFlow.amount).label("total")
            )
            .filter(CashFlow.date.between(start, end))
            .group_by(CashFlow.date, CashFlow.flow_type)
            .order_by(CashFlow.date)
            .all()
        )

        data: dict[date, dict] = {}

        for r in rows:
            if r.date not in data:
                data[r.date] = {
                    "in_amount":  Decimal(0),
                    "out_amount": Decimal(0)
                }

            if r.flow_type == "IN":
                data[r.date]["in_amount"] += Decimal(r.total)

            else:
                data[r.date]["out_amount"] += Decimal(r.total)

        # Calculate daily balance
        result: List[CashFlowDailyRead] = []
        running_balance = Decimal(0)

        for day in sorted(data.keys()):
            running_balance += (
                    data[day]["in_amount"] - data[day]["out_amount"]
            )

            result.append(
                CashFlowDailyRead(
                    date=day,
                    in_amount=data[day]["in_amount"],
                    out_amount=data[day]["out_amount"],
                    balance=running_balance
                )
            )

        return result

    # =====================================================
    # MONTHLY FLOW
    # =====================================================
    def monthly_flow(self, year: int) -> List[CashFlowMonthlyRead]:

        rows = (
            self.db.query(
                extract("month", CashFlow.date).label("month"),
                CashFlow.flow_type,
                func.sum(CashFlow.amount).label("total")
            )
            .filter(extract("year", CashFlow.date) == year)
            .group_by("month", CashFlow.flow_type)
            .order_by("month")
            .all()
        )

        data: dict[int, dict] = {}

        for r in rows:
            month = int(r.month)

            if month not in data:
                data[month] = {
                    "year": year,
                    "month": month,
                    "in_amount": Decimal(0),
                    "out_amount": Decimal(0)
                }

            if r.flow_type == "IN":
                data[month]["in_amount"] += Decimal(r.total)

            else:
                data[month]["out_amount"] += Decimal(r.total)

        result: List[CashFlowMonthlyRead] = []

        for month in sorted(data.keys()):
            in_amount = Decimal(data[month]["in_amount"])
            out_amount = Decimal(data[month]["out_amount"])

            result.append(
                CashFlowMonthlyRead(
                    year=year,
                    month=month,
                    in_amount=in_amount,
                    out_amount=out_amount,
                    balance=in_amount - out_amount
                )
            )

        return result

    # =====================================================
    # CLOSING FLOW (AUDITED)
    # =====================================================
    def closing_flow(self, session_id: int, start: date, end: date) -> CashFlowClosingRead:

        # --------------------------------------------------------
        # 1️⃣ Load cash session
        # --------------------------------------------------------
        session = (
            self.db.query(CashSession)
            .filter(CashSession.id == session_id)
            .first()
        )

        if not session:
            raise HTTPException(status_code=404, detail="Cash session not found")

        if session.status != "closed":
            raise HTTPException(status_code=400, detail="Cash session is not closed")

        opening_balance = Decimal(session.opening_balance)
        closing_balance = Decimal(session.closing_balance)

        # --------------------------------------------------------
        # 2️⃣ Aggregate cash flow
        # --------------------------------------------------------
        rows = (
            self.db.query(
                CashFlow.flow_type,
                func.coalesce(func.sum(CashFlow.amount), 0)
            )
            .filter(
                CashFlow.date.between(start, end)
            )
            .group_by(CashFlow.flow_type)
            .all()
        )

        total_in = Decimal(0)
        total_out = Decimal(0)

        for flow_type, total in rows:
            if flow_type == "IN":
                total_in += Decimal(total)

            elif flow_type == "OUT":
                total_out += Decimal(total)

        # --------------------------------------------------------
        # 3️⃣ Expected vs Real
        # --------------------------------------------------------
        expected_balance = opening_balance + total_in - total_out
        difference = closing_balance - expected_balance

        is_consistent = abs(difference) <= Decimal("0.01")

        # --------------------------------------------------------
        # 4️⃣ Return audited report
        # --------------------------------------------------------

        return CashFlowClosingRead(
            start_date=start,
            end_date=end,

            opening_balance=opening_balance,
            expected_balance=expected_balance,
            closing_balance=closing_balance,
            difference=difference,
            is_consistent=is_consistent,

            total_in=total_in,
            total_out=total_out,

            session_id=session.id,
            closed_at=session.closed_at
        )
