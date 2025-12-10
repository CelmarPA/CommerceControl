# app/repositories/credit_policy_repository.py

from sqlalchemy.orm import Session
from typing import List

from app.models.credit_policy import CreditPolicy



class CreditPolicyRepository:

    def __init__(self, db: Session):
        self.db = db

    def list(self) -> List[CreditPolicy]:
        return self.db.query(CreditPolicy).all()

    def get(self, policy_id: int) -> CreditPolicy:
        return self.db.query(CreditPolicy).filter(CreditPolicy.id == policy_id).first()

    def get_by_profile(self, profile: str) -> CreditPolicy:
        return self.db.query(CreditPolicy).filter(CreditPolicy.profile == profile).first()

    def create(self, policy: CreditPolicy) -> CreditPolicy:
        self.db.add(policy)
        self.db.flush()
        self.db.refresh(policy)

        return policy

    def update(self, policy: CreditPolicy) -> CreditPolicy:
        self.db.flush()
        self.db.refresh(policy)

        return policy

    def delete(self, policy: CreditPolicy) -> None:
        self.db.delete(policy)
        self.db.flush()

    

