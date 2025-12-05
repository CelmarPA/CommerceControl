# app/models/purchase_receipt.py

from sqlalchemy import Column, Integer, ForeignKey, String, DateTime, Numeric, func
from sqlalchemy.orm import relationship

from app.database import Base


class PurchaseReceipt(Base):

    __tablename__ = "purchase_receipts"

    id = Column(Integer, primary_key=True, index=True)
    purchase_order_id = Column(Integer, ForeignKey('purchase_orders.id'), nullable=False)

    # ===============================
    # Invoice Data (NFe)
    # ===============================
    nfe_key = Column(String(44), nullable=True)     # access key
    note_number = Column(String(20), nullable=True) # number of the note
    serie = Column(String(10), nullable=True)       # NFe series
    cfop = Column(String(10), nullable=True)        # CFOP of the operation

    issue_date = Column(DateTime(timezone=True), nullable=True)
    arrival_date = Column(DateTime(timezone=True), nullable=True)

    # NFe Totals
    total_amount = Column(Numeric(12, 2), nullable=True)
    freight = Column(Numeric(12, 2), nullable=True)
    insurance = Column(Numeric(12, 2), nullable=True)
    discount = Column(Numeric(12, 2), nullable=True)
    other_expenses = Column(Numeric(12, 2), nullable=True)

    # Imported XML file (optional)
    xml_path = Column(String(255), nullable=True)

    # ===============================
    # Internal Control
    # ===============================
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    order = relationship("PurchaseOrder", back_populates="receipts")
    items = relationship("PurchaseReceiptItem", back_populates="receipt")
