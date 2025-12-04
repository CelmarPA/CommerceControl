# app/routers/supplier.py

from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.core.permissions import admin_required, superadmin_required
from app.schemas.suppliers_schema import SupplierCreate, SupplierRead, SupplierUpdate
from app.services.supplier_service import SupplierService

router = APIRouter(prefix="/suppliers", tags=["Suppliers"])


@router.post("/", response_model=SupplierRead, status_code=status.HTTP_201_CREATED, dependencies=[Depends(admin_required)])
def create_supplier(payload: SupplierCreate, db: Session = Depends(get_db)) -> SupplierRead:
    service = SupplierService(db)

    return service.create(payload)


@router.get("/", response_model=List[SupplierRead])
def list_suppliers(db: Session = Depends(get_db)) -> List[SupplierRead]:
    service = SupplierService(db)

    return service.list()


@router.get("/deleted", response_model=List[SupplierRead], dependencies=[Depends(admin_required)])
def list_deleted_suppliers(db: Session = Depends(get_db)) ->List[SupplierRead]:
    service = SupplierService(db)

    return service.deleted_list()


@router.get("/{supplier_id}", response_model=SupplierRead)
def get_supplier(supplier_id: int, db: Session = Depends(get_db)) -> SupplierRead:
    service = SupplierService(db)

    return service.get(supplier_id)


@router.put("/{supplier_id}", response_model=SupplierRead)
def update_supplier(supplier_id: int, payload: SupplierUpdate, db: Session = Depends(get_db)) -> SupplierRead:
    service = SupplierService(db)

    return service.update(supplier_id, payload)


@router.put("/{supplier_id}/disable", response_model=SupplierRead, dependencies=[Depends(admin_required)])
def disable_supplier(supplier_id: int, db: Session = Depends(get_db)) -> SupplierRead:
    service = SupplierService(db)

    return service.disable(supplier_id)


@router.put("/{supplier_id}/enable", response_model=SupplierRead, dependencies=[Depends(admin_required)])
def enable_supplier(supplier_id: int, db: Session = Depends(get_db)) -> SupplierRead:
    service = SupplierService(db)

    try:
        supplier = service.enable(supplier_id)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not supplier:
        raise HTTPException(status_code=400, detail="Supplier not found")

    return supplier


@router.delete("/{supplier_id}", response_model=SupplierRead, dependencies=[Depends(superadmin_required)])
def soft_delete_supplier(supplier_id: int, db: Session = Depends(get_db)) -> SupplierRead:
    service = SupplierService(db)

    return service.soft_delete(supplier_id)
