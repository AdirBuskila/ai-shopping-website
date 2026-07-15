from decimal import Decimal

from app.core.enums import OrderStatus
from app.models import OrderItem, Product, User
from app.repositories.order_repository import OrderRepository


def _user(db, username="a"):
    u = User(username=username, email=f"{username}@x.com", password_hash="h")
    db.add(u)
    db.commit()
    return u.id


def _product(db, name="Apple iPhone 13", stock=5):
    p = Product(name=name, price_usd=Decimal("499"), stock=stock)
    db.add(p)
    db.commit()
    return p.id


def test_create_and_get_temp(db_session):
    uid = _user(db_session)
    repo = OrderRepository(db_session)
    assert repo.get_temp(uid) is None
    order = repo.create_temp(uid)
    assert order.id is not None
    assert order.status == OrderStatus.TEMP
    assert order.is_temp == 1
    found = repo.get_temp(uid)
    assert found.id == order.id


def test_get_item(db_session):
    uid = _user(db_session)
    pid = _product(db_session)
    repo = OrderRepository(db_session)
    order = repo.create_temp(uid)
    assert repo.get_item(order.id, pid) is None
    db_session.add(OrderItem(order_id=order.id, product_id=pid,
                             quantity=2, unit_price=Decimal("499")))
    db_session.commit()
    item = repo.get_item(order.id, pid)
    assert item.quantity == 2


def test_list_for_user_temp_first(db_session):
    uid = _user(db_session)
    repo = OrderRepository(db_session)
    # a closed order, then a temp one
    closed = repo.create_temp(uid)
    closed.status = OrderStatus.CLOSE
    closed.is_temp = None
    db_session.commit()
    temp = repo.create_temp(uid)
    ids = [o.id for o in repo.list_for_user(uid)]
    assert ids[0] == temp.id  # TEMP pinned first
    assert set(ids) == {temp.id, closed.id}


def test_delete_cascades_items(db_session):
    uid = _user(db_session)
    pid = _product(db_session)
    repo = OrderRepository(db_session)
    order = repo.create_temp(uid)
    oid = order.id
    db_session.add(OrderItem(order_id=oid, product_id=pid,
                             quantity=1, unit_price=Decimal("499")))
    db_session.commit()
    repo.delete(order)
    assert repo.get(oid) is None
    assert db_session.query(OrderItem).filter_by(order_id=oid).count() == 0
