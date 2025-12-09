# app/models/receipt.py

from sqlalchemy import Column, Integer, String, ForeignKey, Numeric, DateTime, func, Text
from sqlalchemy.orm import relationship

from app.database import Base


class Receipt(Base):

    __tablename__ = "receipts"

    id = Column(Integer, primary_key=True, index=True)
    sale_id = Column(Integer, ForeignKey("sales.id"), nullable=False, index=True)

    # Basic total / printable fields
    subtotal = Column(Numeric(12, 2), nullable=False, default=0)
    discount = Column(Numeric(12, 2), nullable=True, default=0)
    total = Column(Numeric(12, 2), nullable=False, default=0)
    payment_summary = Column(Text, nullable=True) # JSON/text summary of payments
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    items = relationship("ReceiptItem", back_populates="receipt", cascade="all, delete-orphan")
    sale = relationship("Sale")
