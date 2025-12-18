# app/models/cash_flow.py

from sqlalchemy import Column, Integer, String, Date, DateTime, func, Numeric, Index

from app.database import Base


class CashFlow(Base):

    __tablename__ = "cash_flows"

    id = Column(Integer, primary_key=True, index=True)

    date = Column(Date, nullable=False)

    flow_type = Column(String(10), nullable=False)  # IN | OUT
    category = Column(String(50), nullable=False)

    amount = Column(Numeric(12, 2), nullable=False)

    reference_type = Column(String(50), nullable=True)   # receivable | payable | sale | cash
    reference_id = Column(Integer, nullable=True)

    description = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("ix_cash_flow_date", "date"),
        Index("ix_cash_flow_entry_type", "flow_type"),
        Index("ix_cash_flow_category", "category")
    )
