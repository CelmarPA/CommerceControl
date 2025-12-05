# app/models/purchase_order.py

from sqlalchemy import Column, Integer, ForeignKey, String, DateTime, Numeric, func
from sqlalchemy.orm import relationship

from app.database import Base


class PurchaseOrder(Base):

    __tablename__ = "purchase_orders"

    id = Column(Integer, primary_key=True, index=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False)

    status = Column(String(20), default="PENDING")  # PENDING / PARTIAL / RECEIVED / CANCELED
    expected_date = Column(DateTime(timezone=True), nullable=True)
    notes = Column(String(255), nullable=True)

    total_amount = Column(Numeric(12, 2), default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


    supplier = relationship("Supplier", back_populates="purchase_orders")
    items = relationship("PurchaseOrderItem", back_populates="order", cascade="all, delete")
    receipts = relationship("PurchaseReceipt", back_populates="order")
