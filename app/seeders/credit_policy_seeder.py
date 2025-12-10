# app/seeders/credit_policy_seeder.py

from app.models.credit_policy import CreditPolicy


DEFAULT_POLICIES = [
    CreditPolicy(
        profile="DIAMOND",
        allow_credit=True,
        max_installments=18,
        max_sale_amount=50000,
        max_percentage_of_limit=100,
        max_delay_days=30,
        max_open_invoices=10
    ),

    CreditPolicy(
        profile="GOLD",
        allow_credit=True,
        max_installments=12,
        max_sale_amount=30000,
        max_percentage_of_limit=90,
        max_delay_days=20,
        max_open_invoices=8
    ),

    CreditPolicy(
        profile="SILVER",
        allow_credit=True,
        max_installments=6,
        max_sale_amount=15000,
        max_percentage_of_limit=80,
        max_delay_days=15,
        max_open_invoices=6
    ),

    CreditPolicy(
        profile="BRONZE",
        allow_credit=True,
        max_installments=3,
        max_sale_amount=5000,
        max_percentage_of_limit=60,
        max_delay_days=10,
        max_open_invoices=4
    ),
]


def seed_default_credit_policies(db):
    existing = db.query(CreditPolicy).count()
    if existing == 0:
        for policy in DEFAULT_POLICIES:
            db.add(policy)
        db.commit()
