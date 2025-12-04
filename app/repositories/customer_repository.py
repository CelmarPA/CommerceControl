# app/repository/customer_repository.py

from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List

from app.models.customer import Customer
from app.schemas.customer_schema import CustomerCreate, CustomerUpdate


class CustomerRepository:

    def __init__(self, db: Session):
        self.db = db

    def create(self, payload: CustomerCreate) -> Customer:
        customer = Customer(
            **payload.model_dump(exclude_unset=True),
            created_at=datetime.now(timezone.utc)
        )

        try:
            self.db.add(customer)
            self.db.commit()
            self.db.refresh(customer)

            return customer

        except IntegrityError as e:
            self.db.rollback()

            msg = str(e.orig)

            if "customers.email" in msg:
                raise ValueError("Email already registered")

            if "customers.cpf_cnpj" in msg:
                raise ValueError("CPF/CNPJ already registered")

            raise ValueError("Duplicate customer data detected")

    def  list(self) -> List[Customer]:
        return self.db.query(Customer).order_by(Customer.id.desc()).all()

    def get(self, customer_id: int) -> Customer:
        return self.db.query(Customer).filter(Customer.id == customer_id).first()

    def update(self, customer_id: int, payload: CustomerUpdate) -> Customer | None:
        customer = self.get(customer_id)

        if not customer:
            return None

        if customer.deleted_at is not None:
            raise ValueError("Cannot update a deleted customer")

        for key, value in payload.model_dump(exclude_unset=True).items():
            setattr(customer, key, value)

        try:
            self.db.commit()
            self.db.refresh(customer)

            return customer

        except IntegrityError as e:
            self.db.rollback()
            msg = str(e.orig)

            if "customers.email" in msg:
                raise ValueError("Email already registered")

            if "customers.cpf_cnpj" in msg:
                raise ValueError("CPF/CNPJ already registered")

            raise ValueError("Duplicate customer data detected")

    def disable(self, customer_id: int) -> Customer:
        customer = self.get(customer_id)

        if not customer:
            return None

        customer.is_active = False

        self.db.commit()
        self.db.refresh(customer)

        return customer

    def enable(self, customer_id: int) -> Customer:
        customer = self.get(customer_id)

        if not customer:
            return None

        if customer.deleted_at is not None:
            raise ValueError("Cannot enable a deleted customer")

        customer.is_active = True

        self.db.commit()
        self.db.refresh(customer)

        return customer

    def soft_delete(self, customer_id: int) -> Customer:
        customer = self.get(customer_id)

        if not customer:
            return None

        customer.deleted_at = datetime.now(timezone.utc)
        customer.is_active = False

        self.db.commit()
        self.db.refresh(customer)

        return customer

    def soft_deleted_list(self) -> List[Customer]:
        return (
            self.db.query(Customer)
            .filter(Customer.deleted_at.is_not(None))
            .order_by(Customer.id.desc())
            .all()
        )

    def exists_email(self, email: str) -> bool:
        return (
            self.db.query(Customer)
            .filter(Customer.email == email, Customer.deleted_at.is_(None))
            .first()
            is not None
        )

    def exists_cpf_cnpj(self, cpf_cnpj: str) -> bool:
        return (
            self.db.query(Customer)
            .filter(Customer.cpf_cnpj == cpf_cnpj, Customer.deleted_at.is_(None))
            .first()
            is not None
        )