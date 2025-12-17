# app/models/payable.py

from sqlalchemy import Column, Integer, Numeric, DateTime, String, ForeignKey, func

from app.database import Base


class Payable(Base):

    __tablename__ = 'payables'

    id = Column(Integer, primary_key=True, index=True)
    supplier_id = Column(Integer, ForeignKey('suppliers.id'), nullable=False)

    description = Column(String(255), nullable=True)

    amount = Column(Numeric(12, 2), nullable=False)
    paid_amount = Column(Numeric(12, 2), default=0)

    due_date = Column(DateTime(timezone=True), nullable=False)
    paid_at = Column(DateTime(timezone=True), nullable=True)

    status = Column(String(20), default="open")   # open | partial | paid | canceled

    reference_type = Column(String(50), nullable=True)
    reference_id = Column(Integer, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
