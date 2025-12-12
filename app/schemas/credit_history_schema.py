# app/schemas/credit_history_schema.py

from pydantic import BaseModel
from datetime import datetime
from decimal import Decimal


class CreditHistoryRead(BaseModel):
    id: int
    customer_id: int
    event_type: str
    amount: Decimal
    balance_after: Decimal
    notes: str | None
    created_at: datetime

    class Config:
        from_attributes = True
