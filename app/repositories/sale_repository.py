# app/repositories/sale_repository.py

from sqlalchemy.orm import Session
from typing import Optional, List, Any

from app.models.sale import Sale
from app.models.sale_item import SaleItem
from app.models.payment import Payment


class SaleRepository:

    def __init__(self, db: Session):
        self.db = db

    def create(self, sale: Sale) -> Sale:
        self.db.add(sale)
        self.db.flush()
        self.db.refresh(sale)

        return sale

    def get(self, sale_id: int) -> Optional[Sale]:
        return self.db.query(Sale).filter(Sale.id == sale_id).first()

    def list(self) -> List[Sale]:
        return self.db.query(Sale).order_by(Sale.id.desc()).all()

    def add_item(self, item: SaleItem) -> SaleItem:
        self.db.add(item)
        self.db.flush()
        self.db.refresh(item)

        return item

    def remove_item(self, item: SaleItem) -> None:
        self.db.delete(item)
        self.db.flush()

        return None

    def add_payment(self, payment: Payment) -> Payment:
        self.db.add(payment)
        self.db.flush()
        self.db.refresh(payment)

        return payment

    def update(self, obj) -> Any:
        self.db.flush()
        self.db.refresh(obj)

        return obj
