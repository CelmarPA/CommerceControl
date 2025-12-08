# app/schemas/sales_order_schema.py
from datetime import datetime

from pydantic import BaseModel, Field
from decimal import Decimal
from typing import List, Optional


class SalesOrderItemCreate(BaseModel):
    product_id: int
    quantity: Decimal = Field(..., gt=0)
    unit_price: Decimal = Field(..., gt=0)


class SalesOrderCreate(BaseModel):
    customer_id: Optional[int] = None
    items: List[SalesOrderItemCreate]


class SalesOrderItemRead(BaseModel):
    id: int
    product_id: int
    quantity: Decimal
    unit_price: Decimal
    sub_total: Decimal

    class Config:
        from_attributes = True


class SalesOrderRead(BaseModel):
    id: int
    customer_id: int
    status: str
    total_amount: Decimal
    create_at: datetime
    items: List[SalesOrderItemRead]

    class Config:
        from_attributes = True
