# app/services/credit_engine.py

from decimal import Decimal
from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session
from datetime import datetime, timezone, timedelta

from app.models.credit_alert import CreditAlert
from app.models.customer import Customer
from app.models.credit_policy import CreditPolicy
from app.models.account_receivable import AccountReceivable
from app.models.credit_history import CreditHistory
from app.services.credit_policy_service import CreditPolicyService



class CreditEngine:

    def __init__(self, db: Session):
        self.db = db

    # ============================================================
    # LOAD POLICY
    # ============================================================
    def load_policy_for_customer(self, customer: Customer) -> CreditPolicy:
        service = CreditPolicyService(self.db)
        profile = (customer.credit_profile or "BRONZE").upper()

        policy = service.get_by_profile(profile)

        if not policy:
            policy = service.get_by_profile("BRONZE")

        return policy

    # ============================================================
    # OUTSTANDING (used + overdue + partial)
    # ============================================================
    def outstanding_amount(self, customer_id: int) -> Decimal:
        # sum of open ARs (status != 'paid' and != 'cancelled'
        val = (
            self.db.query(
                func.coalesce(
                    func.sum(AccountReceivable.amount - AccountReceivable.paid_amount),
                    0
                )
            )
            .filter(
                AccountReceivable.customer_id == customer_id,
                AccountReceivable.status.notin_(["paid", "canceled"])
            )
            .scalar()
        )

        return Decimal(val or 0)

    # ============================================================
    # OVERDUE INFO
    # ============================================================
    def overdue_info(self, customer_id: int) -> dict:
        # retorn (count_overdue, max_days_overdue)
        from datetime import datetime, timezone

        ars = (
            self.db.query(AccountReceivable)
            .filter(AccountReceivable.customer_id == customer_id)
            .all()
        )

        count_overdue = 0
        max_days = 0

        for ar in ars:
            if ar.due_date and ar.status == "overdue":
                delta = (datetime.now(timezone.utc) - ar.due_date).days
                max_days = max(max_days, delta)
                count_overdue += 1

        return {
            "count_overdue": count_overdue,
            "max_days_overdue": max_days
        }

    # ============================================================
    # VALIDATE SALE — FULL RISK ENGINE
    # ============================================================
    def validate_sale(self, customer_id: int, sale_total: Decimal, installments: int | None = None) -> bool:
        """
        Raises HTTPException on validation failure.
        """

        customer = self.db.query(Customer).filter(Customer.id == customer_id).first()

        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")

        if self.is_credit_blocked(customer.id):
            raise HTTPException(status_code=400, detail="Customer credit temporarily blocked")

        policy = self.load_policy_for_customer(customer)

        if not policy.allow_credit:
            raise HTTPException(status_code=400, detail="Customer is not allowed to use credit")

        # 1) Max installments
        n = installments or 1

        if policy.max_installments and n > policy.max_installments:
            raise HTTPException(status_code=400, detail=f"Max installments allowed: {policy.max_installments}")

        # 2) Max sale amount per policy
        if policy.max_sale_amount is not None and Decimal(sale_total) > Decimal(policy.max_sale_amount):
            raise HTTPException(status_code=400, detail=f"Sale exceeds max allowed for profile {policy.profile}")

        # 3) Check credit limit usage
        outstanding = self.outstanding_amount(customer_id)
        limit = Decimal(customer.credit_limit or 0)

        # calculate allowed percent of limit
        effective_limit = limit * (policy.max_percentage_of_limit / 100)

        if (outstanding + Decimal(sale_total)) > effective_limit:
            raise HTTPException(status_code=400, detail="Customer credit limit exceeded")

        # 4) Overdue checks
        overdue = self.overdue_info(customer_id)

        if overdue["count_overdue"] > 0 and overdue["max_days_overdue"] > policy.max_delay_days:
            raise HTTPException(status_code=400, detail="Customer has overdue invoices exceeding allowed days")

        # 5) Additional custom checks (score)
        if customer.credit_score is not None and customer.credit_score < 300:
                raise HTTPException(status_code=400, detail="Customer credit score too low")

        # Passed all checks
        return True

    # ============================================================
    # REFRESH OVERDUE FOR ONE CUSTOMER
    # ============================================================
    def refresh_overdue(self, customer_id: int) -> None:
        now = datetime.now(timezone.utc)

        ars = self.db.query(AccountReceivable).filter(
            AccountReceivable.customer_id == customer_id,
            AccountReceivable.status == "open"
        ).all()

        changed = False

        for ar in ars:
            if ar.due_date and ar.due_date < now:
                ar.status = "overdue"
                self.db.add(ar)
                changed = True

        if changed:
            self.db.commit()
            self.recalc_and_apply(customer_id)

    # ============================================================
    # SCORE RE-CALCULATION (PROFESSIONAL MODEL)
    # ============================================================
    def recalculate_score(self, customer_id: int) -> int:
        """
        Score range: 0 - 1000
        """

        customer = self.db.query(Customer).filter(Customer.id == customer_id).first()

        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")

        outstanding = self.outstanding_amount(customer_id)
        overdue = self.overdue_info(customer_id)

        score = 500 # Base score

        # ---------------------------------------------------------
        # 1) Limit usage (the more you use it, the lower the score)
        # ---------------------------------------------------------
        if customer.credit_limit:
            usage_percent = float(outstanding / customer.credit_limit) * 100

            if usage_percent > 90:
                score -= 200

            elif usage_percent > 70:
                score -= 120

            elif usage_percent > 50:
                score -= 60

        # ---------------------------------------------------------
        # 2) Overdue behavior
        # ---------------------------------------------------------
        if overdue["count_overdue"] > 0:
            score -= overdue["count_overdue"] * 25
            score -= min(overdue["max_days_overdue"], 120)  # max penalty 120 pts

        # ---------------------------------------------------------
        # 3) Long-term customer? (+ points)
        # ---------------------------------------------------------
        if customer.created_at:
            years = max((datetime.now(timezone.utc) - customer.created_at).days // 365, 0)

            if years >= 5:
                score += 80

            elif years >= 2:
                score += 40

        # ---------------------------------------------------------
        # 3) Long-term customer? (+ points)
        # ---------------------------------------------------------
        payments = (
            self.db.query(func.count(CreditHistory.id))
            .filter(
                CreditHistory.customer_id == customer.id,
                CreditHistory.event_type == "payment"
            )
            .scalar()
        )

        score += min(int(payments * 2), 60)

        # Limit 0 - 1000
        score = max(0, min(1000, score))

        return score

    # ==========================================================
    # PROFILE ASSIGNMENT (BRONZE / SILVER / GOLD / DIAMOND)
    # ===========================================================
    @staticmethod
    def assign_profile(score: int) -> str:

        if score >= 850:
            return "DIAMOND"

        elif score >= 700:
            return "GOLD"

        elif score >= 500:
            return "SILVER"

        return "BRONZE"

    # ============================================================
    # UPDATE PROFILE AND SCORE
    # ============================================================
    def update_customer_profile(self, customer_id: int) -> dict:
        customer = self.db.query(Customer).filter(Customer.id == customer_id).first()

        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")

        new_score = self.recalculate_score(customer_id)
        new_profile = self.assign_profile(new_score)

        customer.credit_score = new_score
        customer.credit_profile = new_profile

        self.db.add(customer)
        self.db.commit()

        return {
            "customer_id": customer.id,
            "new_score": new_score,
            "new_profile": new_profile
        }

    # ============================================================
    # SCORE VIEW
    # ============================================================
    def get_score(self, customer_id: int) -> dict:
        customer = self.db.query(Customer).filter(Customer.id == customer_id).first()

        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")

        return {
            "customer_id": customer.id,
            "name": customer.name,
            "credit_score": customer.credit_score,
            "profile": customer.credit_profile
        }

    # ============================================================
    # LIMIT VIEW
    # ============================================================
    def get_limit(self, customer_id: int) -> dict:
        customer = self.db.query(Customer).filter(Customer.id == customer_id).first()

        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")

        outstanding = self.outstanding_amount(customer_id)
        total_limit = Decimal(customer.credit_limit or 0)
        available = total_limit - outstanding

        return {
            "customer_id": customer.id,
            "total_limit": total_limit,
            "used": outstanding,
            "available": available
        }

    # ============================================================
    # STATUS OVERVIEW
    # ============================================================
    def check_customer_status(self, customer_id: int) -> dict:
        customer = self.db.query(Customer).filter(Customer.id == customer_id).first()

        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")

        overdue = self.overdue_info(customer_id)
        outstanding = self.outstanding_amount(customer_id)

        total_limit = Decimal(customer.credit_limit or 0)
        available = total_limit - outstanding

        return {
            "customer_id": customer.id,
            "name": customer.name,
            "credit_profile": customer.credit_profile,
            "credit_score": customer.credit_score,
            "limit_total": total_limit,
            "outstanding": outstanding,
            "available": available,
            "overdue": overdue
        }

    # ============================================================
    # CREDIT ANALYTICS — Global customer risk analysis
    # ============================================================
    def analytics(self, customer_id: int) -> dict:
        customer =self.db.query(Customer).filter(Customer.id == customer_id).first()

        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")

        # Base data
        outstanding = self.outstanding_amount(customer_id)
        total_limit = Decimal(customer.credit_limit or 0)
        available = total_limit - outstanding
        usage_percent = float(outstanding / total_limit * 100) if total_limit > 0 else 0

        overdue = self.overdue_info(customer_id)

        # Recent behavior (90 days)
        limit_days = datetime.now(timezone.utc) - timedelta(days=90)

        purchase_90 = (
            self.db.query(AccountReceivable)
            .filter(
                AccountReceivable.customer_id == customer.id,
                AccountReceivable.created_at >= limit_days
            )
            .count()
        )

        payments_90 = (
            self.db.query(CreditHistory)
            .filter(
                CreditHistory.customer_id == customer.id,
                CreditHistory.event_type == "payment",
                CreditHistory.created_at >= limit_days
            )
            .count()
        )

        # Determine trend
        if  payments_90 > purchase_90:
            trend = "improving"

        elif payments_90 == purchase_90:
            trend = "stable"

        else:
            trend = "worsening"

        # Risk level (AI - style)
        if customer.credit_score >= 800:
            risk_level = "very-low"

        elif customer.credit_score >= 650:
            risk_level = "low"

        elif customer.credit_score >= 500:
            risk_level = "medium"

        elif customer.credit_score >= 350:
            risk_level = "high"

        else:
            risk_level = "very-high"

        return {
            "customer_id": customer.id,
            "name": customer.name,

            "credit_score": customer.credit_score,
            "credit_profile": customer.credit_profile,
            "risk_level": risk_level,

            "credit_limit": total_limit,
            "outstanding": outstanding,
            "available": available,
            "usage_percent": round(usage_percent, 2),

            "overdue_invoices": overdue["count_overdue"],
            "max_days_overdue": overdue["max_days_overdue"],

            "payments_last_90": payments_90,
            "purchases_last_90": purchase_90,

            "trend": trend
        }

    # ============================================================
    # GLOBAL RISK REPORT
    # ============================================================
    def risk_report(self) -> dict:
        customers = self.db.query(Customer).all()

        top_risk = []
        top_safe = []

        for customer in customers:
            outstanding = self.outstanding_amount(customer.id)
            total_limit = Decimal(customer.credit_limit or 0)
            usage_percent = float(outstanding / total_limit * 100) if total_limit > 0 else 0

            overdue = self.overdue_info(customer.id)

            # Determine risk_level
            if customer.credit_score is None:
                risk = "unknown"

            elif customer.credit_score >= 850:

                risk = "very-low"

            elif customer.credit_score >= 650:

                risk = "low"

            elif customer.credit_score >= 500:

                risk = "medium"

            elif customer.credit_score >= 350:

                risk = "high"

            else:

                risk = "very-high"

            entry = {
                "customer_id": customer.id,
                "name": customer.name,
                "credit_score": customer.credit_score,
                "profile": customer.credit_profile,
                "risk_level": risk,
                "outstanding": outstanding,
                "usage_percent": round(usage_percent, 2),
                "max_days_overdue": overdue["max_days_overdue"],
            }

            if risk in ("high", "very-high"):
                top_risk.append(entry)

            else:
                top_safe.append(entry)

        # Order lists
        top_risk.sort(key=lambda x: (x["usage_percent"], x["max_days_overdue"], -(x["credit_score"] or 0)), reverse=True)
        top_safe.sort(key=lambda x: (x["credit_score"] or 0), reverse=True)

        return {
            "generated_at": datetime.now(timezone.utc),
            "total_customers": len(customers),
            "top_risk_customers": top_risk[:10],
            "top_safe_customers": top_safe[:10],
        }

    # ============================================================
    # APPLY SCORE + PROFILE + HISTORY
    # ============================================================
    def recalc_and_apply(self, customer_id: int) -> dict:
        score = self.recalculate_score(customer_id)
        profile = self.assign_profile(score)

        customer = self.db.query(Customer).filter(Customer.id == customer_id).first()

        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")

        if self.is_credit_blocked(customer.id):
            self.emit_alert(
                customer_id=customer.id,
                type_alert="credit_block",
                message="Customer credit blocked automatically due to risk"

            )

        old_score = customer.credit_score
        old_profile = customer.credit_profile

        customer.credit_score = score
        customer.credit_profile = profile

        self.db.add(customer)

        # History
        self.db.add(CreditHistory(
            customer_id=customer.id,
            event_type="score_recalc",
            amount=0,
            balance_after=customer.credit_used or 0,
            notes=f"Score {old_score} → {score}, Profile {old_profile} → {profile}"
        ))

        self.db.commit()

        return {
            "customer_id": customer.id,
            "score": score,
            "profile": profile
        }

    # ============================================================
    # RECALCULATE ALL CUSTOMERS (ADMIN / CRON)
    # ============================================================
    def recalc_all_customers(self) -> dict:
        customers = self.db.query(Customer).all()

        updated = 0
        errors= []

        for customer in customers:
            try:
                self.recalc_and_apply(customer.id)
                updated += 1

            except Exception as e:
                errors.append({
                    "customer_id": customer.id,
                    "error": str(e)
                })

        return {
            "total_customers": len(customers),
            "updated": updated,
            "errors": errors
        }

    # ============================================================
    # CREDIT BLOCK DECISION
    # ============================================================
    def is_credit_blocked(self, customer_id: int) -> bool:
        customer = self.db.query(Customer).filter(Customer.id == customer_id).first()

        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")

        overdue = self.overdue_info(customer.id)
        outstanding = self.outstanding_amount(customer.id)

        if customer.credit_score is not None and customer.credit_score < 300:
            return True

        if overdue["max_days_overdue"] > 60:
            return True

        if customer.credit_limit and outstanding > customer.credit_limit:
            return True

        return False

    # ============================================================
    # EMIT ALERT
    # ============================================================
    def emit_alert(self, customer_id: int, type_alert: str, message: str) -> dict:
        self.db.add(CreditAlert(
            customer_id=customer_id,
            type_alert=type_alert,
            message=message
        ))
