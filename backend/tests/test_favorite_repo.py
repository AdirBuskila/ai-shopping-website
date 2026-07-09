from decimal import Decimal

from app.models import Product, User
from app.repositories.favorite_repository import FavoriteRepository


def _uid_pid(db):
    u = User(username="a", email="a@x.com", password_hash="h")
    p = Product(name="Apple iPhone 13", price_usd=Decimal("499"), stock=5)
    db.add_all([u, p])
    db.commit()
    return u.id, p.id


def test_add_exists_list_remove(db_session):
    uid, pid = _uid_pid(db_session)
    repo = FavoriteRepository(db_session)
    assert repo.exists(uid, pid) is False
    repo.add(uid, pid)
    assert repo.exists(uid, pid) is True
    assert [p.id for p in repo.list_products(uid)] == [pid]
    repo.remove(uid, pid)
    assert repo.list_products(uid) == []
