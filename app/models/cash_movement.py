# app/models/cash_movement.py

from sqlalchemy import Column, Integer, String, Numeric, ForeignKey, DateTime, func

from app.database import Base


class CashMovement(Base):

    __tablename__ = 'cash_movements'

    id = Column(Integer, primary_key=True, index=True)

    cash_session_id = Column(Integer, ForeignKey('cash_sessions.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)

    movement_type = Column(String(20), nullable=False)   # sale | withdrawal | supply | refund | adjustment
    amount = Column(Numeric(12, 2), nullable=False)

    reason = Column(String(255), nullable=True)
    reference_id = Column(Integer, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
