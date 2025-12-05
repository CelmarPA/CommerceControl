# app/models/receivable_payment.py

from sqlalchemy import Column, Integer, ForeignKey, Numeric, DateTime, func
from sqlalchemy.orm import relationship

from app.database import Base


class ReceivablePayment(Base):

    __tablename__ = "receivable_payments"

    id = Column(Integer, primary_key=True, index=True)

    receivable_id = Column(Integer, ForeignKey('accounts_receivable.id'), nullable=False, index=True)
    amount = Column(Numeric(12, 2), nullable=False)
    paid_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    user_id = Column(Integer, nullable=True)

    receivable = relationship("AccountReceivable", back_populates="payments")
