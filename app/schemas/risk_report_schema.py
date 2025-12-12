# app/schemas/risk_report_schema.py

from pydantic import BaseModel
from decimal import Decimal
from typing import List, Optional
from datetime import datetime


class RiskCustomer(BaseModel):
    customer_id: int
    name: str
    credit_score: Optional[int]
    profile: Optional[str]

    risk_level: str

    outstanding: Decimal
    usage_percent: float
    max_days_overdue: int

    class Config:
        from_attributes = True


class RiskReport(BaseModel):
    generated_at: datetime
    total_customers: int
    top_risk_customers: List[RiskCustomer]
    top_safe_customers: List[RiskCustomer]
