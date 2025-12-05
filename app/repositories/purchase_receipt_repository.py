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
            # Persist receipt header
            self.db.add(receipt)
            self.db.commit()
            self.db.refresh(receipt)

            # Process items
            for r_item in items:
                # attach receipt_id to item
                r_item.receipt_id = receipt.id
                self.db.add(r_item)
                self.db.commit()
                self.db.refresh(r_item)

                # update corresponding purchase order item
                po_item = self.db.query(PurchaseOrderItem).filter(
                    PurchaseOrderItem.purchase_order_id == receipt.purchase_order_id,
                    PurchaseOrderItem.product_id == r_item.product_id
                ).first()

                if not po_item:
                    # Rollback everything if inconsistent
                    raise ValueError("Purchase order item not found for this product")

                # Compute allowable receive quantity
                remaining = Decimal(po_item.quantity_ordered or 0) - Decimal(po_item.quantity_received or 0)

                if Decimal(r_item.quantity_received) > remaining:
                    raise ValueError("Receipt quantity exceeds remaining ordered quantity")

                # increase received quantity
                po_item.quantity_received = Decimal(po_item.quantity_received or 0) + Decimal(r_item.quantity_received)

                self.db.commit()
                self.db.refresh(po_item)

                # Create stock movement IN for received quantity
                self.stock_repo.apply_movement_simple(
                    product_id=r_item.product_id,
                    quantity=float(r_item.quantity_received),
                    movement_type="IN",
                    description=f"Purchase order {receipt.purchase_order_id} - Receipt {receipt.id}"
                )

            # after processing items, recalc PO totals/status
            po = self.purchase_order_repo.get(receipt.purchase_order_id)
            self.purchase_order_repo.recalc_totals_and_status(po)

            return receipt

        except IntegrityError as e:
            self.db.rollback()

            raise ValueError(f"DB error creating receipt: {e}")

        except Exception:
            # any custom validation error -> rollback and re-raise
            self.db.rollback()

            raise
