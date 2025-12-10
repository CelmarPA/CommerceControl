# app/models/credit_policy.py

from sqlalchemy import Column, Integer, String, Numeric, Boolean

from app.database import Base


class CreditPolicy(Base):

    __tablename__ = "credit_policies"

    id = Column(Integer, primary_key=True, index=True)

    profile = Column(String(20), unique=True, nullable=False)
    allow_credit = Column(Boolean, default=True)

    max_installments = Column(Integer, nullable=False, default=6)
    max_sale_amount = Column(Numeric(12, 2), nullable=True)

    max_percentage_of_limit = Column(Numeric(5, 2), default=100)

    max_delay_days = Column(Integer, default=30)
    max_open_invoices = Column(Integer, default=5)

