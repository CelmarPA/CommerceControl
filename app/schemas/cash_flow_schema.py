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


class CashFlowClosingRead(BaseModel):
    start_date: date
    end_date: date

    opening_balance: Decimal
    expected_balance: Decimal
    closing_balance: Decimal
    difference: Decimal
    is_consistent: bool

    total_in: Decimal
    total_out: Decimal

    session_id: Optional[int]
    closed_at: Optional[datetime]

    class Config:
        from_attributes = True
