# app/schemas/payable_schema.py

from pydantic import BaseModel
from decimal import Decimal
from datetime import datetime
from typing import Optional


class PayableBase(BaseModel):
    supplier_id: int
    description: Optional[str] = None
    amount: Decimal
    due_date: datetime
    reference_type: Optional[str] = None
    reference_id: Optional[int] = None


class PayableCreate(PayableBase):
    pass


class PayableRead(PayableBase):
    id: int
    paid_amount: Decimal
    status: str
    paid_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True
