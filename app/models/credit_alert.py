# app/models/credit_alert.py

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, func

from app.database import Base

class CreditAlert(Base):

    __tablename__ = 'credit_alerts'

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey('customers.id'), index=True)

    alert_type = Column(String(50), nullable=False)
    message = Column(String(255), nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    resolved = Column(Boolean, default=False)
