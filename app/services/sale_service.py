# app/services/sale_service.py

from sqlalchemy.orm import Session
from decimal import Decimal
from fastapi import HTTPException

from app.repositories.sale_repository import SaleRepository
from app.repositories.receivable_repository import ReceivableRepository
from app.repositories.stock_repository import StockRepository
from app.repositories.product_repository import ProductRepository

from app.models.sale import Sale, SaleStatus
from app.models.sale_item import SaleItem
from app.models.payment import Payment
from app.models.account_receivable import AccountReceivable

from app.schemas.sale_schema import SaleCreate, SaleItemIn
from app.schemas.payment_schema import PaymentIn

from app.services.credit_engine import CreditEngine


class SalesService:

    def __init__(self, db: Session):
        self.db = db
        self.repo = SaleRepository(db)
        self.receivable_repo = ReceivableRepository(db)
        self.stock_repo = StockRepository(db)
        self.product_repo = ProductRepository(db)
        self.engine = CreditEngine(db)

    # ============================================================
    # CREATE SALE
    # ============================================================
    def create(self, payload: SaleCreate) -> Sale:
        """
        Create a sale inside an explicit transaction so the object is persisted
        even if repo.create() uses flush() instead of commit().
        """
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

            return sale

        except Exception as e:
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

        current_stock = self.stock_repo.get_current_stock(payload.product_id)

        if Decimal(current_stock) < Decimal(payload.quantity):
            raise HTTPException(status_code=400, detail="Not enough stock")

        unit_price = payload.unit_price if payload.unit_price else Decimal(product.sell_price)
        subtotal = (unit_price * payload.quantity) - Decimal(payload.discount or 0)

        item = SaleItem(
            sale_id=sale.id,
            product_id=payload.product_id,
            quantity=payload.quantity,
            unit_price=unit_price,
            discount=payload.discount or Decimal(0),
            subtotal=subtotal,
        )

        try:
            with self.db.begin_nested():  # SAFE SAVEPOINT
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
            amount=Decimal(payload.amount),
            provider_reference=payload.provider_reference
        )

        try:
            with self.db.begin_nested():
                self.db.add(payment)
                self.db.flush()
                self.db.refresh(payment)

                total_paid = sum([p.amount for p in sale.payments] or []) + payload.amount

                if total_paid >= Decimal(sale.total - (sale.discount_total or 0)):
                    sale.status = SaleStatus.PAID
                    sale.closed_by_user_id = user_id
                    self.db.add(sale)

            return payment

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to apply payment: {e}")

    # ============================================================
    # CHECKOUT (FINALIZE SALE)
    # ============================================================
    def checkout(self, sale_id: int, payment_mode: str, installments: int | None = None, customer_credit_limit_check: bool = True) -> Sale:
        """
        Finalizes the sale.

        - If payment_mode == 'credit' or 'installment plan': generates accounts_receivable with installments
        - Always reduces inventory upon completion (deducts stock)
        - Checks customer credit limit in case of installment plan
        """
        sale = self.repo.get(sale_id)

        if not sale:
            raise HTTPException(status_code=404, detail="Sale not found")

        if sale.status != SaleStatus.OPEN:
            raise HTTPException(status_code=400, detail="Sale is not open")

        if not sale.items:
            raise HTTPException(status_code=400, detail="Sale has no items")

        total_due = (Decimal(sale.total) - Decimal(sale.discount_total or 0)).quantize(Decimal("0.01"))

        try:
            with self.db.begin_nested():  # SAFE SAVEPOINT

                # ======================================================
                # 1) SPOT PAYMENT — CASH / PIX / CARD / DEBIT
                # ======================================================
                if payment_mode in ("cash", "card", "pix", "debit"):
                    payment = Payment(
                        sale_id=sale.id,
                        method=payment_mode,
                        amount=total_due,
                    )
                    self.db.add(payment)

                    sale.status = SaleStatus.PAID
                    sale.payment_mode = payment_mode
                    self.db.add(sale)

                # ======================================================
                # 2) CREDIT / INSTALLMENTS
                # ======================================================-
                else:
                    if not sale.customer_id:
                        raise HTTPException(status_code=400, detail="Installments require a customer")

                    # Validate credit rules
                    if customer_credit_limit_check:
                        engine = CreditEngine(self.db)

                        engine.validate_sale(
                            customer_id=sale.customer_id,
                            sale_total=total_due,
                            installments=installments
                        )

                    from app.models.customer import Customer

                    customer = self.db.query(Customer).filter(Customer.id == sale.customer_id).first()

                    if not customer:
                        raise HTTPException(status_code=400, detail="Customer not found")

                    # --------------------------
                    # Create Installments (AR)
                    # --------------------------
                    n = installments or 1
                    installment_amount = Decimal(total_due / n).quantize(Decimal("0.01"))

                    from datetime import timedelta, datetime as dt

                    for i in range(1, n + 1):
                        due_date = dt.now() + timedelta(days=30 * i)
                        ar = AccountReceivable(
                            customer_id=customer.id,
                            sale_id=sale.id,
                            installment_number=i,
                            due_date=due_date,
                            amount=installment_amount,
                            paid_amount=Decimal(0),
                            status=SaleStatus.OPEN
                        )
                        self.db.add(ar)

                    self.engine.recalc_and_apply(customer.id)

                    # --------------------------
                    # Update Sale status
                    # --------------------------
                    sale.status = SaleStatus.PENDING
                    sale.payment_mode = "credit"
                    sale.installments = n
                    self.db.add(sale)

                    # --------------------------
                    # Update Customer Credit Used
                    # --------------------------
                    customer.credit_used = Decimal(customer.credit_used or 0) + total_due
                    self.db.add(customer)

                    # --------------------------
                    # Register Credit History
                    # --------------------------
                    from app.services.credit_history_service import CreditHistoryService

                    history = CreditHistoryService(self.db)
                    history.record(
                        customer_id=customer.id,
                        event_type="sale",
                        amount=total_due,
                        balance_after=customer.credit_used,
                        notes=f"Sale #{sale.id} - {n} installments"
                    )

                    # --------------------------
                    # OPTIONAL: Recalculate Score
                    # --------------------------
                    engine = CreditEngine(self.db)

                    new_score = engine.recalculate_score(customer.id)
                    new_profile= engine.assign_profile(new_score)

                    customer.credit_score = new_score
                    customer.credit_profile = new_profile

                    self.db.add(customer)

                # ======================================================
                # 3) STOCK MOVEMENT (OUT)
                # ======================================================
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

            # END WITH — SAVEPOINT COMMITTED
            self.db.commit()
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
            with self.db.begin_nested():  # SAFE SAVEPOINT

                # STOCK RETURN
                for item in sale.items:
                    self.stock_repo.apply_movement_simple_no_commit(
                        product_id=item.product_id,
                        quantity=float(item.quantity),
                        movement_type="IN",
                        description=f"Cancel Sale {sale.id}"
                    )

                # CANCEL RECEIVABLES
                ars = self.db.query(AccountReceivable).filter(AccountReceivable.sale_id == sale.id).all()

                for ar in ars:
                    ar.status = "canceled"
                    self.db.add(ar)

                # 3. Update SALE
                sale.status = SaleStatus.CANCELED
                sale.closed_by_user_id = user_id
                self.db.add(sale)

            # END WITH — SAVEPOINT SUCCESS
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
