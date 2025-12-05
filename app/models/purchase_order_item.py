# app/models/purchase_order_item.py

from sqlalchemy import Column, Integer, ForeignKey, Numeric
from sqlalchemy.orm import relationship

from app.database import Base


class PurchaseOrderItem(Base):

    __tablename__ = "purchase_order_items"

    id = Column(Integer, primary_key=True, index=True)
    purchase_order_id = Column(Integer, ForeignKey("purchase_orders.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)

    quantity_ordered = Column(Numeric(12, 2), nullable=False)
    quantity_received = Column(Numeric(12, 2), default=0)
    cost_price = Column(Numeric(12, 2), nullable=False)

    order = relationship("PurchaseOrder", back_populates="items")
    product = relationship("Product")