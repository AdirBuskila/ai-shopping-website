import pytest

from app.ai.vector_store import DIM, VectorStore
from app.core.redis_client import redis_client


@pytest.mark.integration
def test_knn_returns_nearest_first():
    store = VectorStore(redis_client)
    store.clear()
    store.ensure_index()

    base = [0.0] * DIM
    near = base.copy(); near[0] = 1.0
    far = base.copy(); far[1] = 1.0
    store.upsert(1, near, "near")
    store.upsert(2, far, "far")

    query = base.copy(); query[0] = 0.9
    assert store.knn(query, k=1) == [1]
    assert store.knn(query, k=2) == [1, 2]
    assert store.knn(query, k=1, exclude_id=1) == [2]

    store.clear()
