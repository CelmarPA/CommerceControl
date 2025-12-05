# app/routers/receivables.py

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.services.receivable_service import ReceivableService
from app.schemas.receivable_schema import AccountReceivableRead, ReceivablePaymentIn, ReceivablePaymentRead
from app.core.permissions import admin_required # seller_required

router = APIRouter(prefix="/receivables", tags=["Receivables"])


@router.get("/customer/{customer_id}", response_model=List[AccountReceivableRead], dependencies=[Depends(admin_required)])
def list_customer_accounts(customer_id: int, db: Session = Depends(get_db)) -> List[AccountReceivableRead]:
    service = ReceivableService(db)

    return service.list_customer(customer_id)


@router.post("/{receivable_id}/pay", response_model=ReceivablePaymentRead, dependencies=[Depends(admin_required)])
def pay_receivable(receivable_id: int, payload: ReceivablePaymentIn, db: Session = Depends(get_db), user_id: int | None = None):
    service = ReceivableService(db)
    rp = service.pay_receivable(receivable_id,  payload, user_id)

    return rp


@router.get("/overdue", response_model=List[ReceivablePaymentRead], dependencies=[Depends(admin_required)])
def list_overdue(db: Session = Depends(get_db)) -> List[ReceivablePaymentRead]:
    service = ReceivableService(db)

    return service.list_overdue()

