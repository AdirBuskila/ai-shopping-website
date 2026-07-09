from decimal import Decimal

import pytest
from sqlalchemy.exc import IntegrityError

from app.core.enums import OrderStatus
from app.models import Order, Product, User


def test_product_roundtrip(db_session):
    db_session.add(Product(name="Test Phone", price_usd=Decimal("199.99"),
                           stock=5, category="phones"))
    db_session.commit()
    p = db_session.query(Product).filter_by(name="Test Phone").one()
    assert p.stock == 5
    assert p.price_usd == Decimal("199.99")


def test_only_one_temp_order_per_user(db_session):
    u = User(username="a", email="a@x.com", password_hash="h")
    db_session.add(u)
    db_session.commit()

    db_session.add(Order(user_id=u.id, status=OrderStatus.TEMP, is_temp=1))
    db_session.commit()

    db_session.add(Order(user_id=u.id, status=OrderStatus.TEMP, is_temp=1))
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_closed_orders_do_not_collide(db_session):
    u = User(username="b", email="b@x.com", password_hash="h")
    db_session.add(u)
    db_session.commit()
    # is_temp NULL for CLOSE -> many allowed (NULLs are distinct in unique index)
    db_session.add(Order(user_id=u.id, status=OrderStatus.CLOSE, is_temp=None))
    db_session.add(Order(user_id=u.id, status=OrderStatus.CLOSE, is_temp=None))
    db_session.commit()
    assert db_session.query(Order).filter_by(user_id=u.id).count() == 2
