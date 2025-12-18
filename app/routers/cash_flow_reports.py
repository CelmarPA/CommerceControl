# app/routers/cash_flow_reports.py

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from datetime import date
from typing import List

from app.database import get_db
from app.services.cash_flow_report_service import CashFlowReportService
from app.schemas.cash_flow_report_schema import (
    CashFlowDailyRead,
    CashFlowMonthlyRead,
    CashFlowByCategoryRead,
    CashFlowSummaryRead
)
from app.core.permissions import admin_required

router = APIRouter(prefix="/reports/cash-flow", tags=["Reports / Cash Flow"])


# =====================================================
# SUMMARY FLOW
# =====================================================
@router.get("/cash-flow/summary", response_model=CashFlowSummaryRead, dependencies=[Depends(admin_required)])
def cash_flow_summary(start: date, end: date, db: Session = Depends(get_db)) -> CashFlowSummaryRead:
    service = CashFlowReportService(db)

    return service.summary_by_period(start, end)


# =====================================================
# DAILY FLOW
# =====================================================
@router.get("/daily", response_model=List[CashFlowDailyRead], dependencies=[Depends(admin_required)])
def daily_cash_flow_report(
        start: date = Query(..., description="Start date (YYYY-MM-DD"),
        end: date = Query(..., description="End date (YYYY-MM-DD)"),
        db: Session = Depends(get_db)
) -> List[CashFlowDailyRead]:
    """
    Daily cash flow report with running balance
    """

    service = CashFlowReportService(db)

    return service.daily_flow(start, end)


# =====================================================
# MONTHLY FLOW
# =====================================================
@router.get("/monthly", response_model=List[CashFlowMonthlyRead], dependencies=[Depends(admin_required)])
def monthly_cash_flow_report(
        year: int = Query(..., description="Year (YYYY"),
        db: Session = Depends(get_db)
) -> List[CashFlowMonthlyRead]:
    service = CashFlowReportService(db)

    return service.monthly_flow(year)


# =====================================================
# CATEGORY FLOW
# =====================================================
@router.get("/category", response_model=List[CashFlowByCategoryRead], dependencies=[Depends(admin_required)])
def cash_flow_by_category(db: Session = Depends(get_db)) -> List[CashFlowByCategoryRead]:
    service = CashFlowReportService(db)

    return service.by_category()
