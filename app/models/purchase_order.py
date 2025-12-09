# app/models/purchase_order.py

from enum import Enum
from sqlalchemy import Column, Integer, ForeignKey, String, DateTime, Numeric, func
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import relationship


from app.database import Base


class PurchaseOrderStatus(str, Enum):
    PENDING = "pending"
    PARTIAL = "partial"
    RECEIVED = "received"
    CANCELED = "canceled"


class PurchaseOrder(Base):

    __tablename__ = "purchase_orders"

    id = Column(Integer, primary_key=True, index=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False)

    status = Column(SAEnum(PurchaseOrderStatus, native_enum=False), default=PurchaseOrderStatus.PENDING, nullable=False)
    expected_date = Column(DateTime(timezone=True), nullable=True)
    notes = Column(String(255), nullable=True)

    total_amount = Column(Numeric(12, 2), default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


    supplier = relationship("Supplier", back_populates="purchase_orders")
    items = relationship("PurchaseOrderItem", back_populates="order", cascade="all, delete")
    receipts = relationship("PurchaseReceipt", back_populates="order")
