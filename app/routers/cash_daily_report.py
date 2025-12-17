# app/routers/dashboard_service.py

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import date


from app.database import get_db
from app.core.permissions import admin_required
from app.schemas.cash_daily_report_schema import CashDailyReportRead
from app.services.cash_daily_report_service import CashDailyReportService


router = APIRouter(prefix="/cash/reports", tags=["Cash Daily Report"])


@router.get("/daily/{day}", response_model=CashDailyReportRead, dependencies=[Depends(admin_required)])
def daily_cash_report(day: date, db: Session = Depends(get_db)) -> CashDailyReportRead:
    service = CashDailyReportService(db)

    return service.daily_report(day)

