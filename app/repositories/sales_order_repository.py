# app/repositories/sales_order_repository.py
from typing import List

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from decimal import Decimal

from app.models.sale_orders import SalesOrder


class SalesOrderRepository:

    def __init__(self, db: Session):
        self.db = db

    def create(self, order: SalesOrder) -> SalesOrder:
        try:
            self.db.add(order)
            self.db.commit()
            self.db.refresh(order)

            return order

        except IntegrityError as e:
            self.db.rollback()

            raise ValueError("Error creating Sales Order")

    def get(self, order_id: int) -> SalesOrder:
        return(
            self.db.query(SalesOrder)
            .filter(SalesOrder.id == order_id)
            .first()
        )

    def list(self) -> List[SalesOrder]:
        return self.db.query(SalesOrder).order_by(SalesOrder.id.desc()).all()
