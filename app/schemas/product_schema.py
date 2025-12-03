# app/schemas/product_schema.py

"""
Product Schemas
---------------

Schemas used for creating, updating, and returning product information.
"""

from decimal import Decimal
from pydantic import BaseModel, Field
from typing import Optional, List, Any


# -----------------------------------------
# Base
# -----------------------------------------
class ProductBase(BaseModel):
    """
    Base schema with common product attributes.

    :param name: Name of the product.
    :type name: str

    :param description: Detailed description of the product.
    :type description: str | None

    :param price: Monetary price of the product.
    :type price: float

    :param stock: Quantity of the product available in stock.
    :type stock: int
    """

    name: str = Field(..., description="Product name")
    sku: Optional[str] = Field(None, description="Unique SKU code")
    barcode: Optional[str] = Field(None, description="Product barcode")
    description: Optional[str] = None
    unit: Optional[str] = "unit"
    category_id: Optional[int] = None


# -----------------------------------------
# Create
# -----------------------------------------
class ProductCreate(ProductBase):
    """
    Schema for creating a new product.

    Inherits all fields from ProductBase.
    """
    cost_price: Optional[Decimal] = None
    sell_price: Decimal = Field(..., description="Selling price")
    tax: Optional[Any] = None
    images: Optional[List[str]] = None


# -----------------------------------------
# Update
# -----------------------------------------
class ProductUpdate(BaseModel):
    name: Optional[str]
    sku: Optional[str]
    barcode: Optional[str]
    description: Optional[str]
    cost_price: Optional[Decimal]
    sell_price: Optional[Decimal]
    unit: Optional[str]
    category_id: Optional[int]
    tax: Optional[Any]
    images: Optional[List[str]]


# -----------------------------------------
# Output / Read-only
# -----------------------------------------
class ProductRead(ProductBase):
    id: int
    cost_price: Optional[Decimal]
    sell_price: Decimal
    tax: Optional[Any]
    images: Optional[List[str]]

    class Config:
        from_attributes = True


# -----------------------------------------
# Output with full detail
# -----------------------------------------
class ProductOut(ProductRead):
    pass
