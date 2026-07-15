from datetime import datetime, timedelta, timezone
from decimal import Decimal

from app.core.enums import OrderStatus
from app.ml.features import FEATURE_NAMES, compute_features, feature_vector
from app.models import Favorite, Order, OrderItem, Product, User


def _now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def test_features_for_a_buyer(db_session):
    u = User(username="a", email="a@x.com", password_hash="h",
             created_at=_now() - timedelta(days=100))
    p = Product(name="Phone", price_usd=Decimal("500"), stock=5)
    db_session.add_all([u, p])
    db_session.commit()
    o = Order(user_id=u.id, status=OrderStatus.CLOSE, is_temp=None,
              total_price=Decimal("500"),
              created_at=_now() - timedelta(days=10),
              closed_at=_now() - timedelta(days=10))
    db_session.add(o)
    db_session.commit()
    db_session.add(OrderItem(order_id=o.id, product_id=p.id, quantity=1,
                             unit_price=Decimal("500")))
    db_session.add(Favorite(user_id=u.id, product_id=p.id))
    db_session.commit()

    f = compute_features(db_session, u.id)
    assert f["frequency"] == 1
    assert f["monetary"] == 500.0
    assert f["avg_order_value"] == 500.0
    assert f["favorites_count"] == 1
    assert 8 <= f["recency_days"] <= 12
    assert 98 <= f["tenure_days"] <= 102
    assert len(feature_vector(f)) == len(FEATURE_NAMES)


def test_features_for_non_buyer(db_session):
    u = User(username="b", email="b@x.com", password_hash="h",
             created_at=_now() - timedelta(days=200))
    db_session.add(u)
    db_session.commit()

    f = compute_features(db_session, u.id)
    assert f["frequency"] == 0
    assert f["monetary"] == 0.0
    assert f["avg_order_value"] == 0.0
    assert f["recency_days"] == f["tenure_days"]  # never bought → recency = tenure


def test_temp_orders_do_not_count(db_session):
    u = User(username="c", email="c@x.com", password_hash="h",
             created_at=_now() - timedelta(days=50))
    db_session.add(u)
    db_session.commit()
    # an open cart must NOT count as a purchase
    db_session.add(Order(user_id=u.id, status=OrderStatus.TEMP, is_temp=1,
                         total_price=Decimal("999")))
    db_session.commit()

    f = compute_features(db_session, u.id)
    assert f["frequency"] == 0 and f["monetary"] == 0.0
