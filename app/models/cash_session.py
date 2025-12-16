# app/models/cash_session.py

from sqlalchemy import Column, Integer, DateTime, Numeric, ForeignKey, String, func

from app.database import Base


class CashSession(Base):

    __tablename__ = "cash_sessions"

    id = Column(Integer, primary_key=True, index=True)

    cash_register_id = Column(Integer, ForeignKey('cash_registers.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)

    opened_at = Column(DateTime(timezone=True), server_default=func.now())
    closed_at = Column(DateTime(timezone=True), nullable=True)

    opening_balance = Column(Numeric(12, 2), nullable=False)
    closing_balance = Column(Numeric(12, 2), nullable=True)

    status = Column(String(20), default="open")     # open | closed
