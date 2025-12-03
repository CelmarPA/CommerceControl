# app/router/customer.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Callable

from app.database import get_db
from app.schemas import Message
from app.schemas.customer_schema import CustomerCreate, CustomerUpdate, CustomerRead
from app.services.customer_service import CustomerService
from app.core.permissions import superadmin_required, admin_required

router = APIRouter(prefix="/customers", tags=["Customers"])


@router.post("/", response_model=CustomerRead, dependencies=[Depends(admin_required)])
def create_customer(payload: CustomerCreate, db: Session = Depends(get_db)) -> Callable:
    service = CustomerService(db)

    try:
        return service.create(payload)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=List[CustomerRead])
def list_customers(db: Session = Depends(get_db)) -> List[CustomerRead]:
    service = CustomerService(db)

    return service.list()


@router.get("/deleted", response_model=List[CustomerRead], dependencies=[Depends(admin_required)])
def list_deleted_customers(db: Session = Depends(get_db)):
    """
    List all soft-deleted customers.
    Admin only.
    """
    service = CustomerService(db)
    return service.list_deleted()


@router.get("/{customer_id}", response_model=CustomerRead)
def get_customer(customer_id: int, db: Session = Depends(get_db)) -> CustomerRead:
    service = CustomerService(db)

    customer = service.get(customer_id)

    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    return customer


@router.put("/{customer_id}", response_model=CustomerRead,  dependencies=[Depends(admin_required)])
def update_customer(customer_id: int, payload: CustomerUpdate, db: Session = Depends(get_db)) -> CustomerRead:
    service = CustomerService(db)

    try:
        customer = service.update(customer_id, payload)

        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")

        return customer

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{customer_id}/disable", response_model=CustomerRead, dependencies=[Depends(admin_required)])
def disable_customer(customer_id: int, db: Session = Depends(get_db)) -> CustomerRead:
    service = CustomerService(db)

    customer = service.disable(customer_id)

    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    return customer


@router.put("/{customer_id}/enable", response_model=CustomerRead, dependencies=[Depends(admin_required)])
def enable_customer(customer_id: int, db: Session = Depends(get_db)) -> CustomerRead:
    service = CustomerService(db)

    try:
        customer = service.enable(customer_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    return customer


@router.delete("/{customer_id}/", dependencies=[Depends(superadmin_required)],  response_model=Message)
def delete_customer(customer_id: int, db: Session = Depends(get_db)) -> Message:
    service = CustomerService(db)

    customer = service.soft_delete(customer_id)

    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    return {"detail": "Customer archived (soft deleted)"}
