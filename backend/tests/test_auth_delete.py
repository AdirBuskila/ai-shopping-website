from app.core.enums import OrderStatus


def _login(client):
    client.post(
        "/auth/register",
        json=dict(username="adir", password="pw12345", email="a@x.com"),
    )
    return client.post(
        "/auth/login", json=dict(username="adir", password="pw12345")
    ).json()["access_token"]


def test_delete_account_then_me_401(client):
    tok = _login(client)
    h = {"Authorization": f"Bearer {tok}"}
    assert client.delete("/auth/me", headers=h).status_code == 204
    assert client.get("/auth/me", headers=h).status_code == 401


def test_delete_cascades_favorites_and_orders(client, db_session):
    tok = _login(client)
    from app.models import Favorite, Order, Product, User

    u = db_session.query(User).filter_by(username="adir").one()
    user_id = u.id  # capture before the account is deleted (row will be gone)
    p = Product(name="P", price_usd=10, stock=1)
    db_session.add(p)
    db_session.commit()
    product_id = p.id
    db_session.add(Favorite(user_id=user_id, product_id=product_id))
    db_session.add(Order(user_id=user_id, status=OrderStatus.TEMP, is_temp=1))
    db_session.commit()

    client.delete("/auth/me", headers={"Authorization": f"Bearer {tok}"})
    db_session.expire_all()

    assert db_session.query(Favorite).filter_by(user_id=user_id).count() == 0
    assert db_session.query(Order).filter_by(user_id=user_id).count() == 0
