# app/models/credit_history.py

from sqlalchemy import Column, Integer, ForeignKey, String, Numeric, DateTime, func
from sqlalchemy.orm import relationship

from app.database import Base


class CreditHistory(Base):

    __tablename__ = 'credit_history'

    id = Column(Integer, primary_key=True,  index=True)
    customer_id = Column(Integer, ForeignKey('customers.id'), nullable=False, index=True)

    event_type = Column(String(50), nullable=False)  # sale_created, payment, limit_change, policy_change...
    amount = Column(Numeric(12, 2), nullable=False, default=0)
    balance_after = Column(Numeric(12, 2), nullable=False, default=0)
    notes = Column(String(255), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    customer = relationship("Customer", back_populates="credit_history")