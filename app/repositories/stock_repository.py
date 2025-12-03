# app/repositories/stock_repository.py
from typing import List

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.stock_movement import StockMovement
from app.models.product import Product
from app.schemas.stock_schema import StockMovementCreate


class StockRepository:

    def __init__(self, db: Session):
        self.db = db

    def apply_movement(self,  payload: StockMovementCreate) -> StockMovement:
        product = self.db.query(Product).filter(Product.id == payload.product_id).first()

        if not product:
            raise ValueError("Product not found")

        if payload.movement_type == "IN":
            product.strock += payload.quantity

        elif payload.movement_type == "OUT":
            if product.strock < payload.quantity:
                raise ValueError("Not enough stock")

        elif payload.movement_type == "ADJUST":
            product.strock += payload.quantity

        movement = StockMovement(
            product_id=payload.product_id,
            quantity=payload.quantity,
            movement_type=payload.movement_type,
            description=payload.description,
        )

        try:
            self.db.add(movement)
            self.db.commit()
            self.db.refresh(movement)

            return movement

        except IntegrityError:
            self.db.rollback()

            raise ValueError("Failed to create movement")

    def list(self, product_id: int | None = None) -> List[StockMovement]:
        query = self.db.query(StockMovement)

        if product_id:
            query = query.filter(StockMovement.product_id == product_id)

        return query.order_by(StockMovement.id.desc()).all()
