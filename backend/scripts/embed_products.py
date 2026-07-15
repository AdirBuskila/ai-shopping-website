"""Embed every product into the Redis vector store. Run once (like seeding);
the chat path also builds the index lazily if it's still empty."""
import pathlib
import sys

# allow "import app" when run directly — find the dir that holds the app package
# (host layout: repo-root/backend/app ; container layout: /app/app)
_here = pathlib.Path(__file__).resolve()
for _cand in (_here.parents[1] / "backend", _here.parents[1]):
    if (_cand / "app").is_dir():
        sys.path.insert(0, str(_cand))
        break

from app.ai.indexer import build_index  # noqa: E402
from app.ai.vector_store import VectorStore  # noqa: E402
from app.core.database import SessionLocal  # noqa: E402
from app.core.redis_client import redis_client  # noqa: E402


def main() -> None:
    db = SessionLocal()
    try:
        store = VectorStore(redis_client)
        store.clear()  # rebuild cleanly
        n = build_index(db, store)
        print("embedded", n, "products")
    finally:
        db.close()


if __name__ == "__main__":
    main()
