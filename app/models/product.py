# app/models/product.py

"""
Database model for storing product information.

This table is used to manage items available in the system's catalog.
It supports:
- Listing products
- Managing stock levels
- Handling pricing (cost and selling price)
- Tracking creation timestamps
- Associating products with categories
- Storing additional metadata such as images and tax information

Each entry represents a single product in the system.
"""

from sqlalchemy import Column, Integer, String, Numeric, Text, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.types import DateTime

from app.database import Base


class Product(Base):
    """
    Represents a product available in the system.

    :param id: Primary key of the product.
    :type id: int

    :param name: Name of the product.
    :type name: str

    :param sku: Stock Keeping Unit (unique product identifier).
    :type sku: str

    :param barcode: Barcode associated with the product.
    :type barcode: str

    :param description: Detailed description of the product.
    :type description: str

    :param cost_price: Internal cost of the product (used for profit calculation).
    :type cost_price: float

    :param sell_price: Price at which the product is sold to customers.
    :type sell_price: float

    :param unit: Unit of measurement (e.g., "unit", "kg", "box").
    :type unit: str

    :param tax: JSON structure containing tax rules or percentages.
    :type tax: JSON

    :param images: JSON list storing product image URLs or metadata.
    :type images: JSON

    :param category_id: Foreign key linking the product to a category.
    :type category_id: int

    :param created_at: UTC timestamp indicating when the product was created.
    :type created_at: DateTime
    """

    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)

    sku =  Column(String(64), unique=True, index=True, nullable=True)    # Unique SKU for inventory management
    barcode = Column(String(64), unique=True, index=True, nullable=True)

    description = Column(Text, nullable=True)
    cost_price = Column(Numeric(12, 2), nullable=True)
    sell_price = Column(Numeric(12, 2), nullable=False, default=0)

    unit = Column(String(20), default="unit")

    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)  # Category relationship

    tax = Column(JSON, nullable=True)     # Tax configuration (JSON object)
    images = Column(JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    stock_movements = relationship("StockMovement", back_populates="product")