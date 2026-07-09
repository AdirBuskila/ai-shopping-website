from decimal import Decimal

from app.models import Product


def _headers(client, username="adir"):
    client.post("/auth/register", json=dict(
        username=username, password="pw12345", email=f"{username}@x.com"))
    tok = client.post("/auth/login", json=dict(
        username=username, password="pw12345")).json()["access_token"]
    return {"Authorization": f"Bearer {tok}"}


def _product(db, name="Apple iPhone 13"):
    p = Product(name=name, brand="Apple", category="smartphone",
                price_usd=Decimal("499"), stock=5)
    db.add(p)
    db.commit()
    return p.id


def test_favorites_require_login(client):
    assert client.get("/favorites").status_code == 401
    assert client.post("/favorites/1").status_code == 401
    assert client.delete("/favorites/1").status_code == 401


def test_add_then_list(client, db_session):
    h = _headers(client)
    pid = _product(db_session)
    r = client.post(f"/favorites/{pid}", headers=h)
    assert r.status_code == 201
    assert [p["id"] for p in r.json()] == [pid]
    assert [p["id"] for p in client.get("/favorites", headers=h).json()] == [pid]


def test_add_is_unique(client, db_session):
    h = _headers(client)
    pid = _product(db_session)
    client.post(f"/favorites/{pid}", headers=h)
    body = client.post(f"/favorites/{pid}", headers=h).json()
    assert [p["id"] for p in body] == [pid]  # still once


def test_remove(client, db_session):
    h = _headers(client)
    pid = _product(db_session)
    client.post(f"/favorites/{pid}", headers=h)
    assert client.delete(f"/favorites/{pid}", headers=h).json() == []


def test_add_missing_product_404(client):
    h = _headers(client)
    assert client.post("/favorites/999", headers=h).status_code == 404


def test_favorites_isolated_per_user(client, db_session):
    pid = _product(db_session)
    ha = _headers(client, "usera")
    hb = _headers(client, "userb")
    client.post(f"/favorites/{pid}", headers=ha)
    assert client.get("/favorites", headers=hb).json() == []
