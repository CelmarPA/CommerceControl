# app/models/purchase_receipt_item.py

from sqlalchemy import Column, Integer, ForeignKey,Numeric
from sqlalchemy.orm import relationship

from app.database import Base


class PurchaseReceiptItem(Base):

    __tablename__ = "purchase_receipt_items"

    id = Column(Integer, primary_key=True, index=True)
    receipt_id = Column(Integer, ForeignKey('purchase_receipts.id'),nullable=False)
    product_id = Column(Integer, ForeignKey('products.id'),nullable=False)

    quantity_received = Column(Numeric(12, 2), nullable=False)
    cost_price = Column(Numeric(12, 2), nullable=False)

    receipt = relationship("PurchaseReceipt", back_populates="items")
    product = relationship("Product")
