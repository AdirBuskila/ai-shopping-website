"""OpenAI embeddings client (text-embedding-3-small → 1536-d vectors).

Every function here is a thin wrapper so the assistant can inject fakes in tests
and never hit the network. `is_configured()` lets the app degrade gracefully when
no real key is present.
"""
from openai import OpenAI

from app.core.config import settings

_client: OpenAI | None = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=settings.openai_api_key)
    return _client


def is_configured() -> bool:
    key = settings.openai_api_key or ""
    return bool(key) and not key.startswith("sk-REPLACE")


def embed(text: str) -> list[float]:
    resp = _get_client().embeddings.create(
        model=settings.openai_embedding_model, input=text)
    return resp.data[0].embedding


def embed_many(texts: list[str]) -> list[list[float]]:
    out: list[list[float]] = []
    for i in range(0, len(texts), 100):  # keep each request well under OpenAI limits
        chunk = texts[i:i + 100]
        resp = _get_client().embeddings.create(
            model=settings.openai_embedding_model, input=chunk)
        out.extend(d.embedding for d in resp.data)
    return out
