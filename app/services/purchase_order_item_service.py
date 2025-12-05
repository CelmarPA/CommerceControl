# app/services/purchase_order_item_service.py

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.repositories.purchase_order_item_repository import PurchaseOrderItemRepository
from app.repositories.purchase_order_repository import PurchaseOrderRepository
from app.schemas.purchase_order_schema import PurchaseOrderItemCreate
from  app.models.purchase_order_item import PurchaseOrderItem


class PurchaseOrderItemService:

    def __init__(self, db: Session):
        self.db = db
        self.repo = PurchaseOrderItemRepository(db)
        self.order_repo = PurchaseOrderRepository(db)

    def add_item(self, order_id: int, payload: PurchaseOrderItemCreate) -> PurchaseOrderItem:
        order = self.order_repo.get(order_id)

        if not order:
            raise HTTPException(404, "Purchase order not found")

        if order.status != "PENDING":
            raise HTTPException(400,  "Order already received — cannot add items")

        item = PurchaseOrderItem(
            purchase_order_id=order_id,
            product_id=payload.product_id,
            quantity_ordered=payload.quantity_ordered,
            cost_price=payload.cost_price
        )

        saved = self.repo.create(item)
        self.order_repo.recalc_totals_and_status(order)

        return saved
