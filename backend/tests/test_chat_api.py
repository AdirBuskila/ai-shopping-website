from fastapi import Depends

from app.ai.assistant import Assistant
from app.controllers.chat import get_assistant
from app.core.database import get_db


class _FakeRedis:
    def __init__(self):
        self.kv = {}

    def get(self, k):
        return self.kv.get(k)

    def incr(self, k):
        self.kv[k] = int(self.kv.get(k, 0)) + 1
        return self.kv[k]

    def expire(self, k, ttl):
        pass


class _FakeStore:
    def ensure_index(self):
        pass

    def is_empty(self):
        return False

    def knn(self, vec, k, exclude_id=None):
        return []


# One real Assistant wired with fakes, so the endpoint + assistant logic run
# end-to-end with zero network. Shared redis so the cap persists across requests.
_shared_redis = _FakeRedis()


def _factory(db=Depends(get_db)):
    return Assistant(
        db, _shared_redis, embed_fn=lambda t: [0.0],
        chat_fn=lambda m, t: {"content": "Here are some options.", "tool_calls": []},
        store=_FakeStore())


def test_chat_returns_reply_and_remaining(client, monkeypatch):
    monkeypatch.setattr("app.ai.assistant.is_configured", lambda: True)
    client.app.dependency_overrides[get_assistant] = _factory
    r = client.post("/chat", json={"message": "hi", "session_id": "chat-test-1"})
    assert r.status_code == 200
    body = r.json()
    assert body["reply"] == "Here are some options."
    assert body["remaining_prompts"] == 4
    assert body["available"] is True


def test_chat_validates_body(client):
    assert client.post("/chat", json={}).status_code == 422
    assert client.post("/chat", json={"message": "hi"}).status_code == 422
