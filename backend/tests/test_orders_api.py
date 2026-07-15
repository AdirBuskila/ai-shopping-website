from decimal import Decimal

from app.models import Product


def _register(client, username="adir"):
    client.post("/auth/register", json=dict(
        username=username, password="pw12345", email=f"{username}@x.com"))


def _login(client, username="adir"):
    tok = client.post("/auth/login", json=dict(
        username=username, password="pw12345")).json()["access_token"]
    return {"Authorization": f"Bearer {tok}"}


def _headers(client, username="adir"):
    _register(client, username)
    return _login(client, username)


def _product(db, name="Apple iPhone 13", price="499", stock=5):
    p = Product(name=name, brand="Apple", category="smartphone",
                price_usd=Decimal(price), stock=stock)
    db.add(p)
    db.commit()
    return p.id


def _add(client, headers, pid, qty=1):
    return client.post("/orders/items", headers=headers,
                       json={"product_id": pid, "quantity": qty})


# --- auth gate ---------------------------------------------------------------

def test_orders_require_login(client):
    assert client.get("/orders").status_code == 401
    assert client.post("/orders/items", json={"product_id": 1}).status_code == 401
    assert client.delete("/orders/items/1").status_code == 401
    assert client.get("/orders/1").status_code == 401
    assert client.post("/orders/1/purchase", json={}).status_code == 401
    assert client.delete("/orders/1").status_code == 401


# --- add / cart --------------------------------------------------------------

def test_first_add_creates_temp(client, db_session):
    h = _headers(client)
    pid = _product(db_session)
    r = _add(client, h, pid)
    assert r.status_code == 201
    body = r.json()
    assert body["status"] == "TEMP"
    assert body["total_price"] == 499.0
    assert len(body["items"]) == 1
    line = body["items"][0]
    assert line["product_id"] == pid
    assert line["name"] == "Apple iPhone 13"
    assert line["quantity"] == 1
    assert line["line_total"] == 499.0
    assert len(client.get("/orders", headers=h).json()) == 1


def test_duplicate_add_increments(client, db_session):
    h = _headers(client)
    pid = _product(db_session)
    _add(client, h, pid)
    body = _add(client, h, pid).json()
    assert len(body["items"]) == 1          # still one line
    assert body["items"][0]["quantity"] == 2
    assert body["total_price"] == 998.0


def test_multi_product_total(client, db_session):
    h = _headers(client)
    a = _product(db_session, "Apple iPhone 13", "499", 5)
    b = _product(db_session, "Google Pixel 8", "301", 5)
    _add(client, h, a)
    body = _add(client, h, b).json()
    assert len(body["items"]) == 2
    assert body["total_price"] == 800.0


def test_add_missing_product_404(client):
    h = _headers(client)
    assert _add(client, h, 999).status_code == 404


def test_add_out_of_stock_409(client, db_session):
    h = _headers(client)
    pid = _product(db_session, stock=0)
    assert _add(client, h, pid).status_code == 409


def test_add_exceeds_stock_409(client, db_session):
    h = _headers(client)
    pid = _product(db_session, stock=3)
    assert _add(client, h, pid, qty=5).status_code == 409


def test_increment_exceeding_stock_is_rejected(client, db_session):
    h = _headers(client)
    pid = _product(db_session, stock=2)
    assert _add(client, h, pid, qty=2).status_code == 201
    assert _add(client, h, pid, qty=1).status_code == 409  # would be 3 > 2
    # unchanged
    assert client.get("/orders", headers=h).json()[0]["items"][0]["quantity"] == 2


# --- remove ------------------------------------------------------------------

def test_remove_item_updates_total(client, db_session):
    h = _headers(client)
    a = _product(db_session, "Apple iPhone 13", "499", 5)
    b = _product(db_session, "Google Pixel 8", "301", 5)
    _add(client, h, a)
    _add(client, h, b)
    body = client.delete(f"/orders/items/{a}", headers=h).json()
    assert [i["product_id"] for i in body["items"]] == [b]
    assert body["total_price"] == 301.0


def test_remove_last_item_deletes_order(client, db_session):
    h = _headers(client)
    pid = _product(db_session)
    _add(client, h, pid)
    assert client.delete(f"/orders/items/{pid}", headers=h).json() is None
    assert client.get("/orders", headers=h).json() == []


# --- one TEMP per user + persistence ----------------------------------------

