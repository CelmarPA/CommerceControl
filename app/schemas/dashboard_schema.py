# app/schemas/dashboard_schema.py

from pydantic import BaseModel


class DashboardRead(BaseModel):
    cash: dict
    sales: dict
    credit: dict
