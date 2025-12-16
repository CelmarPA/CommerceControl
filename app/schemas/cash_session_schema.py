# app/schemas/cash_session_schema.py

from pydantic import BaseModel
from decimal import Decimal
from typing import Optional
from datetime import datetime


class CashSessionBase(BaseModel):
    cash_register_id: int
    user_id: int
    opening_balance: Decimal
    closing_balance: Optional[Decimal] = None
    status: str = "open"


class CashSessionCreate(CashSessionBase):
    pass


class CashSessionRead(CashSessionBase):
    id: int
    opened_at: datetime
    closed_at: Optional[datetime] = None

    # 🔹 CALCULATED FIELDS (CLOSING)
    expected_balance: Optional[Decimal] = None
    difference: Optional[Decimal] = None

    class Config:
        from_attributes = True