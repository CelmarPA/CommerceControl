# app/repositories/supplier_repository.py

from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List

from app.models.suppliers import Supplier
from app.schemas.suppliers_schema import SupplierCreate, SupplierUpdate


class SupplierRepository:

    def __init__(self, db: Session):
        self.db = db

    def create(self,payload: SupplierCreate) -> Supplier:
        supplier = Supplier(**payload.model_dump(exclude_unset=True))

        try:
            self.db.add(supplier)
            self.db.commit()
            self.db.refresh(supplier)

            return supplier

        except IntegrityError as e:
            self.db.rollback()

            msg = str(e.orig)

            if "suppliers.cnpj" in msg:
                raise ValueError("CNPJ already registered")

            raise ValueError(f"Database constraint error: {msg}")

    def list(self) -> List[Supplier]:
        return (
            self.db.query(Supplier)
            .filter(Supplier.deleted_at.is_(None))
            .order_by(Supplier.id.desc())
            .all()
        )

    def get(self, supplier_id: int) -> Supplier:
        return self.db.query(Supplier).filter(Supplier.id == supplier_id).first()

    def update(self, supplier_id: int, payload: SupplierUpdate) -> Supplier | None:
        supplier = self.get(supplier_id)

        if not supplier:
            return None

        for key, value in payload.model_dump(exclude_unset=True).items():
            setattr(supplier, key, value)

        try:
            self.db.commit()
            self.db.refresh(supplier)

            return supplier

        except IntegrityError as e:
            self.db.rollback()

            msg = str(e.orig)

            if "suppliers.cnpj" in msg:
                raise ValueError("CNPJ already registered")

            raise ValueError(f"Database constraint error: {msg}")

    def disable(self, supplier_id: int) -> Supplier:
        supplier = self.get(supplier_id)

        if not supplier:
            return None

        supplier.is_active = False

        self.db.commit()
        self.db.refresh(supplier)

        return supplier

    def enable(self, supplier_id: int) -> Supplier:
        supplier = self.get(supplier_id)

        if not supplier:
            return None

        if supplier.deleted_at is not None:
            raise ValueError("Cannot enable a deleted supplier")

        supplier.is_active = True

        self.db.commit()
        self.db.refresh(supplier)

        return supplier

    def soft_delete(self, supplier_id: int) -> Supplier:
        supplier = self.get(supplier_id)

        if not supplier:
            return None

        supplier.deleted_at = datetime.now(timezone.utc)
        supplier.is_active = False

        self.db.commit()
        self.db.refresh(supplier)

        return supplier

    def deleted_list(self) -> List[Supplier]:
        return(
            self.db.query(Supplier)
            .filter(Supplier.deleted_at.is_not(None))
            .order_by(Supplier.id.desc())
            .all()
        )

    def exists_email(self, email: str) -> bool:
        return (
            self.db.query(Supplier)
            .filter(Supplier.email == email, Supplier.deleted_at.is_(None))
            .first()
            is not None
        )

    def exists_cnpj(self, cnpj: str) -> bool:
        return (
            self.db.query(Supplier)
            .filter(Supplier.cnpj == cnpj, Supplier.deleted_at.is_(None))
            .first()
            is not None
        )
