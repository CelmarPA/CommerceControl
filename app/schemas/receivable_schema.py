# app/schemas/receivable_schema.py

from pydantic import BaseModel
from decimal import Decimal
from datetime import datetime
from typing import Optional


class AccountReceivableCreate(BaseModel):
    customer_id: int
    sale_id: int
    installment_number: int
    due_date: datetime
    amount: Decimal


class AccountReceivableRead(BaseModel):
    id: int
    customer_id: int
    sale_id: int
    installment_number: int
    due_date: datetime
    amount: Decimal
    paid_amount: Decimal
    status: str
    paid_at: Optional[datetime]

    class Config:
        from_attributes = True


class ReceivablePaymentIn(BaseModel):
    amount: Decimal
    user_id: Optional[int] = None


class ReceivablePaymentRead(BaseModel):
    id: int
    amount: Decimal
    paid_at: datetime
    user_id: Optional[int]

    class Config:
        from_attributes = True
