# app/routers/purchase_receipts.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.schemas.purchase_receipt_schema import PurchaseReceiptCreate, PurchaseReceiptRead
from app.services.purchase_receipt_service import PurchaseReceiptService
from app.core.permissions import admin_required #purchaser_required

router = APIRouter(prefix="/purchase-receipts", tags=["Purchase Receipts"])


@router.post("/", response_model=PurchaseReceiptRead, status_code=status.HTTP_201_CREATED, dependencies=[Depends(admin_required)])
def create_receipt(payload: PurchaseReceiptCreate, db: Session = Depends(get_db)):
    service = PurchaseReceiptService(db)

    return service.create_receipt(payload)


@router.get("/order/{order_id}", response_model=List[PurchaseReceiptRead], dependencies=[Depends(admin_required)])
def list_receipts_for_order(order_id: int, db: Session = Depends(get_db)):
    service = PurchaseReceiptService(db)

    return service.list_for_order(order_id)
