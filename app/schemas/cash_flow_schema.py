# app/schemas/cash_flow_schema.py

from pydantic import BaseModel
from decimal import Decimal
from datetime import date, datetime
from typing import Optional


class CashFlowRead(BaseModel):
    id: int
    date: date
    flow_type: str   # IN | OUT
    category: str
    amount: Decimal

    reference_type: Optional[str]
    reference_id: Optional[int]

    description: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True