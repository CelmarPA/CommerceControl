# app/services/credit_policy_service.py

from sqlalchemy.orm import Session
from decimal import Decimal

from app.models.credit_policy import CreditPolicy
from app.repositories.credit_policy_repository import CreditPolicyRepository
from app.schemas.credit_policy_schema import CreditPolicyCreate


class CreditPolicyService:

    def __init__(self, db: Session):
        self.db = db
        self.repo = CreditPolicyRepository(db)

    def list(self):
        return self.repo.list()

    def get(self, policy_id: int) -> CreditPolicy | None:
        return self.repo.get(policy_id)

    def get_by_profile(self, profile: str) -> CreditPolicy | None:
        if profile is None:
            return None

        return self.repo.get_by_profile(profile.upper())

    def create(self, payload: CreditPolicyCreate) -> CreditPolicy:
        profile = payload.profile.upper()
        existing = self.repo.get_by_profile(profile)

        if existing:
            raise ValueError("Profile already exists")

        policy = CreditPolicy(
            profile=profile,
            allow_credit=payload.allow_credit,
            max_installments=payload.max_installments or 6,
            max_sale_amount=payload.max_sale_amount or None,
            max_percentage_of_limit=payload.max_percentage_of_limit or Decimal(100),
            max_delay_days=payload.max_delay_days or 30,
            max_open_invoices=payload.max_open_invoices or 5,
        )

        return self.repo.create(policy)

    def update(self, policy_id: int, payload: CreditPolicyCreate) -> CreditPolicy:
        policy = self.repo.get(policy_id)

        if not policy:
            raise ValueError("Policy not found")

        #  normalize
        profile = payload.profile.upper()
        policy.profile = profile
        policy.allow_credit = payload.allow_credit
        policy.max_installments = payload.max_installments or policy.max_installments
        policy.max_sale_amount = payload.max_sale_amount or policy.max_sale_amount
        policy.max_percentage_of_limit = (
            payload.max_percentage_of_limit
            if payload.max_percentage_of_limit is not None
            else policy.max_percentage_of_limit
        )
        policy.max_delay_days = payload.max_delay_days or policy.max_delay_days
        policy.max_open_invoices = payload.max_open_invoices or policy.max_open_invoices

        return self.repo.update(policy)

    def delete(self, policy_id: int) -> None:
        policy = self.repo.get(policy_id)

        if not policy:
            raise ValueError("Policy not found")

        self.repo.delete(policy)
