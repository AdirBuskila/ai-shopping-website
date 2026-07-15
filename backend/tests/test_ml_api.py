from datetime import datetime, timedelta, timezone

from app.models import User


def _now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def test_churn_for_user(client, db_session):
    u = User(username="buyer", email="b@x.com", password_hash="h",
             created_at=_now() - timedelta(days=90))
    db_session.add(u)
    db_session.commit()

    r = client.get(f"/ml/churn/{u.id}")
    assert r.status_code == 200
    body = r.json()
    assert body["user_id"] == u.id
    assert 0.0 <= body["probability"] <= 1.0
    assert body["label"] in ("churn", "retain")
    assert len(body["top_factors"]) >= 1
    assert set(body["features"]) >= {"recency_days", "frequency", "monetary"}


def test_churn_unknown_user_404(client):
    assert client.get("/ml/churn/999999").status_code == 404
