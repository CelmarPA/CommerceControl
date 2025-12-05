# app/schemas/purchase_order_schema.py

from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field
from typing import List, Optional


class PurchaseOrderItemCreate(BaseModel):
    product_id: int
    quantity_ordered: Decimal = Field(..., gt=0)
    cost_price: Decimal = Field(..., gt=0)


class PurchaseOrderCreate(BaseModel):
    supplier_id: int
    expected_date: Optional[datetime] = None
    notes: Optional[str] = None
    items: List[PurchaseOrderItemCreate] = []


class PurchaseOrderItemRead(BaseModel):
    id: int
    product_id: int
    quantity_ordered: Decimal
    quantity_received: Decimal
    cost_price: Decimal

    class Config:
        from_attributes = True

class PurchaseOrderRead(BaseModel):
    id: int
    supplier_id: int
    status: str
    total_amount: Decimal
    expected_date: Optional[datetime]
    notes: Optional[str]
    created_at: datetime
    items: List[PurchaseOrderItemRead] = []

    class Config:
        from_attributes = True
