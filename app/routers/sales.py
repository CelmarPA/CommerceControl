# app/routers/sales.py

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.sale_schema import SaleCreate, SaleRead, SaleItemIn, SaleItemRead
from app.schemas.payment_schema import PaymentIn
from app.services.sale_service import SalesService
from app.core.permissions import admin_required # seller_required

router = APIRouter(prefix="/sales", tags=["Sales"])


@router.post("/", response_model=SaleRead, status_code=status.HTTP_201_CREATED, dependencies=[Depends(admin_required)])
def create_sale(payload: SaleCreate, db: Session = Depends(get_db)):
    service = SalesService(db)

    return service.create(payload)


@router.post("/{sale_id}/items", response_model=SaleItemRead, dependencies=[Depends(admin_required)])
def add_item(sale_id: int, payload: SaleItemIn, db: Session = Depends(get_db)):
    service = SalesService(db)

    return service.add_item(sale_id, payload)


@router.delete("/{sale_id}/items/{item_id}", dependencies=[Depends(admin_required)])
def remove_item(sale_id: int, item_id: int, db: Session = Depends(get_db)) -> dict:
    service = SalesService(db)

    service.remove_item(sale_id, item_id)

    return {"detail": "Item removed"}

@router.post("{sale_id}/pay", response_model=dict, dependencies=[Depends(admin_required)])
def apply_payment(sale_id: int, payload: PaymentIn, db: Session = Depends(get_db), user_id: int | None = None):
    service = SalesService(db)
    p = service.apply_payment(sale_id, payload, user_id)

    return {"id": p.id, "amount": p.amount}


@router.post("/{sale_id}/checkout", response_model=SaleRead,  dependencies=[Depends(admin_required)])
def checkout(sale_id: int, payment_mode: str, installments: int | None = None, db: Session = Depends(get_db)) -> SaleRead:
    service = SalesService(db)

    return service.checkout(sale_id, payment_mode, installments)


@router.post("/{sale_id}/cancel", response_model=SaleRead, dependencies=[Depends(admin_required)])
def cancel_sale(sale_id: int, db: Session = Depends(get_db)) ->SaleRead:
    service = SalesService(db)

    return service.cancel_sale(sale_id)
