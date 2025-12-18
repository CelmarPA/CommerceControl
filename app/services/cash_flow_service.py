# app/services/cash_flow_service.py

from datetime import date
from decimal import Decimal
from sqlalchemy.orm import Session

from app.models.cash_flow import CashFlow


class CashFlowService:

    def __init__(self, db: Session):
        self.db = db

    def register(
            self,
            *,
            flow_type: str,
            category: str,
            amount: Decimal,
            reference_type: str | None = None,
            reference_id: int | None = None,
            description: str | None = None
    ) -> CashFlow:

        if flow_type not in ("IN", "OUT"):
            raise ValueError("Invalid flow_type, must be either 'IN' or 'OUT'")

        flow = CashFlow(
            date=date.today(),
            flow_type=flow_type,
            category=category,
            amount=amount,
            reference_type=reference_type,
            reference_id=reference_id,
            description=description
        )

        self.db.add(flow)
        self.db.flush()
        self.db.refresh(flow)

        return flow
