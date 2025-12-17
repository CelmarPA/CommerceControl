# app/schemas/cash_daily_report_schema.py

from pydantic import BaseModel
from decimal import Decimal
from datetime import date


class CashDailyReportRead(BaseModel):
    date: date

    sessions: int
    sessions_closed: int

    opening_total: Decimal
    closing_total: Decimal

    sales_total: Decimal
    supplies_total: Decimal
    withdrawals_total: Decimal
    refunds_total: Decimal
    adjustments_total: Decimal

    expected_balance: Decimal
    difference: Decimal
