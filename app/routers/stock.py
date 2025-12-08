# app/routers/stock.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Callable

from app.database import get_db
from app.schemas.stock_schema import StockMovementCreate, StockMovementRead, StockCurrentRead
from app.services.stock_service import StockService
from app.core.permissions import admin_required

router = APIRouter(prefix="/stock", tags=["Stock"])


@router.post("/", response_model=StockMovementRead, dependencies=[Depends(admin_required)])
def apply_stock_movement(payload: StockMovementCreate, db: Session = Depends(get_db)) -> Callable:
    service = StockService(db)

    try:
        return service.apply_movement(payload)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=List[StockMovementRead])
def list_stock_movement(product_id: int | None = None, db: Session = Depends(get_db)) -> List[StockMovementRead]:
    service = StockService(db)

    return service.list(product_id)


@router.get("/{product_id}/current", response_model=StockCurrentRead)
def get_current_stock(product_id: int, db: Session = Depends(get_db)) -> StockCurrentRead:
    service = StockService(db)

    return service.get_stock(product_id)
