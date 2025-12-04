# app/models/suppliers.py
from sqlalchemy import Column, Integer, String, DateTime, Boolean, func

from app.database import Base


class Supplier(Base):

    __tablename__ = 'suppliers'

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String(255), nullable=False, index=True)
    cnpj = Column(String(32), unique=True, nullable=False, index=True)

    email = Column(String(255), nullable=True, index=True)
    phone = Column(String(32), nullable=True, index=True)

    address = Column(String(255), nullable=True)
    city = Column(String(128), nullable=True)
    state = Column(String(32), nullable=True)
    zip_code = Column(String(32), nullable=True)

    is_active = Column(Boolean, default=True, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
