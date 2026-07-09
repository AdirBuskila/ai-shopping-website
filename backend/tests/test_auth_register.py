def _payload(**over):
    base = dict(
        username="adir", password="pw12345", email="a@x.com",
        first_name="Adir", last_name="B", phone="050", country="IL", city="TA",
    )
    base.update(over)
    return base


def test_register_returns_public_user_without_password(client):
    r = client.post("/auth/register", json=_payload())
    assert r.status_code == 201
    body = r.json()
    assert body["username"] == "adir"
    assert "password" not in body and "password_hash" not in body


def test_password_is_stored_hashed(client, db_session):
    client.post("/auth/register", json=_payload())
    from app.core.security import verify_password
    from app.models import User
    u = db_session.query(User).filter_by(username="adir").one()
    assert u.password_hash != "pw12345"
    assert verify_password("pw12345", u.password_hash)


def test_duplicate_username_conflicts(client):
    client.post("/auth/register", json=_payload())
    r = client.post("/auth/register", json=_payload(email="b@x.com"))
    assert r.status_code == 409


def test_duplicate_email_conflicts(client):
    client.post("/auth/register", json=_payload())
    r = client.post("/auth/register", json=_payload(username="other"))
    assert r.status_code == 409
