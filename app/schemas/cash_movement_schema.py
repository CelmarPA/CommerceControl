# app/schemas/cash_movement_schema.py

from pydantic import BaseModel
from decimal import Decimal
from datetime import datetime
from typing import Optional


class CashMovementRead(BaseModel):
    id: int
    cash_session_id: int
    user_id: int

    movement_type: str
    amount: Decimal

    reason: Optional[str]
    reference_id: Optional[int]

    created_at: datetime

    class Config:
        from_attributes = True
