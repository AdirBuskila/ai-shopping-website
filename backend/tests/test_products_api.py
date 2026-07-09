from decimal import Decimal

from app.models import Product


def _seed(db):
    db.add(Product(name="Apple iPhone 13", brand="Apple", category="smartphone",
                   price_usd=Decimal("499.00"), stock=5, image_url="/x.jpg",
                   description="d"))
    db.commit()


def test_list_products(client, db_session):
    _seed(db_session)
    r = client.get("/products")
    assert r.status_code == 200
    body = r.json()
    assert len(body) == 1
    assert body[0]["name"] == "Apple iPhone 13"
    assert body[0]["price_usd"] == 499.0 and body[0]["stock"] == 5


def test_get_product_by_id(client, db_session):
    _seed(db_session)
    pid = db_session.query(Product).one().id
    assert client.get(f"/products/{pid}").json()["name"] == "Apple iPhone 13"


def test_get_missing_product_404(client):
    assert client.get("/products/999").status_code == 404
