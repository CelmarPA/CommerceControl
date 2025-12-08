# app/repositories/stock_repository.py
from decimal import Decimal
from typing import List

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.stock_movement import StockMovement
from app.models.product import Product
from app.schemas.stock_schema import StockMovementCreate


class StockRepository:

    def __init__(self, db: Session):
        self.db = db

    # ---------------------------
    # CURRENT STOCK CALCULATION
    # ---------------------------
    def get_current_stock(self, product_id: int) -> int:
        """
        Calculates the current stock based on all movements.
        """

        movements = (
            self.db.query(StockMovement)
            .filter(StockMovement.product_id == product_id)
            .all()
        )

        stock = Decimal("0")

        for m in movements:
            qty = Decimal(m.quantity)

            if m.movement_type == "IN":
                stock += qty

            elif m.movement_type == "OUT":
                stock -= qty

            elif m.movement_type == "ADJUST":
                stock += qty

        return stock

    # --------------------------
    # APPLY MOVEMENT
    # ---------------------------
    def apply_movement_simple_no_commit(self, product_id: int, quantity: float, movement_type: str, description: str = "") -> StockMovement:
        """
        Applies the transaction without committing it. Used by services that manage transactions.
        """

        product = self.db.query(Product).filter(Product.id == product_id).first()

        if not product:
            raise ValueError("Product not found")

        # validate stock if it is OUT
        if movement_type == "OUT":
            current_stock = self.get_current_stock(product_id)

            if current_stock is None or float(current_stock) < float(quantity):
                raise ValueError("Not enough stock")


        movement = StockMovement(
            product_id=product_id,
            quantity=quantity,
            movement_type=movement_type,
            description=description
        )

        try:
            self.db.add(movement)
            self.db.flush()
            self.db.refresh(movement)

            return movement

        except IntegrityError:
            self.db.rollback()

            raise ValueError("Failed to create movement")

    # --------------------------
    # LIST MOVEMENTS
    # ---------------------------
    def list(self, product_id: int | None = None) -> List[StockMovement]:
        query = self.db.query(StockMovement)

        if product_id:
            query = query.filter(StockMovement.product_id == product_id)

        return query.order_by(StockMovement.id.desc()).all()

