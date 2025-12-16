# app/services/credit_events.py

from sqlalchemy.orm import Session

from app.services.credit_engine import CreditEngine


class CreditEvents:

    def __init__(self, db: Session) -> None:
        self.db = db
        self.engine = CreditEngine(db)

    def on_payment(self, customer_id: int) -> dict:
        self.engine.recalc_and_apply(customer_id)

    def on_sale(self, customer_id: int) -> dict:
        self.engine.recalc_and_apply(customer_id)

    def on_cancel(self, customer_id: int) -> dict:
        self.engine.recalc_and_apply(customer_id)

    def on_overdue(self, customer_id: int) -> dict:
        self.engine.recalc_and_apply(customer_id)