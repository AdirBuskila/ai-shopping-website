import pytest


@pytest.mark.integration
def test_ready_when_infra_up(client):
    # Requires: docker compose up -d mysql redis
    r = client.get("/health/ready")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["checks"] == {"database": True, "redis": True}
