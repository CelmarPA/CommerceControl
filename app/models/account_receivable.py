# app/models/account_receivable.py

from sqlalchemy import Column, Integer, ForeignKey, Numeric, DateTime, String, func
from sqlalchemy.orm import relationship

from app.database import Base


class AccountReceivable(Base):

    __tablename__ = "accounts_receivable"

    id = Column(Integer, primary_key=True, index=True)

    customer_id = Column(Integer, ForeignKey('customers.id'), nullable=False, index=True)
    sale_id = Column(Integer, ForeignKey('sales.id'), nullable=False, index=True)
    installment_number = Column(Integer, nullable=False)
    due_date = Column(DateTime(timezone=True), nullable=False)
    amount = Column(Numeric(12,2), nullable=False)
    paid_amount = Column(Numeric(12,2), default=0)
    status = Column(String(32), nullable=False, default='open')     # open, partial, paid, overdue
    paid_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    payments = relationship("ReceivablePayment", back_populates="receivable", cascade="all, delete-orphan")
