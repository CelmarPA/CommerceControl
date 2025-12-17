# app/routers/payables.py

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from decimal import Decimal

from app.database import get_db
from app.schemas.payable_schema import PayableCreate, PayableRead
from app.schemas.payable_payment_schema import PayablePaymentRead
from app.services.payable_service import PayableService

router = APIRouter(prefix="/payables", tags=["Accounts Payable"])


@router.post("/", response_model=PayableRead)
def create_payable(data: PayableCreate, db: Session = Depends(get_db)):
    service = PayableService(db)

    return service.create(data)


@router.post("/{payable_id}/pay", response_model=PayablePaymentRead)
def pay_payable(payable_id: int, amount: Decimal, db: Session = Depends(get_db), user_id: int | None = None) -> PayablePaymentRead:
    service = PayableService(db)

    return service.pay(payable_id, amount, user_id)
