from decimal import Decimal

from app.core.enums import SearchOp
from app.models import Product
from app.repositories.product_repository import ProductRepository


def _seed(db):
    db.add_all([
        Product(name="Apple iPhone 13", brand="Apple", category="smartphone",
                price_usd=Decimal("499"), stock=5),
        Product(name="Sun Table Lamp", brand="Ikea", category="accessory",
                price_usd=Decimal("40"), stock=20),
        # Google Pixel (not "Samsung") so "sun" doesn't coincidentally substring-match
        Product(name="Google Pixel", brand="Google", category="smartphone",
                price_usd=Decimal("300"), stock=0),
    ])
    db.commit()


def test_multi_term_or_name_search(db_session):
    _seed(db_session)
    repo = ProductRepository(db_session)
    names = {p.name for p in repo.search("iphone, sun", None, None, None, None)}
    assert names == {"Apple iPhone 13", "Sun Table Lamp"}


def test_stock_greater_than(db_session):
    _seed(db_session)
    repo = ProductRepository(db_session)
    names = {p.name for p in repo.search(None, SearchOp.GT, 10, None, None)}
    assert names == {"Sun Table Lamp"}


def test_price_less_than(db_session):
    _seed(db_session)
    repo = ProductRepository(db_session)
    names = {p.name for p in repo.search(None, None, None, SearchOp.LT, 350)}
    assert names == {"Sun Table Lamp", "Google Pixel"}


def test_no_match_returns_empty(db_session):
    _seed(db_session)
    repo = ProductRepository(db_session)
    assert repo.search("zzz", None, None, None, None) == []
