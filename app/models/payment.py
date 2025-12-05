# app/models/payment.py
from pygments.lexers import q
from sqlalchemy import Column, Integer, ForeignKey, Numeric, String, DateTime, func
from sqlalchemy.orm import relationship

from app.database import Base


class Payment(Base):

    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)

    sale_id = Column(Integer, ForeignKey('sales.id'), nullable=False, index=True)
    method = Column(String(32), nullable=False)  # cash, pix, card, credit
    amount = Column(Numeric(12, 2), nullable=False)
    provider_reference = Column(String(255), nullable=True)
    paid_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    sale = relationship("Sale", back_populates="payments")
