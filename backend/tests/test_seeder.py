from app.models import Product
from scripts.seed_products import seed_products

ITEMS = [{
    "name": "X Phone", "description": "d", "category": "smartphone",
    "brand": "X", "price_usd": 100, "stock": 3, "image_url": None, "specs": {},
}]


def test_seed_inserts(db_session):
    n = seed_products(db_session, ITEMS)
    assert n == 1
    assert db_session.query(Product).filter_by(name="X Phone").one().stock == 3


def test_seed_is_idempotent(db_session):
    seed_products(db_session, ITEMS)
    seed_products(db_session, [{**ITEMS[0], "stock": 9}])
    rows = db_session.query(Product).filter_by(name="X Phone").all()
    assert len(rows) == 1 and rows[0].stock == 9  # updated, not duplicated
