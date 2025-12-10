# app/schemas/credit_policy_schema.py

from pydantic import BaseModel
from decimal import Decimal
from typing import Optional


class CreditPoliceBase(BaseModel):
    profile: str
    allow_credit: bool = True
    max_installments: Optional[int] = None
    max_sale_amount: Optional[Decimal] = None
    mex_percentage_of_limit: Optional[Decimal] = Decimal(100)
    max_delay_days: Optional[int] = 30
    max_open_invoices: Optional[int] = 5


class CreditPolicyCreate(CreditPoliceBase):
    pass


class CreditPolicyRead(CreditPoliceBase):
    id: int

    class Config:
        from_attributes = True
