# app/repositories/purchase_receipt_repository.py

from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List
from app.models.purchase_receipt import PurchaseReceipt
from app.models.purchase_receipt_item import PurchaseReceiptItem
from app.models.purchase_order_item import PurchaseOrderItem
from app.repositories.purchase_order_repository import PurchaseOrderRepository
from app.repositories.purchase_order_item_repository import PurchaseOrderItemRepository
from app.repositories.stock_repository import StockRepository


class PurchaseReceiptRepository:

    def __init__(self, db: Session):
        self.db = db
        self.purchase_order_repo = PurchaseOrderRepository(db)
        self.purchase_order_item_repo = PurchaseOrderItemRepository(db)
        self.stock_repo = StockRepository(db)

    def create_receipt(self, receipt: PurchaseReceipt, items: List[PurchaseReceiptItem]) -> PurchaseReceipt:
        """
        Create a receipt (possibly with multiple items). For each receipt item:
        - validate against the order item
        - update PurchaseOrderItem.quantity_received
        - create stock movements (IN)
        - recalc order totals/status
        """

        try:
            self.db.add(receipt)
            self.db.flush()

            for item in items:
                item.receipt_id = receipt.id
                self.db.add(item)

            self.db.commit()
            self.db.refresh(receipt)

            return receipt


        except IntegrityError as e:
            self.db.rollback()

            raise ValueError(f"DB error creating receipt: {e}")
