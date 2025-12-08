# app/schema/stock_schema.py
from decimal import Decimal

from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime


class StockMovementBase(BaseModel):
    product_id: int
    quantity: int = Field(gt=0,  description="Movement must be greater than zero")
    movement_type: str = Field(pattern="^(IN|OUT|ADJUST)$")
    description: Optional[str] = None


class StockMovementCreate(StockMovementBase):
    movement_type: Literal["IN", "OUT", "ADJUST"]
    description: Optional[str]


class StockMovementRead(StockMovementBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class StockCurrentRead(BaseModel):
    product_id: int
    stock: Decimal
