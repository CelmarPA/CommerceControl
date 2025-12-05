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

        stock = 0

        for m in movements:
            if m.movement_type == "IN":
                stock += m.quantity

            elif m.movement_type == "OUT":
                stock -= m.quantity

            elif m.movement_type == "ADJUST":
                stock += m.quantity

        return stock

    # --------------------------
    # APPLY MOVEMENT
    # ---------------------------
    def apply_movement(self,  payload: StockMovementCreate) -> StockMovement:
        """
        Registers a stock movement and validates inventory rules.
        """

        product = self.db.query(Product).filter(Product.id == payload.product_id).first()

        if not product:
            raise ValueError("Product not found")

        # Calculates CURRENT inventory without a physical field
        current_stock = self.get_current_stock(payload.product_id)

        if payload.movement_type == "OUT" and current_stock <  payload.quantity:
            raise ValueError("Not enough stock")

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

    # --------------------------
    # SIMPLE MODE — USED AT PDV
    # --------------------------
    def apply_movement_simple(self, product_id: int, quantity: float, movement_type: str, description: str = "") -> StockMovement:
        """
        Helper used by PDV
        """

        payload = StockMovementCreate(
            product_id=product_id,
            quantity=quantity,
            movement_type=movement_type,
            description=description
        )
        return self.apply_movement(payload)

    # --------------------------
    # LIST MOVEMENTS
    # ---------------------------
    def list(self, product_id: int | None = None) -> List[StockMovement]:
        query = self.db.query(StockMovement)

        if product_id:
            query = query.filter(StockMovement.product_id == product_id)

        return query.order_by(StockMovement.id.desc()).all()

