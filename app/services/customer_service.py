# app/services/customer_service.py
from fastapi import HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.models.customer import Customer
from app.schemas.customer_schema import CustomerCreate, CustomerUpdate
from app.repositories.customer_repository import CustomerRepository


class CustomerService:

    def __init__(self, db: Session):
        self.repo = CustomerRepository(db)

    def create(self, payload: CustomerCreate) -> Customer:
        if self.repo.exists_email(payload.email):
            raise HTTPException(status_code=400, detail="Email already exists")

        if self.repo.exists_cpf_cnpj(payload.cpf_cnpj):
            raise HTTPException(status_code=400, detail="CPF/CNPJ already exists")

        return self.repo.create(payload)

    def list(self)  -> List[Customer]:
        return self.repo.list()

    def get(self, customer_id: int) -> Customer:
        return self.repo.get(customer_id)

    def update(self, customer_id: int, payload: CustomerUpdate) -> Customer:
        return self.repo.update(customer_id, payload)

    def disable(self, customer_id: int) -> Customer:
        return self.repo.disable(customer_id)

    def enable(self, customer_id: int) -> Customer:
        return self.repo.enable(customer_id)

    def soft_delete(self, customer_id: int) -> Customer:
        return self.repo.soft_delete(customer_id)

    def list_deleted(self) -> List[Customer]:
        return self.repo.soft_deleted_list()