# app/routers/credit.py
from datetime import datetime
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, List

from app.database import get_db
from app.core.permissions import admin_required
from app.schemas.credit_history_schema import CreditHistoryRead
from app.schemas.risk_report_schema import RiskReport
from app.services.credit_engine import CreditEngine
from app.schemas.credit_schema import CreditSaleValidation
from app.schemas.credit_analytics_schema import CreditAnalytics
from app.services.credit_history_service import CreditHistoryService
from app.models.customer import Customer


router = APIRouter(prefix="/credit", tags=["Credit"])


# ===========================
# Helpers
# ===========================
def get_credit_engine(db: Session) -> CreditEngine:
    return CreditEngine(db)


# ============================================================
# GET FULL CREDIT STATUS
# ============================================================
@router.get("/check/{customer_id}", response_model=Dict, dependencies=[Depends(admin_required)])
def check_credit(customer_id: int,  db: Session = Depends(get_db)) -> Dict:
    credit_engine = get_credit_engine(db)

    try:
        return credit_engine.check_customer_status(customer_id)

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================
# VALIDATE SALE (CREDIT CHECK)
# ============================================================
@router.post("/validate-sale", response_model=Dict, dependencies=[Depends(admin_required)])
def validate_sale(payload: CreditSaleValidation, db: Session = Depends(get_db)) -> Dict:
    credit_engine = get_credit_engine(db)

    try:
        credit_engine.validate_sale(
            customer_id=payload.customer_id,
            sale_total=payload.sale_total,
            installments=payload.installments
        )

        return {"detail": "Sale approved for credit"}

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================
# GET SCORE
# ============================================================
@router.get("/score/{customer_id}", response_model=Dict, dependencies=[Depends(admin_required)])
def get_score(customer_id: int, db: Session = Depends(get_db)) -> Dict:
    credit_engine = get_credit_engine(db)

    return credit_engine.get_score(customer_id)


# ============================================================
# GET LIMIT INFO
# ============================================================
@router.get("/limit/{customer_id}", response_model=Dict, dependencies=[Depends(admin_required)])
def get_credit_limit(customer_id: int, db: Session = Depends(get_db)) -> Dict:
    credit_engine = get_credit_engine(db)

    return credit_engine.get_limit(customer_id)


# ============================================================
# RECALCULATE SCORE (PROFESSIONAL ENGINE)
# ============================================================
@router.post("/recalculate-score/{customer_id}", response_model=Dict, dependencies=[Depends(admin_required)])
def recalc_score(customer_id: int, db: Session = Depends(get_db)) -> Dict:
    credit_engine = get_credit_engine(db)

    try:
        score = credit_engine.recalculate_score(customer_id)
        profile = credit_engine.assign_profile(score)

        # Save customer
        customer = db.query(Customer).filter(Customer.id == customer_id).first()

        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")

        customer.credit_score = score
        customer.credit_profile = profile
        db.commit()

        return {
            "customer_id": customer.id,
            "new_score": score,
            "new_profile": profile
        }

    except Exception as e:
        db.rollback()

        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# FORCE RECLASSIFY PROFILE (ADMIN TOOL)
# ============================================================
@router.post("/apply-profile/{customer_id}/{profile}", response_model=Dict, dependencies=[Depends(admin_required)])
def apply_profile(customer_id: int, profile: str, db: Session = Depends(get_db)) -> Dict:
    profile = profile.upper()

    # -------------------------------
    # 1) Validate profile
    # -------------------------------
    valid_profiles = ["BRONZE", "SILVER", "GOLD", "DIAMOND"]

    if profile not in valid_profiles:
        raise HTTPException(status_code=400, detail=f"Invalid profile: {profile}. Must be one of {valid_profiles}")

    # -------------------------------
    # 2) Fetch customer
    # -------------------------------
    customer = db.query(Customer).filter(Customer.id == customer_id).first()

    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    old_profile = customer.credit_profile or "NONE"

    # -------------------------------
    # 3) Update profile
    # -------------------------------
    customer.credit_profile = profile
    db.add(customer)

    # -------------------------------
    # 4) Register history entry
    # -------------------------------
    from app.services.credit_history_service import CreditHistoryService

    history = CreditHistoryService(db)
    history.record(
        customer_id=customer.id,
        event_type="profile_change",
        amount=0,
        balance_after=customer.credit_used or 0,
        notes=f"Profile changed from {old_profile} to {profile}"
    )

    db.commit()

    return {
        "detail": f"Profile updated from {old_profile} to {profile}",
        "customer_id": customer_id,
        "old_profile": old_profile,
        "new_profile": profile
    }


