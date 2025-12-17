# app/schemas/payable_payment_schema.py

from pydantic import BaseModel
from decimal import Decimal
from datetime import datetime
from typing import Optional


class PayablePaymentBase(BaseModel):
    payable_id: int
    amount: Decimal


class PayablePaymentCreate(PayablePaymentBase):
    pass


class PayablePaymentRead(PayablePaymentBase):
    id: int
    user_id: int
    paid_at: Optional[datetime]

    class Config:
        from_attributes = True
