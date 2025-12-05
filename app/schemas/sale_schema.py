# app/schemas/sale_schema.py

from pydantic import BaseModel, Field
from typing import List, Optional
from decimal import Decimal
from datetime import datetime

from app.schemas.payment_schema import PaymentRead

class SaleItemIn(BaseModel):
    product_id: int
    quantity: Decimal = Field(..., gt=0)
    unit_price: Optional[Decimal] = None
    discount: Optional[Decimal] = Decimal(0)


class SaleCreate(BaseModel):
    customer_id: Optional[int] = None
    opened_by_user_id: Optional[int] = None


class SaleItemRead(BaseModel):
    id: int
    product_id: int
    quantity: Decimal
    unit_price: Decimal
    discount: Decimal
    subtotal: Decimal
    created_at: datetime

    class Config:
        from_attributes = True


class SaleRead(BaseModel):
    id: int
    customer_id: Optional[int]
    status: str
    discount_total: Optional[Decimal]
    total: Decimal
    payment_mode: Optional[str]
    installments: Optional[int]
    created_at: datetime
    items: List[SaleItemIn] = []
    payments: List[PaymentRead] = []

    class Config:
        from_attributes = True
