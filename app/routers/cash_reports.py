# app/routers/cash_reports.py

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.core.permissions import admin_required
from app.schemas.cash_movement_schema import CashMovementRead
from app.services.cash_movement_report_service import CashMovementReportService

router = APIRouter(prefix="/cash/reports", tags=["Cash Reports"])


@router.get("/movements/{session_id}", response_model=List[CashMovementRead], dependencies=[Depends(admin_required)])
def cash_movement_audit(session_id: int, db: Session = Depends(get_db)) -> List[CashMovementRead]:
    service = CashMovementReportService(db)

    return service.list_by_session(session_id)
