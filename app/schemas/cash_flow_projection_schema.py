# app/schemas/cash_flow_projection_schema.py

from pydantic import BaseModel
from datetime import date
from decimal import Decimal


class CashFlowProjectionRead(BaseModel):
    date: date
    expected_in: Decimal
    expected_out: Decimal
    projected_balance: Decimal

    class Config:
        from_attributes = True
