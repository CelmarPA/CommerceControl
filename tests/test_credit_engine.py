from decimal import Decimal
from app.services.credit_engine import CreditEngine
from app.models.customer import Customer
from app.models.credit_policy import CreditPolicy

def test_simple_limit(db_session):  # supondo fixture db_session
    # cria policy C
    policy = CreditPolicy(profile='C', max_installments=3, max_percentage_of_limit=100)
    db_session.add(policy)
    db_session.commit()

    cust = Customer(name="Test", credit_limit=Decimal("1000.00"), credit_profile='C', credit_score=700)
    db_session.add(cust)
    db_session.commit()

    engine = CreditEngine(db_session)
    assert engine.validate_sale(cust.id, Decimal("100.00"), installments=1) is True

    # excede
    try:
        engine.validate_sale(cust.id, Decimal("2000.00"), installments=1)
        assert False, "should fail"
    except Exception:
        pass
