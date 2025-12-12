# app/models/customer.py

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Numeric
from sqlalchemy.orm import relationship

from app.database import Base


class Customer(Base):

    __tablename__ = 'customers'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    phone = Column(String(30), nullable=True)
    cpf_cnpj = Column(String(20), unique=True, nullable=True)
    address = Column(String(255), nullable=True)
    zip_code = Column(String(10), nullable=True)
    city = Column(String(10), nullable=True)
    state = Column(String(15), nullable=True)

    credit_limit = Column(Numeric(12, 2),default=0, nullable=True)
    credit_profile = Column(String(20), default="BRONZE", nullable=True)
    credit_used = Column(Numeric(12, 2), nullable=False, default=0)
    credit_score = Column(Integer, default=600,nullable=True)
    max_overdue_days = Column(Integer, default=30, nullable=True)
    is_active_credit = Column(Boolean, default=True)

    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False)

    deleted_at = Column(DateTime(timezone=True), nullable=True)

    sales_orders = relationship("SalesOrder", back_populates="customer")

    credit_history = relationship("CreditHistory", back_populates="customer", cascade="all, delete-orphan")
