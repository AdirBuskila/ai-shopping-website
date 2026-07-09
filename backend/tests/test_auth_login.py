def _reg(client):
    client.post(
        "/auth/register",
        json=dict(username="adir", password="pw12345", email="a@x.com"),
    )


def test_login_returns_token(client):
    _reg(client)
    r = client.post("/auth/login", json=dict(username="adir", password="pw12345"))
    assert r.status_code == 200
    assert r.json()["access_token"]


def test_login_wrong_password_401(client):
    _reg(client)
    r = client.post("/auth/login", json=dict(username="adir", password="nope"))
    assert r.status_code == 401


def test_me_requires_token(client):
    assert client.get("/auth/me").status_code == 401


def test_me_returns_current_user(client):
    _reg(client)
    tok = client.post(
        "/auth/login", json=dict(username="adir", password="pw12345")
    ).json()["access_token"]
    r = client.get("/auth/me", headers={"Authorization": f"Bearer {tok}"})
    assert r.status_code == 200
    assert r.json()["username"] == "adir"
