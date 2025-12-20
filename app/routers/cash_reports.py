# app/routers/cash_reports.py

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from datetime import date

from app.database import get_db
from app.core.permissions import admin_required
from app.schemas.cash_flow_schema import CashFlowClosingRead
from app.schemas.cash_movement_schema import CashMovementRead
from app.services.cash_flow_report_service import CashFlowReportService
from app.services.cash_movement_report_service import CashMovementReportService

router = APIRouter(prefix="/cash/reports", tags=["Cash Reports"])


@router.get("/movements/{session_id}", response_model=List[CashMovementRead], dependencies=[Depends(admin_required)])
def cash_movement_audit(session_id: int, db: Session = Depends(get_db)) -> List[CashMovementRead]:
    service = CashMovementReportService(db)

    return service.list_by_session(session_id)


@router.get("/flow/closing", response_model=CashFlowClosingRead, dependencies=[Depends(admin_required)])
def clash_flow_closing(session_id: int, start: date, end: date, db: Session = Depends(get_db)) -> CashFlowClosingRead:
    service = CashFlowReportService(db)

    return service.closing_flow(session_id, start, end)
