# app/models/payment_schema.py

from pydantic import BaseModel
from typing import Optional
from decimal import Decimal
from datetime import datetime


class PaymentIn(BaseModel):
    method: str
    amount: Decimal
    provider_reference: Optional[str] = None


class PaymentRead(BaseModel):
    id: int
    method: str
    amount: Decimal
    created_at: Optional[datetime] = None
    paid_at: datetime


    class Config:
        from_attributes = True
