# app/routers/credit_policy.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict

from app.database import get_db
from app.schemas.credit_policy_schema import CreditPolicyCreate, CreditPolicyRead
from app.services.credit_policy_service import CreditPolicyService
from app.core.permissions import admin_required

router = APIRouter(prefix="/credit_policies", tags=["Credit Policies"])


@router.get("/", response_model=List[CreditPolicyRead])
def list_credit_policies(db: Session = Depends(get_db)) -> List[CreditPolicyRead]:
    service = CreditPolicyService(db)

    return service.list()


@router.get("/by-profile/{profile}", response_model=CreditPolicyRead)
def get_by_profile(profile: str, db: Session = Depends(get_db)) -> CreditPolicyRead:
    service = CreditPolicyService(db)
    policy = service.get_by_profile(profile.upper())

    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")

    return policy


@router.post("/", response_model=CreditPolicyRead, status_code=status.HTTP_201_CREATED, dependencies=[Depends(admin_required)])
def create_policy(payload: CreditPolicyCreate, db: Session = Depends(get_db)) ->CreditPolicyRead:
    service = CreditPolicyService(db)

    try:
        return service.create(payload)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{policy_id}", response_model=CreditPolicyRead, dependencies=[Depends(admin_required)])
def update_policy(policy_id: int, payload: CreditPolicyCreate, db: Session = Depends(get_db)) -> CreditPolicyRead:
    service = CreditPolicyService(db)

    try:
        return service.update(policy_id, payload)
    except ValueError as e:
        raise HTTPException(status_code=404 if "not found" in str(e).lower() else 400, detail=str(e))


@router.delete("/{policy_id}", response_model=Dict, dependencies=[Depends(admin_required)])
def delete_policy(policy_id: int, db: Session = Depends(get_db)) -> Dict:
    service = CreditPolicyService(db)

    try:
        service.delete(policy_id)

        return {"detail": "Policy deleted"}

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
