# app/repositories/purchase_order_repository.py

from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List, Optional

from app.models.purchase_order import PurchaseOrder, PurchaseOrderStatus
from app.repositories.stock_repository import StockRepository


class PurchaseOrderRepository:

    def __init__(self, db: Session):
        self.db = db
        self.stock_repo = StockRepository(db)

    # CRUD: PurchaseOrder
    def create(self, po: PurchaseOrder) -> PurchaseOrder:
        try:
            self.db.add(po)
            self.db.commit()
            self.db.refresh(po)

            return po

        except IntegrityError as e:
            self.db.rollback()

            raise ValueError(f"DB error creating PurchaseOrder: {e}")

    def get(self, order_id: int) -> Optional[PurchaseOrder]:
        return self.db.query(PurchaseOrder).filter(PurchaseOrder.id == order_id).first()

    def list(self) -> List[PurchaseOrder]:
        return self.db.query(PurchaseOrder).order_by(PurchaseOrder.id.desc()).all()

    def update_no_commit(self, po: PurchaseOrder) -> PurchaseOrder:
        self.db.flush()
        self.db.refresh(po)
        return po

    def delete(self, po: PurchaseOrder) -> None:
        try:
            self.db.delete(po)
            self.db.commit()

        except IntegrityError as e:
            self.db.rollback()

            raise ValueError(f"DB error deleting PurchaseOrder: {e}")

    # Helpers for order status / totals
    def recalc_totals_and_status(self, po: PurchaseOrder) -> PurchaseOrder:
        """
        Recalculates total_amount from items and sets status:
        - pending if nothing received
        - partial if some items partially received
        - received if all quantities received
        """
        total = Decimal(0)
        all_received = True
        any_received = False

        for item in po.items:
            total += Decimal(item.cost_price or 0) * Decimal(item.quantity_ordered or 0)

            if (item.quantity_received or 0) > 0:
                any_received = True

            if Decimal(item.quantity_received or 0) < Decimal(item.quantity_ordered or 0):
                all_received = False

        po.total_amount = total

        if all_received and any_received:
            po.status = PurchaseOrderStatus.RECEIVED

        elif all_received:
            po.status = PurchaseOrderStatus.PARTIAL

        else:
            po.status = PurchaseOrderStatus.PENDING

        return self.update_no_commit(po)
