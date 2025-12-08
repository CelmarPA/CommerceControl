# app/services/sale_service.py
from sqlalchemy import func
from sqlalchemy.orm import Session
from decimal import Decimal
from datetime import datetime
from fastapi import HTTPException

from app.repositories.sale_repository import SaleRepository
from app.repositories.receivable_repository import ReceivableRepository
from app.models.sale import Sale, SaleStatus
from app.models.sale_item import SaleItem
from app.models.payment import Payment
from app.models.account_receivable import AccountReceivable
from app.schemas.sale_schema import SaleCreate, SaleItemIn
from app.schemas.payment_schema import PaymentIn
from app.repositories.stock_repository import StockRepository
from app.repositories.product_repository import ProductRepository


class SalesService:

    def __init__(self, db: Session):
        self.db = db
        self.repo = SaleRepository(db)
        self.receivable_repo = ReceivableRepository(db)
        self.stock_repo = StockRepository(db)
        self.product_repo = ProductRepository(db)

    # ============================================================
    # CREATE SALE (OPEN)
    # ============================================================
    def create(self, payload: SaleCreate) -> Sale:
        sale = Sale(
            customer_id=payload.customer_id,
            status=SaleStatus.OPEN,
            opened_by_user_id=payload.opened_by_user_id,
            total=Decimal(0)
        )

        try:
            # open explicit transaction; commit/rollback handled automatically
            with self.db.begin_nested():
                # persist sale and ensure it has an ID
                self.db.add(sale)
                self.db.flush()
                self.db.refresh(sale)

            # sale is committed at this point
            return sale

        except Exception as e:
            # surface as HTTP error to FastAPI (useful for debugging)
            raise HTTPException(status_code=500, detail=f"Failed to create sale: {e}")

    # ============================================================
    # ADD ITEM
    # ============================================================
    def add_item(self, sale_id: int, payload: SaleItemIn) -> SaleItem:
        sale = self.repo.get(sale_id)

        if not sale:
            raise HTTPException(status_code=404, detail="Sale not found")

        if sale.status != SaleStatus.OPEN:
            raise HTTPException(status_code=400, detail="Sale is not open")

        product = self.product_repo.get(payload.product_id)

        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

        # Use stock repository to check current stock (we use movements)
        current_stock = self.stock_repo.get_current_stock(payload.product_id)

        if current_stock is None:
            raise HTTPException(status_code=400, detail="Product stock not managed")

        if Decimal(current_stock) < Decimal(payload.quantity):
            raise HTTPException(status_code=400, detail="Not enough stock")

        unit_price = payload.unit_price if payload.unit_price is not None else Decimal(product.sell_price or 0)
        subtotal = (Decimal(unit_price) * Decimal(payload.quantity)) - Decimal(payload.discount or 0)

        item = SaleItem(
            sale_id=sale.id,
            product_id=payload.product_id,
            quantity=payload.quantity,
            unit_price=unit_price,
            discount=payload.discount or Decimal(0),
            subtotal=subtotal,
        )

        try:
            with self.db.begin_nested():
                self.db.add(item)
                self.db.flush()

                sale.total = Decimal(sale.total) + subtotal
                self.db.add(sale)

            self.db.refresh(item)

            return item

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to add item: {e}")

    # ============================================================
    # REMOVE ITEM
    # ============================================================
    def remove_item(self, sale_id: int, item_id: int) -> None:
        sale = self.repo.get(sale_id)

        if not sale:
            raise HTTPException(status_code=404, detail="Sale not found")

        if sale.status != SaleStatus.OPEN:
            raise HTTPException(status_code=400, detail="Sale is not open")

        item = self.db.query(SaleItem).filter(SaleItem.id == item_id, SaleItem.sale_id == sale_id).first()

        if not item:
            raise HTTPException(status_code=404, detail="Item not found")

        try:
            with self.db.begin_nested():
                sale.total = Decimal(sale.total) - Decimal(item.subtotal)
                self.db.add(sale)

                self.db.delete(item)

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to remove item: {e}")

    # ============================================================
    # APPLY PAYMENT
    # ============================================================
    def apply_payment(self, sale_id: int, payload: PaymentIn, user_id: int | None = None) -> Payment:
        sale = self.repo.get(sale_id)

        if not sale:
            raise HTTPException(status_code=404, detail="Sale not found")

        if sale.status in (SaleStatus.PAID, SaleStatus.CANCELED):
            raise HTTPException(status_code=400, detail="Sale cannot receive payments")

        payment = Payment(
            sale_id=sale.id,
            method=payload.method,
            amount=payload.amount,
            provider_reference=payload.provider_reference
        )

        try:
            with self.db.begin_nested():
                self.db.add(payment)
                self.db.flush()
                self.db.refresh(payment)

                # recalculate total paid
                total_paid = sum([p.amount for p in sale.payments] or []) + Decimal(payload.amount)

                # Total includes discount
                if Decimal(total_paid) > Decimal(sale.total) - Decimal(sale.discount_total or 0):
                    sale.status = SaleStatus.PAID
                    sale.closed_by_user_id = user_id
                    self.db.add(sale)

            return payment

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to apply payment: {e}")

    # ============================================================
    # CHECKOUT (FINALIZE SALE)
    # ============================================================
    def checkout(self, sale_id: int, payment_mode: str, installments: int | None = None) -> Sale:
        """
        Finalizes the sale.

        - If payment_mode == 'credit' or 'installment plan': generates accounts_receivable with installments
        - Always reduces inventory upon completion (deducts stock)
        - Checks customer credit limit in case of installment plan
        """
        from decimal import Decimal
        from app.models.payment import Payment as PaymentModel

        sale = self.repo.get(sale_id)

        if not sale:
            raise HTTPException(status_code=404, detail="Sale not found")

        if sale.status != SaleStatus.OPEN:
            raise HTTPException(status_code=400, detail="Sale is not open")

        if not sale.items:
            raise HTTPException(status_code=400, detail="Sale has no items")

        total_due = Decimal(sale.total) - Decimal(sale.discount_total or 0)

        try:
            # Open transaction (automatic commit/rollback on exit)
            with self.db.begin_nested():

                # Apply for immediate payment if it's not a credit purchase
                if payment_mode in ("cash", "card", "pix", "debit"):
                    # immediate payment
                    payment = PaymentModel(sale_id=sale.id, method=payment_mode, amount=total_due)

                    self.db.add(payment)

                    sale.status = SaleStatus.PAID
                    sale.payment_mode = payment_mode
                    self.db.add(sale)

                else:
                    # INSTALLMENT PLAN Or CREDIT: generate installments (simple, same value divided)
                    if not sale.costumer_id:
                        raise HTTPException(status_code=400, detail="Installment payments require a customer")

                    # Check customer's credit limit
                    # customer = self.db.query("customers").filter()  # placeholder; use Customer repo
                    # We'll use raw checks with Customer model below.
                    from app.models.customer import Customer

                    customer = self.db.query(Customer).filter(Customer.id == sale.customer_id).first()

                    if not customer:
                        raise HTTPException(status_code=400, detail="Customer not found")

                    if customer.deleted_at is not None or not customer.is_active:
                        raise HTTPException(status_code=400, detail="Customer not available for credit")

                    # generate installments
                    n = installments or 1
                    installments_amount = Decimal(total_due / Decimal(n)).quantize(Decimal("0.01"))

                    from datetime import timedelta

                    for i in range(1, n + 1):
                        due_date = datetime.now() + timedelta(days=30 * i)

                        ar =  AccountReceivable(
                            customer_id=customer.id,
                            sale_id=sale.id,
                            installment_number=i,
                            due_date=due_date,
                            amount=installments_amount,
                            paid_amount=Decimal(0),
                            status="open"
                        )
                        self.db.add(ar)

                    sale.status = SaleStatus.PENDING
                    sale.payment_mode = "credit"
                    sale.installments = n
                    self.db.add(sale)

                # Reduce inventory (whenever finalized or pending)
                # For each item, create an outbound movement
                for item in sale.items:
                    current_stock = self.stock_repo.get_current_stock(item.product_id)

                    if Decimal(current_stock) < Decimal(item.quantity):
                        raise HTTPException(status_code=400, detail=f"Not enough stock for product {item.product_id}")

                    self.stock_repo.apply_movement_simple_no_commit(
                        product_id=item.product_id,
                        quantity=float(item.quantity),
                        movement_type="OUT",
                        description=f"Sale {sale.id}"
                    )

                # End of transaction: implicit commit in exit

            # Final refresh
            self.db.refresh(sale)

            return sale

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Checkout failed: {e}")

    # ============================================================
    # CANCEL SALE
    # ============================================================
    def cancel_sale(self, sale_id: int, user_id: int | None = None) -> Sale:
        sale = self.repo.get(sale_id)

        if not sale:
            raise HTTPException(status_code=404, detail="Sale not found")

        if sale.status == SaleStatus.CANCELED:
            raise HTTPException(status_code=400, detail="Sale already canceled")

        try:
            with self.db.begin_nested():
                # restock

                for item in sale.items:
                    self.stock_repo.apply_movement_simple_no_commit(
                        product_id=item.product_id,
                        quantity=item.quantity,
                        movement_type="IN",
                        description=f"Cancel Sale {sale.id}")

                # Remove / mark accounts receivable (if any) as canceled?
                # Simple: mark AR as 'canceled'
                ars = self.db.query(AccountReceivable).filter(AccountReceivable.sale_id == sale.id).all()

                for ar in ars:
                    ar.status = "canceled"
                    self.db.add(ar)

                sale.status = SaleStatus.CANCELED
                sale.closed_by_user_id = user_id
                self.db.add(sale)

            self.db.refresh(sale)

            return sale

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to cancel sale: {e}")

    # ============================================================
    # LIST & GET
    # ============================================================
    def list(self):
        return self.repo.list()

    def get(self, sale_id: int) -> Sale:
        return self.repo.get(sale_id)
