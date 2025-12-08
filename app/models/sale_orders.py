# app/models/sales_order.py

from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship

from app.database import Base


class SalesOrder(Base):

    __tablename__ = 'sales_orders'

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey('customers.id'), nullable=True)

    status = Column(String(20), default="OPEN")     # OPEN / PARTIAL / COMPLETED / CANCELED

    total_amount = Column(Numeric(12, 2), default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    items = relationship("SalesOrderItem", back_populates="order", cascade="all, delete")
    customer = relationship("Customer", back_populates="sales_orders", lazy="joined")
