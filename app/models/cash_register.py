# app/models/cash_register.py

from sqlalchemy import Column, Integer, String, Boolean

from app.database import Base


class CashRegister(Base):

    __tablename__ = "cash_registers"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String(50), nullable=False)
    is_active = Column(Boolean, default=True)
