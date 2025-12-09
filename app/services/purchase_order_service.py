# app/services/purchase_order_service.py

from fastapi import HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.models.product import Product
from app.models.purchase_order import PurchaseOrder
from app.models.purchase_order_item import PurchaseOrderItem
from app.models.suppliers import Supplier
from app.repositories.purchase_order_item_repository import PurchaseOrderItemRepository
from app.repositories.purchase_order_repository import PurchaseOrderRepository

from app.schemas.purchase_order_schema import (
    PurchaseOrderCreate,
    PurchaseOrderItemCreate
)


class PurchaseOrderService:

    def __init__(self, db: Session):
        self.db = db
        self.repo = PurchaseOrderRepository(db)
        self.item_repo = PurchaseOrderItemRepository(db)

    # ─────────────────────────────────────────────
    # CREATE PURCHASE ORDER
    # ─────────────────────────────────────────────
    def create_order(self, payload: PurchaseOrderCreate) -> PurchaseOrder:
        # 1. Validate supplier
        supplier = self.db.query(Supplier).filter(Supplier.id == payload.supplier_id).first()

        if not supplier:
            raise HTTPException(status_code=404, detail=f"Supplier ID {payload.supplier_id} not found")

        # 2. Validate products before creating the PO
        for item in payload.items:
            product = self.db.query(Product).filter(Product.id == item.product_id).first()

            if not product:
                raise HTTPException(status_code=400, detail=f"Product ID {item.product_id} not found")

        # 3. Create purchase order
        order = PurchaseOrder(
            supplier_id=payload.supplier_id,
            expected_date=payload.expected_date,
            notes=payload.notes
        )

        self.db.add(order)
        self.db.flush()  # ensures order.id is available without commit

        # 4. Add items
        for item_data in payload.items:
            order.items.append(
                PurchaseOrderItem(
                    product_id=item_data.product_id,
                    quantity_ordered=item_data.quantity_ordered,
                    cost_price=item_data.cost_price
                )
            )

        # 5. Commit everything
        self.db.commit()

        # 6. Refresh and recalc totals
        self.db.refresh(order)
        self.repo.recalc_totals_and_status(order)

        return order

    # ─────────────────────────────────────────────
    # LIST PURCHASE ORDERS
    # ─────────────────────────────────────────────
    def list(self) -> List[PurchaseOrderItem]:
        return self.repo.list()

    # ─────────────────────────────────────────────
    # GET PURCHASE ORDER
    # ─────────────────────────────────────────────
    def get(self, order_id: int) -> PurchaseOrder:
        order = self.repo.get(order_id)

        if not order:
            raise HTTPException(status_code=404, detail="Purchase order not found")

        return order

    # ─────────────────────────────────────────────
    # ADD ITEM TO ORDER
    # ─────────────────────────────────────────────
    def add_item(self, order_id: int, payload: PurchaseOrderItemCreate) -> PurchaseOrderItem:
        order = self.repo.get(order_id)

        if not order:
            raise HTTPException(status_code=404, detail="Purchase order not found")

        if order.status != "pending":
            raise HTTPException(status_code=400, detail="Cannot add items after receiving has started")

        item = PurchaseOrderItem(
            purchase_order_id=order.id,
            product_id=payload.product_id,
            quantity_ordered=payload.quantity_ordered,
            cost_price=payload.cost_price
        )

        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)

        self.repo.recalc_totals_and_status(order)

        return item

    # ─────────────────────────────────────────────
    # DELETE ORDER
    # ─────────────────────────────────────────────
    def delete(self,order_id: int) -> None:
        order = self.repo.get(order_id)

        if not order:
            raise HTTPException(status_code=404, detail="Purchase order not found")

        if order.status != "pending":
            raise HTTPException(400, "Cannot delete an order that has receipts")

        self.repo.delete(order)
