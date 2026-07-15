from decimal import Decimal

from app.ai.assistant import Assistant
from app.models import Product


class FakeRedis:
    def __init__(self):
        self.kv = {}

    def get(self, k):
        return self.kv.get(k)

    def incr(self, k):
        self.kv[k] = int(self.kv.get(k, 0)) + 1
        return self.kv[k]

    def expire(self, k, ttl):
        pass


class FakeStore:
    def __init__(self, ids):
        self.ids = ids

    def ensure_index(self):
        pass

    def is_empty(self):
        return False

    def knn(self, vec, k, exclude_id=None):
        return [i for i in self.ids if i != exclude_id]


def _phone(db, name="Apple iPhone 13", stock=5):
    p = Product(name=name, brand="Apple", category="smartphone",
                price_usd=Decimal("499"), stock=stock)
    db.add(p)
    db.commit()
    return p.id


def test_five_prompt_cap(db_session, monkeypatch):
    monkeypatch.setattr("app.ai.assistant.is_configured", lambda: True)
    calls = []

    def chat_fn(messages, tools):
        calls.append(1)
        return {"content": "hi", "tool_calls": []}

    a = Assistant(db_session, FakeRedis(), embed_fn=lambda t: [0.0],
                  chat_fn=chat_fn, store=FakeStore([]))
    for _ in range(5):
        r = a.reply("hello", "s1")
        assert r["available"] is True
    blocked = a.reply("hello", "s1")
    assert blocked["remaining_prompts"] == 0
    assert "limit" in blocked["reply"].lower()
    assert len(calls) == 5  # the 6th never reached OpenAI


def test_remaining_decrements(db_session, monkeypatch):
    monkeypatch.setattr("app.ai.assistant.is_configured", lambda: True)
    a = Assistant(db_session, FakeRedis(), embed_fn=lambda t: [0.0],
                  chat_fn=lambda m, t: {"content": "hi", "tool_calls": []},
                  store=FakeStore([]))
    assert a.reply("hi", "s1")["remaining_prompts"] == 4
    assert a.reply("hi", "s1")["remaining_prompts"] == 3


def test_unavailable_when_not_configured(db_session, monkeypatch):
    monkeypatch.setattr("app.ai.assistant.is_configured", lambda: False)
    a = Assistant(db_session, FakeRedis(), embed_fn=lambda t: [0.0],
                  chat_fn=lambda m, t: {"content": "x", "tool_calls": []},
                  store=FakeStore([]))
    r = a.reply("hello", "s1")
    assert r["available"] is False
    assert "unavailable" in r["reply"].lower()


def test_agent_runs_tool_then_answers(db_session, monkeypatch):
    monkeypatch.setattr("app.ai.assistant.is_configured", lambda: True)
    pid = _phone(db_session)
    scripted = [
        {"content": None, "tool_calls": [
            {"id": "t1", "name": "check_stock", "arguments": {"product_id": pid}}]},
        {"content": "It's in stock.", "tool_calls": []},
    ]

    def chat_fn(messages, tools):
        return scripted.pop(0)

    a = Assistant(db_session, FakeRedis(), embed_fn=lambda t: [0.0],
                  chat_fn=chat_fn, store=FakeStore([pid]))
    r = a.reply("is it available?", "s1")
    assert r["reply"] == "It's in stock."
    assert r["available"] is True


def test_openai_error_degrades_gracefully(db_session, monkeypatch):
    monkeypatch.setattr("app.ai.assistant.is_configured", lambda: True)

    def boom(messages, tools):
        raise RuntimeError("openai down")

    a = Assistant(db_session, FakeRedis(), embed_fn=lambda t: [0.0],
                  chat_fn=boom, store=FakeStore([]))
    r = a.reply("hello", "s1")
    assert r["available"] is False
    assert "unavailable" in r["reply"].lower()