def test_one_temp_per_user(client, db_session):
    h = _headers(client)
    a = _product(db_session, "Apple iPhone 13", "499", 5)
    b = _product(db_session, "Google Pixel 8", "301", 5)
    _add(client, h, a)
    _add(client, h, b)
    orders = client.get("/orders", headers=h).json()
    assert len(orders) == 1               # single TEMP cart
    assert orders[0]["status"] == "TEMP"


def test_temp_survives_relogin(client, db_session):
    h1 = _headers(client)
    pid = _product(db_session)
    _add(client, h1, pid)
    h2 = _login(client)                   # new token, same user (simulated re-login)
    orders = client.get("/orders", headers=h2).json()
    assert len(orders) == 1
    assert orders[0]["items"][0]["product_id"] == pid


# --- purchase ----------------------------------------------------------------

def test_purchase_closes_and_decrements_stock(client, db_session):
    h = _headers(client)
    pid = _product(db_session, stock=5)
    _add(client, h, pid, qty=2)
    oid = client.get("/orders", headers=h).json()[0]["id"]
    r = client.post(f"/orders/{oid}/purchase", headers=h,
                    json={"shipping_address": "1 Main St, Tel Aviv"})
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "CLOSE"
    assert body["shipping_address"] == "1 Main St, Tel Aviv"
    assert body["closed_at"] is not None
    # stock decremented 5 -> 3
    assert client.get(f"/products/{pid}").json()["stock"] == 3


def test_purchase_nonexistent_404(client):
    h = _headers(client)
    assert client.post("/orders/999/purchase", headers=h, json={}).status_code == 404


def test_purchase_twice_is_rejected(client, db_session):
    h = _headers(client)
    pid = _product(db_session, stock=5)
    _add(client, h, pid)
    oid = client.get("/orders", headers=h).json()[0]["id"]
    assert client.post(f"/orders/{oid}/purchase", headers=h, json={}).status_code == 200
    assert client.post(f"/orders/{oid}/purchase", headers=h, json={}).status_code == 409


def test_purchase_then_overorder_blocked(client, db_session):
    h = _headers(client)
    pid = _product(db_session, stock=2)
    _add(client, h, pid, qty=2)
    oid = client.get("/orders", headers=h).json()[0]["id"]
    client.post(f"/orders/{oid}/purchase", headers=h, json={})
    # stock now 0 -> a new add is rejected
    assert _add(client, h, pid).status_code == 409


def test_new_temp_after_purchase(client, db_session):
    h = _headers(client)
    a = _product(db_session, "Apple iPhone 13", "499", 5)
    b = _product(db_session, "Google Pixel 8", "301", 5)
    _add(client, h, a)
    oid = client.get("/orders", headers=h).json()[0]["id"]
    client.post(f"/orders/{oid}/purchase", headers=h, json={})
    _add(client, h, b)                    # starts a fresh TEMP
    orders = client.get("/orders", headers=h).json()
    assert orders[0]["status"] == "TEMP"   # TEMP pinned first
    assert orders[0]["items"][0]["product_id"] == b
    assert {o["status"] for o in orders} == {"TEMP", "CLOSE"}


# --- delete order ------------------------------------------------------------

def test_delete_temp_order(client, db_session):
    h = _headers(client)
    pid = _product(db_session)
    _add(client, h, pid)
    oid = client.get("/orders", headers=h).json()[0]["id"]
    assert client.delete(f"/orders/{oid}", headers=h).status_code == 204
    assert client.get("/orders", headers=h).json() == []


def test_cannot_delete_closed_order(client, db_session):
    h = _headers(client)
    pid = _product(db_session)
    _add(client, h, pid)
    oid = client.get("/orders", headers=h).json()[0]["id"]
    client.post(f"/orders/{oid}/purchase", headers=h, json={})
    assert client.delete(f"/orders/{oid}", headers=h).status_code == 409


# --- ownership isolation -----------------------------------------------------

def test_orders_isolated_per_user(client, db_session):
    pid = _product(db_session)
    ha = _headers(client, "usera")
    hb = _headers(client, "userb")
    _add(client, ha, pid)
    oid = client.get("/orders", headers=ha).json()[0]["id"]
    assert client.get("/orders", headers=hb).json() == []
    assert client.get(f"/orders/{oid}", headers=hb).status_code == 404
    assert client.post(f"/orders/{oid}/purchase", headers=hb, json={}).status_code == 404
    assert client.delete(f"/orders/{oid}", headers=hb).status_code == 404
