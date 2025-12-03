# app/routers/product.py

"""
Products Router
---------------

This module exposes endpoints for managing products.

Features:
- Public product listing
- Product detail retrieval
- Admin-protected product creation, update and deletion

All write operations require admin or superadmin permissions.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.product import Product
from app.core.permissions import admin_required
from app.repositories.product_repository import ProductRepository

from app.schemas.product_schema import (
    ProductCreate,
    ProductRead,
    ProductUpdate,
    ProductOut
)

router = APIRouter(prefix="/products", tags=["Products"])


# -----------------------------------------
# LIST
# -----------------------------------------
@router.get("/", response_model=List[ProductRead])
def list_products(
    q: str = Query(None),
    page: int = 1,
    per_page: int = 20,
    db: Session = Depends(get_db)
) -> List[ProductRead]:
    """
    List products with optional name filtering and pagination.

    :param per_page:
    :param page:
    :param q: Optional substring to search in product names.
    :type q: str | None

    :param skip: Number of items to skip.
    :type skip: int

    :param limit: Maximum number of items to return.
    :type limit: int

    :param db: Active database session.
    :type db: Session

    :return: List of matching products.
    :rtype: list[ProductOut]
    """

    repo = ProductRepository(db)

    return repo.list(q, page=page, per_page=per_page)


# -----------------------------------------
# GET
# -----------------------------------------
@router.get("/{product_id}", response_model=ProductOut)
def get_product(
        product_id: int,
        db: Session = Depends(get_db)
) -> ProductOut:
    """
    Retrieve a single product by its ID.

    :param product_id: ID of the product.
    :type product_id: int

    :param db: Active database session.
    :type db: Session

    :return: Product details if found.
    :rtype: ProductOut
    """

    repo = ProductRepository(db)
    product = repo.get(product_id)

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    return product


# -----------------------------------------
# CREATE
# -----------------------------------------
@router.post('/', response_model=ProductCreate, dependencies=[Depends(admin_required)], status_code=status.HTTP_201_CREATED)
def create_product(
    payload: ProductCreate,
    db: Session = Depends(get_db)
) -> Product:
    """
    Create a new product. Admin or superadmin only.

    :param payload: Product creation data.
    :type payload: ProductCreate

    :param db: Active database session.
    :type db: Session

    :return: Newly created product.
    :rtype: Product
    """

    repo = ProductRepository(db)

    try:
        return repo.create(payload)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# -----------------------------------------
# UPDATE
# -----------------------------------------
@router.put("/{product_id}", response_model=ProductOut, dependencies=[Depends(admin_required)])
def update_product(
    product_id: int,
    payload: ProductUpdate,
    db: Session = Depends(get_db)
) -> ProductOut:
    """
    Update an existing product. Admin or superadmin only.

    :param product_id: ID of the product to update.
    :type product_id: int

    :param payload: Fields to update.
    :type payload: ProductUpdate

    :param db: Active database session.
    :type db: Session

    :return: Updated product.
    :rtype: Product
    """

    repo = ProductRepository(db)

    try:
        updated = repo.update(product_id, payload)

    except ValueError as e:
        return HTTPException(status_code=400, detail=str(e))

    if not updated:
        raise HTTPException(status_code=404, detail="Product not found")

    return updated


# -----------------------------------------
# DELETE
# -----------------------------------------
@router.delete("/{product_id}", response_model=ProductOut, dependencies=[Depends(admin_required)])
def delete_product(
    product_id: int,
    db: Session = Depends(get_db)
) -> ProductOut:
    """
    Delete a product. Superadmin only (enforced by admin_required + role system).

    :param product_id: ID of the product to delete.
    :type product_id: int

    :param db: Active database session.
    :type db: Session

    :return: Deleted product data.
    :rtype: ProductOut
    """

    repo = ProductRepository(db)

    deleted = repo.delete(product_id)

    if not deleted:
        raise HTTPException(status_code=404, detail="Product not found")

    return deleted
