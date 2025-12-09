# app/schemas/receipt_schema.py

from pydantic import BaseModel
from typing import List, Optional
from decimal import Decimal
from datetime import datetime


class ReceiptItemCreate(BaseModel):
    product_id: int
    name: Optional[str] = None
    quantity: Decimal
    unit_price: Decimal
    subtotal: Decimal


class ReceiptCreate(BaseModel):
    sale_id: int
    notes: Optional[str] = None
    items: List[ReceiptItemCreate] = []


class ReceiptItemRead(BaseModel):
    id: int
    product_id: int
    name: Optional[str]
    quantity: Decimal
    unit_price: Decimal
    subtotal: Decimal

    class Config:
        from_attributes = True


class ReceiptRead(BaseModel):
    id: int
    sale_id: int
    subtotal: Decimal
    discount: Decimal
    total: Decimal
    payment_summary: Optional[str]
    notes: Optional[str]
    created_at: datetime
    items: List[ReceiptItemRead] = []

    class Config:
        from_attributes = True
