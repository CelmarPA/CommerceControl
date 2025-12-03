# app/repositories/product_repository.py

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.product import Product
from app.schemas.product_schema import ProductCreate, ProductUpdate


class ProductRepository:

    def __init__(self, db: Session):
        self.db = db

    # ------------------------------------------
    # List
    # ------------------------------------------
    def list(self, q: str = None, page: int = 1, per_page: int = 20):
        query = self.db.query(Product)

        if q:
            query = query.filter(Product.name.ilike(f"%{q}%"))

        return query.offset((page - 1) * per_page).limit(per_page).all()

    # ------------------------------------------
    # Get single
    # ------------------------------------------
    def get(self, product_id: int):
        return self.db.query(Product).filter(Product.id == product_id).first()

    # ------------------------------------------
    # Create
    # ------------------------------------------
    def create(self, payload: ProductCreate):
        obj = Product(**payload.model_dump(exclude_unset=True))

        try:
            self.db.add(obj)
            self.db.commit()
            self.db.refresh(obj)

        except IntegrityError as e:
            self.db.rollback()

            if "sku" in str(e.orig):
                raise ValueError("SKU already exists")

            if "barcode" in str(e.orig):
                raise ValueError("Barcode already exists")

            raise ValueError("Duplicate value detected")

        return obj

    # ------------------------------------------
    # Update
    # ------------------------------------------
    def update(self, product_id: int, payload: ProductUpdate):
        product = self.get(product_id)

        if not product:
            return None

        update_data = payload.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(product, field, value)

        try:
            self.db.commit()
            self.db.refresh(product)

        except IntegrityError as e:
            self.db.rollback()

            if "sku" in str(e.orig):
                raise ValueError("SKU already exists")

            if "barcode" in str(e.orig):
                raise ValueError("Barcode already exists")

            raise ValueError("Duplicate value detected")

        return product

    # ------------------------------------------
    # Delete
    # ------------------------------------------
    def delete(self, product_id: int):
        product = self.get(product_id)

        if not product:
            return None

        self.db.delete(product)
        self.db.commit()

        return product
