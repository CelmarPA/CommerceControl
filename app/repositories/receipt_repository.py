# app/repositories/receipt_repository.py

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List

from app.models.receipt import Receipt
from app.models.receipt_item import ReceiptItem


class ReceiptRepository:

    def __init__(self, db: Session):
        self.db = db

    def create(self, receipt: Receipt, items: List[ReceiptItem]) -> Receipt:
        try:
            self.db.add(receipt)
            self.db.flush()

            for item in items:
                item.receipt_id = receipt.id
                self.db.add(item)

            self.db.flush()
            self.db.refresh(receipt)

            return receipt

        except IntegrityError as e:
            self.db.rollback()
            raise ValueError(f"DB error creating receipt: {e}")

    def get(self, receipt_id: int) -> Receipt | None:
        return self.db.query(Receipt).filter(Receipt.id == receipt_id).first()

    def list_for_sale(self, sale_id: int) -> List[Receipt]:
        return self.db.query(Receipt).filter(Receipt.sale_id == sale_id).order_by(Receipt.id.desc()).all()