# ============================================================
# RECALCULATE ALL CUSTOMERS SCORE AND PROFILES
# ============================================================
@router.post("/recalculate-all", response_model=Dict, dependencies=[Depends(admin_required)])
def recalc_all_customers(db: Session = Depends(get_db)) -> Dict:
    credit_engine = CreditEngine(db)

    return credit_engine.recalc_all_customers()


# ============================================================
# SIMULATE SALE
# ============================================================
@router.post("/simulate-sale", response_model=Dict, dependencies=[Depends(admin_required)])
def simulate_sale(payload: CreditSaleValidation, db: Session = Depends(get_db)) -> Dict:
    credit_engine = get_credit_engine(db)

    try:
        credit_engine.validate_sale(
            customer_id=payload.customer_id,
            sale_total=payload.sale_total,
            installments=payload.installments,
        )

        return {
            "approved": True,
            "detail": "Sale approved in simulation"
        }

    except HTTPException as e:
        return {
            "approved": False,
            "detail": e.detail
        }


# ============================================================
# RISK REPORT
# ============================================================
@router.get("/risk-report", response_model=RiskReport, dependencies=[Depends(admin_required)])
def risk_report(db: Session = Depends(get_db)) -> RiskReport:
    credit_engine = get_credit_engine(db)

    return credit_engine.risk_report()


# ============================================================
# CUSTOMER HISTORY
# ============================================================
@router.get("/history/{customer_id}", response_model=List[CreditHistoryRead], dependencies=[Depends(admin_required)])
def get_credit_history(
        customer_id: int,
        event_type: str | None = None,
        start: datetime | None = None,
        end: datetime | None = None,
        db: Session = Depends(get_db)
) -> List[CreditHistoryRead]:
    history_service = CreditHistoryService(db)

    return history_service.get_history(
        customer_id=customer_id,
        event_type=event_type,
        start=start,
        end=end
    )


# ============================================================
# CUSTOMER HISTORY
# ============================================================
@router.post("/custom-limit/{customer_id}", response_model=Dict, dependencies=[Depends(admin_required)])
def set_custom_limit(customer_id: int, data: Dict, db: Session = Depends(get_db)) -> Dict:
    from app.models.customer import Customer
    from app.services.credit_history_service import CreditHistoryService

    if "new_limit" not in data:
        raise HTTPException(status_code=400, detail="Missing field: new_limit")

    new_limit = Decimal(data["new_limit"])

    customer = db.query(Customer).filter(Customer.id == customer_id).first()

    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    old_limit = Decimal(customer.credit_limit or 0)
    customer.credit_limit = new_limit

    db.add(customer)
    db.commit()

    # History
    history = CreditHistoryService(db)
    history.record(
        customer_id=customer.id,
        event_type="limit_change",
        amount=new_limit,
        balance_after=customer.credit_used or 0,
        notes=f"Limit changed {old_limit} → {new_limit}"
    )

    return {
        "detail": "Limit updated",
        "customer_id": customer.id,
        "old_limit": old_limit,
        "new_limit": new_limit
    }


# ============================================================
# ANALYTICS
# ============================================================
@router.get("/analytics/{customer_id}", response_model=CreditAnalytics, dependencies=[Depends(admin_required)])
def analytics(customer_id: int, db: Session = Depends(get_db)) -> CreditAnalytics:
    credit_engine = get_credit_engine(db)

    return credit_engine.analytics(customer_id)
