# app/services/cash_flow_projection_service.py

from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date
from decimal import Decimal
from typing import List

from app.models.account_receivable import AccountReceivable
from app.models.payable import Payable
from app.schemas.cash_flow_projection_schema import CashFlowProjectionRead


class CashFlowProjectionService:

    def __init__(self, db: Session):
        self.db = db

    # ============================================================
    # CASH FLOW PROJECTION
    # ============================================================
    def project(self, start: date, end: date) -> List[CashFlowProjectionRead]:
        """
        Projects future cash flow based on:
        - Accounts Receivable (expected IN)
        - Payables (expected OUT)

        Does NOT use cash sessions or real movements.
        """

        # --------------------------------------------------------
        # 1️⃣ Receivables (IN)
        # --------------------------------------------------------
        receivables = (
            self.db.query(
                AccountReceivable.due_date.label("date"),
                func.sum(AccountReceivable.amount - func.coalesce(AccountReceivable.paid_amount, 0)
                ).label("total")
            )
            .filter(
                AccountReceivable.status.in_(["open", "partial"]),
                AccountReceivable.due_date.between(start, end)
            )
            .group_by(AccountReceivable.due_date)
            .all()
        )

        # --------------------------------------------------------
        # 2️⃣ Payables (OUT)
        # --------------------------------------------------------
        payables = (
            self.db.query(
                Payable.due_date.label("date"),
                func.sum(
                    Payable.amount - func.coalesce(Payable.paid_amount, 0)
                ).label("total")
            )
            .filter(
                Payable.status.in_(["open", "partial"]),
                Payable.due_date.between(start, end)
            )
            .group_by(Payable.due_date)
            .all()
        )

        # --------------------------------------------------------
        # 3️⃣ Normalize data
        # --------------------------------------------------------
        data: dict[date, dict] = {}

        for r in receivables:
            data.setdefault(r.date, {
                "expected_in": Decimal(0),
                "expected_out": Decimal(0)
            })

            data[r.date]["expected_in"] += Decimal(r.total)

        for p in payables:
            data.setdefault(p.date, {
                "expected_in": Decimal(0),
                "expected_out": Decimal(0)
            })

            data[p.data]["expected_out"] += Decimal(p.total)

        # --------------------------------------------------------
        # 4️⃣ Calculate projected balance
        # --------------------------------------------------------
        result = []
        running_balance = Decimal(0)

        for day in sorted(data.keys()):
            running_balance += (
                data[day]["expected_in"] - data[day]["expected_out"]
            )

            result.append({
                "date": day,
                "expected_in": data[day]["expected_in"],
                "expected_out": data[day]["expected_out"],
                "projected_balance": running_balance
            })

        return result
