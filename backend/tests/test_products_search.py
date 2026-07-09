from decimal import Decimal

from app.models import Product


def _seed(db):
    db.add_all([
        Product(name="Apple iPhone 13", brand="Apple", category="smartphone",
                price_usd=Decimal("499"), stock=5),
        Product(name="Sun Table Lamp", brand="Ikea", category="accessory",
                price_usd=Decimal("40"), stock=20),
        Product(name="Google Pixel", brand="Google", category="smartphone",
                price_usd=Decimal("300"), stock=0),
    ])
    db.commit()


def test_search_multi_term(client, db_session):
    _seed(db_session)
    names = {p["name"] for p in client.get("/products/search",
                                            params={"q": "iphone, sun"}).json()}
    assert names == {"Apple iPhone 13", "Sun Table Lamp"}


def test_search_stock_range(client, db_session):
    _seed(db_session)
    r = client.get("/products/search", params={"stock_op": ">", "stock_value": 10})
    assert {p["name"] for p in r.json()} == {"Sun Table Lamp"}


def test_search_price_range(client, db_session):
    _seed(db_session)
    r = client.get("/products/search", params={"price_op": "<", "price_value": 350})
    assert {p["name"] for p in r.json()} == {"Sun Table Lamp", "Google Pixel"}


def test_search_empty_result_is_200_empty(client, db_session):
    _seed(db_session)
    r = client.get("/products/search", params={"q": "zzz"})
    assert r.status_code == 200 and r.json() == []
