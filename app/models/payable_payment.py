# app/models/payable_payment.py

from sqlalchemy import Column, Integer, Numeric, DateTime, ForeignKey, func

from app.database import Base


class PayablePayment(Base):

    __tablename__ = 'payable_payments'

    id = Column(Integer, primary_key=True, index=True)
    payable_id = Column(Integer, ForeignKey('payables.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)

    amount = Column(Numeric(10,2), nullable=False)

    paid_at = Column(DateTime(timezone=True), server_default=func.now())
