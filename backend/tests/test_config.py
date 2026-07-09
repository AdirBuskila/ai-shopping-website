def test_settings_reads_env(monkeypatch):
    monkeypatch.setenv("JWT_SECRET", "test-secret")
    monkeypatch.setenv("CHAT_PROMPT_LIMIT", "5")
    from app.core.config import Settings
    s = Settings()
    assert s.jwt_secret == "test-secret"
    assert s.chat_prompt_limit == 5
    assert s.openai_embedding_model == "text-embedding-3-small"
