# app/routers/dashboard.py

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.permissions import admin_required
from app.schemas.dashboard_schema import DashboardRead
from app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/", response_model=DashboardRead, dependencies=[Depends(admin_required)])
def get_dashboard(db: Session = Depends(get_db)) -> DashboardRead:
    service = DashboardService(db)

    return service.get_dashboard()
