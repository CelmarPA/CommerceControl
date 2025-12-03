# app/models/customer.py

from sqlalchemy import Column, Integer, String, DateTime, func, Boolean

from app.database import Base


class Customer(Base):

    __tablename__ = 'customers'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    phone = Column(String(30), nullable=True)
    cpf_cnpj = Column(String(20), unique=True, nullable=True)
    address = Column(String(255), nullable=True)
    zip_code = Column(String(10), nullable=True)
    city = Column(String(10), nullable=True)
    state = Column(String(15), nullable=True)

    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False)

    deleted_at = Column(DateTime(timezone=True), nullable=True)


