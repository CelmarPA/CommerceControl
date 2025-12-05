# app/schemas/purchase_receipt_schema.py

from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field
from typing import List, Optional


class PurchaseReceiptItemCreate(BaseModel):
    product_id: int
    quantity_received: Decimal = Field(..., gt=0)
    cost_price: Decimal = Field(..., gt=0)


class PurchaseReceiptCreate(BaseModel):
    purchase_order_id: int

    nfe_key: Optional[str] = None
    note_number: Optional[str] = None
    serie: Optional[str] = None
    cfop: Optional[str] = None

    issue_date: Optional[datetime] = None
    arrival_date: Optional[datetime] = None

    total_amount: Optional[Decimal] = None
    freight: Optional[Decimal] = None
    insurance: Optional[Decimal] = None
    discount: Optional[Decimal] = None
    other_expenses: Optional[Decimal] = None

    xml_path: Optional[str] = None
    notes: Optional[str] = None
    items: List[PurchaseReceiptItemCreate] = []


class PurchaseReceiptItemRead(BaseModel):
    id: int
    product_id: int
    quantity_received: Decimal
    cost_price: Decimal

    class Config:
        from_attributes = True


class PurchaseReceiptRead(BaseModel):
    id: int
    purchase_order_id: int

    nfe_key: Optional[str] = None
    note_number: Optional[str] = None
    serie: Optional[str] = None
    cfop: Optional[str] = None

    issue_date: Optional[datetime] = None
    arrival_date: Optional[datetime] = None

    total_amount: Optional[Decimal] = None
    freight: Optional[Decimal] = None
    insurance: Optional[Decimal] = None
    discount: Optional[Decimal] = None
    other_expenses: Optional[Decimal] = None

    xml_path: Optional[str] = None
    notes: Optional[str] = None

    created_at: datetime
    items: List[PurchaseReceiptItemRead] = []

    class Config:
        from_attributes = True

