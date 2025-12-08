# app/routers/sales_orders.py

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.schemas.sales_order_schema import SalesOrderCreate, SalesOrderRead
from app.services.sales_order_service import SalesOrderService
from app.core.permissions import admin_required

router = APIRouter(prefix="/sales-orders", tags=["Sales Orders"])


@router.post("/", response_model=SalesOrderRead, dependencies=[Depends(admin_required)])
def create_order(payload: SalesOrderCreate, db: Session = Depends(get_db)) -> SalesOrderRead:
    service = SalesOrderService(db)

    return service.create(payload)


@router.get("/", response_model=List[SalesOrderRead], dependencies=[Depends(admin_required)])
def list_orders(db: Session = Depends(get_db)) ->List[SalesOrderRead]:
    service = SalesOrderService(db)

    return service.list()


@router.get("/{order_id}", response_model=SalesOrderRead, dependencies=[Depends(admin_required)])
def get_order(order_id: int, db: Session = Depends(get_db)) -> SalesOrderRead:
    service = SalesOrderService(db)

    return service.get(order_id)