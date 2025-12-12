# app/schemas/credit_analytics_schema.py

from pydantic import BaseModel
from decimal import Decimal


class CreditAnalytics(BaseModel):
    customer_id: int
    name: str

    credit_score: int
    credit_profile: str
    risk_level: str

    credit_limit: Decimal
    outstanding: Decimal
    available: Decimal
    usage_percent: float

    overdue_invoices: int
    max_days_overdue: int

    payments_last_90d: int
    purchase_last_90d: int

    trend: str  # "improving", "stable", "worsening"

    class Config:
        from_attributes = True
