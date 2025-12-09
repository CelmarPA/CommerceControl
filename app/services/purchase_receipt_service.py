# app/services/purchase_receipt_service.py

from decimal import Decimal
from fastapi import HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.models.product import Product
from app.models.purchase_order import PurchaseOrderStatus
from app.models.purchase_order_item import PurchaseOrderItem
from app.models.purchase_receipt import PurchaseReceipt
from app.models.purchase_receipt_item import PurchaseReceiptItem

from app.repositories.purchase_order_repository import PurchaseOrderRepository
from app.repositories.stock_repository import StockRepository

from app.schemas.purchase_receipt_schema import PurchaseReceiptCreate


class PurchaseReceiptService:

    def __init__(self, db: Session):
        self.db = db
        self.order_repo = PurchaseOrderRepository(db)
        self.stock_repo = StockRepository(db)

    # ─────────────────────────────────────────────
    # CREATE RECEIPT
    # ─────────────────────────────────────────────
    def create_receipt(self, payload: PurchaseReceiptCreate) -> PurchaseReceipt:
        order = self.order_repo.get(payload.purchase_order_id)

        if not order:
            raise HTTPException(status_code=404, detail="Purchase Order not found")

        if order.status == PurchaseOrderStatus.RECEIVED:
            raise HTTPException(status_code=400, detail="Purchase Order already fully received")

        try:
            with self.db.begin_nested():
                # ======================================================
                # 1) CREATE PURCHASE RECEIPT
                # ======================================================
                receipt = PurchaseReceipt(
                    purchase_order_id=payload.purchase_order_id,
                    nfe_key=payload.nfe_key,
                    note_number=payload.note_number,
                    serie=payload.serie,
                    cfop=payload.cfop,
                    issue_date=payload.issue_date,
                    arrival_date=payload.arrival_date,
                    freight=payload.freight,
                    insurance=payload.insurance,
                    discount=payload.discount,
                    other_expenses=payload.other_expenses,
                    xml_path=payload.xml_path,
                    notes=payload.notes,
                    total_amount=Decimal("0")
                )

                self.db.add(receipt)
                self.db.flush()  # generate ID

                total_receipt = Decimal("0")

                # ======================================================
                # 2) PROCESS ITEMS
                # ======================================================
                for item_data in payload.items:

                    product = self.db.query(Product).filter(
                        Product.id == item_data.product_id
                    ).first()

                    if not product:
                        raise HTTPException(
                            status_code=400,
                            detail=f"Product ID {item_data.product_id} not found"
                        )

                    order_item = (
                        self.db.query(PurchaseOrderItem)
                        .filter(
                            PurchaseOrderItem.purchase_order_id == order.id,
                            PurchaseOrderItem.product_id == item_data.product_id
                        )
                        .first()
                    )

                    if not order_item:
                        raise HTTPException(
                            status_code=400,
                            detail=f"Product {item_data.product_id} is not in PO {order.id}"
                        )

                    new_received = Decimal(order_item.quantity_received or 0) + Decimal(item_data.quantity_received)

                    if new_received > Decimal(order_item.quantity_ordered):
                        raise HTTPException(
                            status_code=400,
                            detail=f"Receiving {item_data.quantity_received} exceeds ordered qty"
                        )

                    # Create receipt item
                    receipt_item = PurchaseReceiptItem(
                        receipt_id=receipt.id,
                        product_id=item_data.product_id,
                        quantity_received=item_data.quantity_received,
                        cost_price=item_data.cost_price
                    )
                    self.db.add(receipt_item)

                    # Update order item
                    order_item.quantity_received = new_received
                    self.db.add(order_item)

                    # Create stock movement
                    self.stock_repo.apply_movement_simple_no_commit(
                        product_id=item_data.product_id,
                        quantity=float(item_data.quantity_received),
                        movement_type="IN",
                        description=f"Purchase Receipt {receipt.id} (PO {order.id})"
                    )

                    # Add to total
                    total_receipt += (Decimal(item_data.quantity_received) * Decimal(item_data.cost_price))

                # ======================================================
                # 3) UPDATE TOTAL RECEIPT
                # ======================================================
                receipt.total_amount = total_receipt
                self.db.add(receipt)

                # ======================================================
                # 4) UPDATE ORDER STATUS
                # ======================================================
                all_received = all(
                    (Decimal(i.quantity_received or 0) >= Decimal(i.quantity_ordered))
                    for i in order.items
                )

                order.status = PurchaseOrderStatus.RECEIVED if all_received else PurchaseOrderStatus.PARTIAL
                self.db.add(order)

                # end of with => automatic commit
                self.db.refresh(receipt)

                return receipt

        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    # ─────────────────────────────────────────────
    # LIST receipts for order
    # ─────────────────────────────────────────────
    def list_for_order(self, order_id: int) -> List[PurchaseReceipt]:
        order = self.order_repo.get(order_id)

        if not order:
            raise HTTPException(status_code=404, detail="Purchase order not found")

        return order.receipts
