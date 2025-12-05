# app/routers/purchase_orders.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.schemas.purchase_order_schema import PurchaseOrderCreate, PurchaseOrderRead, PurchaseOrderItemRead
from app.services.purchase_order_service import PurchaseOrderService
from app.core.permissions import admin_required #purchaser_required

router = APIRouter(prefix="/purchase_orders", tags=["Purchase Orders"])


@router.post("/", response_model=PurchaseOrderRead, status_code=status.HTTP_201_CREATED, dependencies=[Depends(admin_required)])
def create_order(payload: PurchaseOrderCreate, db: Session = Depends(get_db)) -> PurchaseOrderRead:
    service = PurchaseOrderService(db)

    return service.create_order(payload)


@router.get("/", response_model=List[PurchaseOrderRead], dependencies=[Depends(admin_required)])
def list_orders(db: Session = Depends(get_db)) -> List[PurchaseOrderRead]:
    service = PurchaseOrderService(db)

    return service.list()


@router.get("/{order_id}", response_model=PurchaseOrderRead, dependencies=[Depends(admin_required)])
def get_order(order_id: int, db: Session = Depends(get_db)) -> PurchaseOrderRead:
    service = PurchaseOrderService(db)

    return service.get(order_id)


@router.post("/{order_id}/items", response_model=PurchaseOrderItemRead, dependencies=[Depends(admin_required)])
def add_item(order_id: int, payload: PurchaseOrderItemRead, db: Session = Depends(get_db)) -> PurchaseOrderRead:
    service = PurchaseOrderService(db)

    return service.add_item(order_id, payload)
