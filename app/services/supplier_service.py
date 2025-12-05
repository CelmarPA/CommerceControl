# app/service/supplier_service.py

from fastapi import HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.models.suppliers import Supplier
from app.schemas.suppliers_schema import SupplierCreate, SupplierUpdate
from app.repositories.supplier_repository import SupplierRepository


class SupplierService:

    def __init__(self, db: Session):
        self.repo = SupplierRepository(db)

    def create(self, payload: SupplierCreate) -> Supplier:
        if self.repo.exists_email(payload.email):
            raise HTTPException(status_code=400, detail="Email already exists")

        if self.repo.exists_cnpj(payload.cpf_cnpj):
            raise HTTPException(status_code=400, detail="CNPJ already exists")

        return self.repo.create(payload)

    def list(self) -> List[Supplier]:
        return self.repo.list()

    def get(self, supplier_id: int) -> Supplier:
        return self.repo.get(supplier_id)

    def update(self, supplier_id: int,  payload: SupplierUpdate) -> Supplier:
        return self.repo.update(supplier_id, payload)

    def disable(self, supplier_id: int) -> Supplier:
       return self.repo.disable(supplier_id)

    def enable(self, supplier_id: int) -> Supplier:
        return self.repo.enable(supplier_id)

    def soft_delete(self, supplier_id: int) -> Supplier:
        return self.repo.soft_delete(supplier_id)

    def deleted_list(self) -> List[Supplier]:
        return self.repo.deleted_list()
