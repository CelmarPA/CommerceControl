# app/services/sales_order_service.py
from typing import List

from fastapi import HTTPException
from sqlalchemy.orm import Session
from decimal import Decimal

from app.models.sale_orders import SalesOrder
from app.models.sales_order_item import SalesOrderItem
from app.models.product import Product
from app.repositories.sales_order_repository import SalesOrderRepository
from app.schemas.sales_order_schema import SalesOrderCreate


class SalesOrderService:

    def __init__(self, db: Session):
        self.db = db
        self.repo = SalesOrderRepository(db)

    def create(self, payload: SalesOrderCreate) -> SalesOrder:
        if not payload.items or len(payload.items) == 0:
            raise HTTPException(status_code=400, detail="Sales order must have items")

        order = SalesOrder(customer_id=payload.customer_id)
        self.db.add(order)
        self.db.flush()

        total = Decimal("0")

        for item in payload.items:
            # Validate product
            product = self.db.query(Product).filter(Product.id == item.product_id).first()

            if not product:
                raise HTTPException(status_code=404, detail=f"Product {item.product_id} not found")

            subtotal = Decimal(item.quantity) * Decimal(item.unit_price)

            total += subtotal

            order_item = SalesOrderItem(
                sales_order_id=order.id,
                product_id=product.id,
                quantity=item.quantity,
                unit_price=item.unit_price,
                subtotal=subtotal
            )

            self.db.add(order_item)

        order.total_amount = total

        return self.repo.create(order)

    def list(self) -> List[SalesOrder]:
        return self.repo.list()

    def get(self, order_id: int) -> SalesOrder:
        order = self.repo.get(order_id)

        if not order:
            raise HTTPException(status_code=404, detail=f"Sales Order {order_id} not found")

        return order
