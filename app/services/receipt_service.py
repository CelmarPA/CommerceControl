# app/services/receipt_service.py
import json

from fastapi import HTTPException
from sqlalchemy.orm import Session
from decimal import Decimal
from typing import List

from app.repositories.receipt_repository import ReceiptRepository
from app.models.receipt import Receipt
from app.models.receipt_item import ReceiptItem
from app.models.sale import Sale


class ReceiptService:

    def __init__(self, db: Session):
        self.db = db
        self.repo = ReceiptRepository(db)

    def create_from_sale(self, sale_id: int, notes: str | None = None) -> Receipt:
        sale = self.db.query(Sale).filter(Sale.id == sale_id).first()

        if not sale:
            raise HTTPException(status_code=404, detail="Sale not found")

        if sale.status not in ("paid", "pending"):
            raise HTTPException(status_code=400, detail="Receipt can only be generated for finalized sales (PAID or PENDING)")

        # Build items
        items: List[ReceiptItem] = []
        subtotal = Decimal(0)

        for item in sale.items:
            receipt_item = ReceiptItem(
                product_id=item.product_id,
                name=getattr(item, "product_name", None) or None,
                quantity=item.quantity,
                unit_price=item.unit_price,
                subtotal=item.subtotal,
            )

            items.append(receipt_item)

            subtotal += Decimal(item.subtotal)

        discount = Decimal(sale.discount_total or 0)
        total = Decimal(sale.total) - discount

        # Payment summary as text (you may convert to json)
        payments = [{"method": getattr(p, "method"), "amount": str(p.amount)} for p in (sale.payments or [])]
        payment_summary = json.dumps(payments)

        receipt = Receipt(
            sale_id=sale.id,
            subtotal=subtotal,
            discount=discount,
            total=total,
            payment_summary=payment_summary,
            notes=notes,
        )

        try:
            with self.db.begin_nested():
                created = self.repo.create(receipt, items)

                # no commit here: FastAPI/session will commit after request ends
                return created

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to create receipt: {e}")

    def get(self, receipt_id: int) -> Receipt:
        receipt = self.repo.get(receipt_id)

        if not receipt:
            raise HTTPException(status_code=404, detail="Receipt not found")

        return receipt
