# app/routers/credit.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict

from app.database import get_db
from app.core.permissions import admin_required
from app.services.credit_engine import CreditEngine

router = APIRouter(prefix="/credit", tags=["Credit"])


@router.get("/check/{customer_id}", response_model=Dict, dependencies=[Depends(admin_required)])
def check_credit(customer_id: int,  db: Session = Depends(get_db)) -> Dict:
    engine = CreditEngine(db)

    try:
        result = engine.check_customer_status(customer_id)

        return result

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/validate-scale", response_model=Dict, dependencies=[Depends(admin_required)])
def validate_scale(data: Dict, db: Session = Depends(get_db)) -> Dict:
    """
    Expected JSON:
    {
        "customer_id": 1,
        "sale_total": 500.00,
        "installments": 3
    }
    """

    required = ["customer_id", "sale_total"]

    for field in required:
        if field not in data:
            raise HTTPException(status_code=400, detail=f"Missing field: {field}")

    engine = CreditEngine(db)

    engine.validate_sale(
        customer_id=data["customer_id"],
        sale_total=data["sale_total"],
        installments=data.get("installments", None)
    )

    return {"detail": "Sale approved for credit"}


@router.get("/score/{customer_id}", response_model=Dict, dependencies=[Depends(admin_required)])
def get_score(customer_id: int, db: Session = Depends(get_db)) -> Dict:
    engine = CreditEngine(db)

    return engine.get_score(customer_id)


@router.get("/limit/{customer_id}", response_model=Dict, dependencies=[Depends(admin_required)])
def get_credit_limit(customer_id: int, db: Session = Depends(get_db)) -> Dict:
    engine = CreditEngine(db)

    return engine.get_limit(customer_id)
