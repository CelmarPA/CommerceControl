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

    def create(self, payload: SaleCreate) -> Sale:
        sale = Sale(
            customer_id=payload.customer_id,
            status=SaleStatus.OPEN,
            opened_by_user=payload.opened_by_user_id,
            total=Decimal(0)
        )

        return self.repo.create(sale)

    def add_item(self, sale_id: int, payload: SaleItemIn) -> SaleItem:
        sale = self.repo.get(sale_id)

        if not sale:
            raise HTTPException(status_code=404, detail="Sale not found")

        if sale.status != SaleStatus.OPEN:
            raise HTTPException(status_code=400, detail="Sale is not open")

        product = self.product_repo.get(payload.product_id)

        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

        # Stock
        if product.stock is None:
            raise HTTPException(status_code=400, detail="Product stock not managed")

        if Decimal(product.stock) < Decimal(payload.quantity):
            raise HTTPException(status_code=400, detail="Not enough stock")

        unit_price = payload.unit_price if payload.unit_price is not None else product.sell_price
        subtotal = (Decimal(unit_price) * Decimal(payload.quantity)) - Decimal(payload.discount or 0)

        item = SaleItem(
            sale_id=sale.id,
            product_id=payload.product.id,
            quantity=payload.quantity,
            unit_price=unit_price,
            discount=payload.discount or Decimal(0),
            subtotal=subtotal,
        )

        created = self.repo.add_item(item)

        # update total sales
        sale.total = Decimal(sale.total) + subtotal
        self.repo.update(sale)

        return created

    def remove_item(self, sale_id: int, item_id: int) -> SaleItem:
        sale = self.repo.get(sale_id)

        if not sale:
            raise HTTPException(status_code=404, detail="Sale not found")

        if sale.status != SaleStatus.OPEN:
            raise HTTPException(status_code=400, detail="Sale is not open")

        item = self.db.query(SaleItem).filter(SaleItem.id == item_id, SaleItem.sale_id == sale_id).first()

        if not item:
            raise HTTPException(status_code=404, detail="Item not found")

        sale.total = Decimal(sale.total) - Decimal(item.subtotal)
        self.repo.update(sale)
        self.repo.remove_item(item)

    def apply_payment(self, sale_id: int, payload: PaymentIn, user_id: int | None = None) -> Payment:
        sale = self.repo.get(sale_id)

        if not sale:
            raise HTTPException(status_code=404, detail="Sale not found")

        if sale.status in (SaleStatus.PAID, SaleStatus.CANCELED):
            raise HTTPException(status_code=400, detail="Sale cannot receive payments")

        payment = Payment(
            sale_id=sale.id,
            methed=payload.methed,
            amount=payload.amount,
            provider_reference=payload.provider_reference
        )

        created_payment = self.repo.add_payment(payment)

        # recalculate total paid
        total_paid = sum([p.amount for p in sale.payments] or []) + Decimal(payload.amount)

        # Total includes discount
        if Decimal(total_paid) > Decimal(sale.total) - Decimal(sale.discount_total or 0):
            sale.status = SaleStatus.PAID
            sale.closed_by_user_id = user_id
            self.repo.update(sale)

        return created_payment

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

        # Apply for immediate payment if it's not a credit purchase
        if payment_mode != 'credit' and payment_mode != 'installment plan':
            # Create payment with missing total amount
            from decimal import Decimal

            total_due = Decimal(sale.total) - Decimal(sale.discount_total or 0)
            payment = Payment(sale_id=sale.id, method=payment_mode, amount=total_due)

            self.repo.add_payment(payment)

            sale.status = SaleStatus.PAID

            self.repo.update(sale)

        else:
            # INSTALLMENT PLAN: generate installments (simple, same value divided)
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

            # calculate total value
            from decimal import Decimal
            total_due = Decimal(sale.total) - Decimal(sale.discount_total or 0)

            # sum of credit used + new value
            # ideally calculate outstanding from accounts_receivable
            outstanding = (
                self.db.query(AccountReceivable)
                .filter(AccountReceivable.customer_id == customer.id, AccountReceivable.status != "paid")
                .with_entities(func.coalesce(func.sum(AccountReceivable.amount - AccountReceivable.paid_amount), 0))
                .scalar()
            ) or Decimal(0)

            limit = Decimal(customer.credit_limit or 0)

            if customer.credit_limit  is not None and (outstanding + total_due) > limit:
                raise HTTPException(status_code=400, detail="Customer credit limit exceeded")

            # generate installments
            n = installments or 1
            installments_amount = (total_due / Decimal(n)).quantize(Decimal("0.01"))

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
                self.receivable_repo.create(ar)

            sale.status = SaleStatus.PENDING
            sale.payment_mode = "credit"
            sale.installments = n
            self.repo.update(sale)

        # Reduce inventory (whenever finalized or pending)
        # For each item, create an outbound movement
        for item in sale.items:
            # decrement product.stock and create stock movement
            self.stock_repo.apply_movement_simple(product_id=item.product_id, quantity=item.quantity, movement_type="OUT", description=f"Sale {sale.id}")

        return sale

    def cancel_sale(self, sale_id: int, user_id: int | None = None) -> Sale:
        sale = self.repo.get(sale_id)

        if not sale:
            raise HTTPException(status_code=404, detail="Sale not found")

        if sale.status == SaleStatus.CANCELED:
            raise HTTPException(status_code=400, detail="Sale already canceled")

        # Replenish stock (create IN movement)
        for item in sale.items:
            self.stock_repo.apply_movement_simple(product_id=item.product_id, quantity=item.quantity, movement_type="IN", description=f"Cancel Sale {sale.id}")

        # Remove / mark accounts receivable (if any) as canceled?
        # Simple: mark AR as 'canceled'
        ars = self.db.query(AccountReceivable).filter(AccountReceivable.sale_id == sale.id).all()

        for ar in ars:
            ar.status = "canceled"
            self.receivable_repo.update(ar)

        sale.status = SaleStatus.CANCELED
        sale.closed_by_user_id = user_id
        self.repo.update(sale)

        return sale

