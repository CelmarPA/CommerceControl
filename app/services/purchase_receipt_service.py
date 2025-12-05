# app/services/purchase_receipt_service.py

from fastapi import HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.models.purchase_receipt import PurchaseReceipt
from app.models.purchase_receipt_item import PurchaseReceiptItem
from app.repositories.purchase_receipt_repository import PurchaseReceiptRepository
from app.repositories.purchase_order_repository import PurchaseOrderRepository

from app.schemas.purchase_receipt_schema import (
    PurchaseReceiptCreate,
    PurchaseReceiptItemCreate
)


class PurchaseReceiptService:

    def __init__(self, db: Session):
        self.db = db
        self.repo = PurchaseReceiptRepository(db)
        self.order_repo = PurchaseOrderRepository(db)

    # ─────────────────────────────────────────────
    # CREATE RECEIPT (Goods receipt)
    # ─────────────────────────────────────────────
    def create_receipt(self, payload: PurchaseReceiptCreate) -> PurchaseReceipt:
        order = self.order_repo.get(payload.purchase_order_id)

        if not order:
            raise HTTPException(status_code=404, detail="Purchase Order not found")

        if order.status == "RECEIVED":
            raise HTTPException(status_code=400, detail="Purchase Order already  fully received")

        receipt = PurchaseReceipt(
            purchase_order_id=payload.purchase_order_id,
            nfe_key=payload.nfe_key,
            note_number=payload.note_number,
            serie=payload.serie,
            cfop=payload.cfop,
            issue_date=payload.issue_date,
            arrival_date=payload.arrival_date,
            total_amount=payload.total_amount,
            freight=payload.freight,
            insurance=payload.insurance,
            discount=payload.discount,
            other_expenses=payload.other_expenses,
            xml_path=payload.xml_path
        )

        # Build receipt items
        items = []

        for item_data in payload.items:
            items.append(
                PurchaseReceiptItem(
                    product_id=item_data.product_id,
                    quantity_received=item_data.quantity_received,
                    cost_price=item_data.cost_price,
                )
            )

        try:
            return self.repo.create_receipt(receipt, items)

        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    # ─────────────────────────────────────────────
    # LIST RECEIPTS OF AN ORDER
    # ─────────────────────────────────────────────
    def list_for_order(self, order_id: int) -> List[PurchaseReceipt]:
        order = self.order_repo.get(order_id)

        if not order:
            raise HTTPException(status_code=404, detail="Purchase order not found")

        return order.receipts
