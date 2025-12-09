from sqlalchemy.orm import Session
from typing import List

from app.models.stock_movement import StockMovement
from app.schemas.stock_schema import StockMovementCreate
from app.repositories.stock_repository import StockRepository


class StockService:

    def __init__(self, db: Session):
        self.db = db
        self.repo = StockRepository(db)

    def apply_movement(self, payload: StockMovementCreate) -> StockMovement:
        movement = self.repo.apply_movement_simple_no_commit(**payload.model_dump())

        self.db.commit()
        self.db.refresh(movement)

        return movement

    def list(self, product_id: int | None = None) -> List[StockMovement]:
        return self.repo.list(product_id)

    def get_stock(self, product_id: int) -> StockMovement:
        current_stock = self.repo.get_current_stock(product_id)

        return {
            "product_id": product_id,
            "stock": current_stock
        }
