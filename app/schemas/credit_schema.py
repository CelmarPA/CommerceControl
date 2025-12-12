# app/schemas/credit_schema.py

from pydantic import BaseModel
from  decimal import Decimal


class CreditSaleValidation(BaseModel):
    customer_id: int
    sale_total: Decimal
    installments: int | None = None
