from app.ai import embeddings


def test_is_configured_false_for_placeholder(monkeypatch):
    monkeypatch.setattr(embeddings.settings, "openai_api_key", "sk-REPLACE_ME")
    assert embeddings.is_configured() is False


def test_is_configured_false_for_empty(monkeypatch):
    monkeypatch.setattr(embeddings.settings, "openai_api_key", "")
    assert embeddings.is_configured() is False


def test_is_configured_true_for_real_key(monkeypatch):
    monkeypatch.setattr(embeddings.settings, "openai_api_key", "sk-proj-abc123")
    assert embeddings.is_configured() is True
