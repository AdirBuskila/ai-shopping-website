import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.core.redis_client import get_redis
import app.models  # noqa: F401  registers all models on Base.metadata
from app.main import create_app


class _FakeCache:
    """No-op cache: always a miss, so endpoint tests hit the DB and never
    share state through real Redis."""

    def get(self, key):
        return None

    def setex(self, key, ttl, value):
        pass

    def delete(self, key):
        pass


@pytest.fixture
def _engine():
    """One shared in-memory SQLite DB per test (StaticPool = single connection),
    with foreign keys enforced so cascade deletes behave like MySQL."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def _fk(dbapi_con, _record):
        dbapi_con.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def db_session(_engine):
    session = sessionmaker(bind=_engine)()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(_engine):
    Session = sessionmaker(bind=_engine)

    def override_get_db():
        db = Session()
        try:
            yield db
        finally:
            db.close()

    app = create_app()
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_redis] = lambda: _FakeCache()
    return TestClient(app)
