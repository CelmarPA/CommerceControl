# app/models/sale.py

import enum
from sqlalchemy.orm import relationship

from sqlalchemy import (
    Column,
    Integer,
    ForeignKey,
    String,
    Numeric,
    DateTime,
    Enum,
    func
)

from app.database import Base


class SaleStatus(str, enum.Enum):
    OPEN = "open"
    PENDING = "pending"     # installment plan / payment plan
    PAID = "paid"
    CANCELED = "canceled"


class Sale(Base):

    __tablename__ = "sales"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True, index=True)

    status = Column(Enum(SaleStatus), nullable=False, default=SaleStatus.OPEN)
    discount_total = Column(Numeric(12, 2), default=0)
    total = Column(Numeric(12, 2), default=0, nullable=False)
    payment_mode = Column(String(32), nullable=True)    # e.g., "cash","card","pix","credit"
    installments = Column(Integer, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    opened_by_user_id = Column(Integer, nullable=True)
    closed_by_user_id = Column(Integer, nullable=True)

    items = relationship("SaleItem", back_populates="sale", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="sale", cascade="all, delete-orphan")
