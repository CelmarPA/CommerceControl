# app/repositories/purchase_order_item_repository.py

from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import Optional, List

from app.models.purchase_order_item import PurchaseOrderItem


class PurchaseOrderItemRepository:

    def __init__(self, db: Session):
        self.db = db

    def create(self, item: PurchaseOrderItem) -> PurchaseOrderItem:
        try:
            self.db.add(item)
            self.db.commit()
            self.db.refresh(item)

            return item

        except IntegrityError as e:
            self.db.rollback()

            raise ValueError(f"DB error creating PurchaseOrderItem: {e}")

    def get(self, item_id: int) -> Optional[PurchaseOrderItem]:
        return self.db.query(PurchaseOrderItem).filter(PurchaseOrderItem.id == item_id).first()

    def list_by_order(self, order_id: int) -> List[PurchaseOrderItem]:
        return self.db.query(PurchaseOrderItem).filter(PurchaseOrderItem.purchase_order_id == order_id).order_by(PurchaseOrderItem.id.asc()).all()

    def update(self, item: PurchaseOrderItem) -> PurchaseOrderItem:
        try:
            self.db.commit()
            self.db.refresh(item)

            return item

        except IntegrityError as e:
            self.db.rollback()

            raise ValueError(f"DB error updating PurchaseOrderItem: {e}")

    def increase_received(self, item: PurchaseOrderItem, received_qty: Decimal) -> PurchaseOrderItem:
        """
        Safely increase quantity_received (called when a receipt is processed).
        """

        item.quantity_received = (Decimal(item.quantity_received or 0) + Decimal(received_qty))

        return self.update(item)

    def delete(self, item: PurchaseOrderItem) -> None:
        try:
            self.db.delete(item)
            self.db.commit()

        except IntegrityError as e:
            self.db.rollback()

            raise ValueError(f"DB error deleting PurchaseOrderItem: {e}")
