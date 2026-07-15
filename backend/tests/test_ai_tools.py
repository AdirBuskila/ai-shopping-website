from decimal import Decimal

from app.ai.tools import TOOL_SCHEMAS, ToolExecutor
from app.models import Product, User


class _FakeStore:
    ids: list[int] = []

    def knn(self, vec, k, exclude_id=None):
        return [i for i in self.ids if i != exclude_id]


def _p(db, name="Apple iPhone 13", stock=5, price="499"):
    p = Product(name=name, brand="Apple", category="smartphone",
                price_usd=Decimal(price), stock=stock)
    db.add(p)
    db.commit()
    return p.id


def _user(db):
    u = User(username="a", email="a@x.com", password_hash="h")
    db.add(u)
    db.commit()
    return u


def test_tool_schemas_expose_the_six_tools():
    names = {t["function"]["name"] for t in TOOL_SCHEMAS}
    assert names == {
        "search_products", "semantic_search", "get_product_details",
        "check_stock", "recommend_similar", "add_to_favorites",
    }


def test_check_stock_reports_live_value(db_session):
    pid = _p(db_session, stock=0)
    ex = ToolExecutor(db_session, _FakeStore(), embed_fn=lambda t: [0.0])
    out = ex.run("check_stock", {"product_id": pid})
    assert out["in_stock"] is False and out["stock"] == 0


def test_get_product_details(db_session):
    pid = _p(db_session)
    ex = ToolExecutor(db_session, _FakeStore(), embed_fn=lambda t: [0.0])
    out = ex.run("get_product_details", {"product_id": pid})
    assert out["product"]["id"] == pid
    assert out["product"]["name"] == "Apple iPhone 13"


def test_get_product_details_missing(db_session):
    ex = ToolExecutor(db_session, _FakeStore(), embed_fn=lambda t: [0.0])
    assert "error" in ex.run("get_product_details", {"product_id": 999})


def test_semantic_search_maps_knn_ids_to_products(db_session):
    pid = _p(db_session)
    store = _FakeStore(); store.ids = [pid]
    ex = ToolExecutor(db_session, store, embed_fn=lambda t: [0.0] * 3)
    out = ex.run("semantic_search", {"query": "a phone"})
    assert [p["id"] for p in out["products"]] == [pid]


def test_search_products_by_name(db_session):
    _p(db_session, "Apple iPhone 13")
    _p(db_session, "Google Pixel 8")
    ex = ToolExecutor(db_session, _FakeStore(), embed_fn=lambda t: [0.0])
    out = ex.run("search_products", {"query": "Pixel"})
    assert [p["name"] for p in out["products"]] == ["Google Pixel 8"]


def test_recommend_similar_excludes_self(db_session):
    a = _p(db_session, "Apple iPhone 13")
    b = _p(db_session, "Apple iPhone 14")
    store = _FakeStore(); store.ids = [a, b]
    ex = ToolExecutor(db_session, store, embed_fn=lambda t: [0.0] * 3)
    out = ex.run("recommend_similar", {"product_id": a})
    assert [p["id"] for p in out["products"]] == [b]


def test_add_to_favorites_requires_login(db_session):
    pid = _p(db_session)
    ex = ToolExecutor(db_session, _FakeStore(), embed_fn=lambda t: [0.0], user=None)
    assert "error" in ex.run("add_to_favorites", {"product_id": pid})


def test_add_to_favorites_when_logged_in(db_session):
    pid = _p(db_session)
    user = _user(db_session)
    ex = ToolExecutor(db_session, _FakeStore(), embed_fn=lambda t: [0.0], user=user)
    out = ex.run("add_to_favorites", {"product_id": pid})
    assert out.get("added") is True


def test_unknown_tool_returns_error(db_session):
    ex = ToolExecutor(db_session, _FakeStore(), embed_fn=lambda t: [0.0])
    assert "error" in ex.run("nope", {})
