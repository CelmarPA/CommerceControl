# app/repositories/purchase_receipt_item_repository.py

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List, Optional

from app.models.purchase_receipt_item import PurchaseReceiptItem


class PurchaseReceiptItemRepository:

    def __init__(self, db: Session):
        self.db = db

    def create(self, item: PurchaseReceiptItem) -> PurchaseReceiptItem:
        try:
            self.db.add(item)
            self.db.commit()
            self.db.refresh(item)

            return item

        except IntegrityError as e:
            self.db.rollback()

            raise ValueError(f"DB error creating PurchaseReceiptItem: {e}")

    def get(self, item_id: int) -> Optional[PurchaseReceiptItem]:
        return self.db.query(PurchaseReceiptItem).filter(PurchaseReceiptItem.id == item_id).first()

    def list_by_receipt(self, receipt_id: int) -> List[PurchaseReceiptItem]:
        return self.db.query(PurchaseReceiptItem).filter(PurchaseReceiptItem.receipt_id == receipt_id).order_by(PurchaseReceiptItem.id.asc()).all()
