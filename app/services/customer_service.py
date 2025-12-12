# app/services/customer_service.py
from fastapi import HTTPException
from sqlalchemy.orm import Session
from typing import List
from decimal import Decimal

from app.models.customer import Customer
from app.schemas.customer_schema import CustomerCreate, CustomerUpdate
from app.repositories.customer_repository import CustomerRepository
from app.repositories.credit_policy_repository import CreditPolicyRepository
from app.services.credit_history_service import CreditHistoryService


class CustomerService:

    def __init__(self, db: Session):
        self.repo = CustomerRepository(db)
        self.credit_policy_repo = CreditPolicyRepository(db)
        self.credit_history_service = CreditHistoryService(db)

    def create(self, payload: CustomerCreate) -> Customer:
        if self.repo.exists_email(payload.email):
            raise HTTPException(status_code=400, detail="Email already exists")

        if self.repo.exists_cpf_cnpj(payload.cpf_cnpj):
            raise HTTPException(status_code=400, detail="CPF/CNPJ already exists")

        if not payload.credit_profile:
            default = self.credit_policy_repo.get_by_profile("BRONZE")
            payload.credit_profile = default.profile if default else "BRONZE"

        customer = Customer(**payload.model_dump(exclude_unset=True))

        # if no credit_limit provided, set from policy (optional)
        if customer.credit_limit is None or float(customer.credit_limit) == 0:
            policy = self.credit_policy_repo.get_by_profile(customer.credit_profile)

            if policy and policy.max_sale_amount is not None:
                customer.credit_limit = Decimal(str(policy.max_sale_amount))

        # save
        self.repo.create(customer)

        # record initial credit history entry
        self.credit_history_service.record(
            customer_id=customer.id,
            event_type="profile_assigned",
            amount=0,
            balance_after=customer.credit_used or Decimal(0),
            notes=f"Assigned profile {customer.credit_profile}"
        )

        return customer

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