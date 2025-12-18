# app/schemas/cash_flow_report_schema.py

from pydantic import BaseModel
from decimal import Decimal
from datetime import date


class CashFlowSummaryRead(BaseModel):
    start_date: date
    end_date: date
    total_in: Decimal
    total_out: Decimal
    balance: Decimal

    class Config:
        from_attributes = True


class CashFlowByCategoryRead(BaseModel):
    category: str
    flow_type: str  # IN | OUT
    total: Decimal

    class Config:
        from_attributes = True


class CashFlowDailyRead(BaseModel):
    date: date
    in_amount: Decimal
    out_amount: Decimal
    balance: Decimal

    class Config:
        from_attributes = True


class CashFlowMonthlyRead(BaseModel):
    year: int
    month: int
    in_amount: Decimal
    out_amount: Decimal
    balance: Decimal

    class Config:
        from_attributes = True