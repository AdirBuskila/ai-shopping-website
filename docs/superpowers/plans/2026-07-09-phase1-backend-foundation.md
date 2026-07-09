# Phase 1 — Backend Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Stand up the FastAPI backend skeleton — config, enums, database + Redis clients, all ORM models, migrations, and health checks — so `docker-compose up` boots a live, migrated API.

**Architecture:** MVC layering (`controllers → services → repositories → models`) with a pydantic-settings config layer and centralized enums. SQLAlchemy 2.x over MySQL 8; Redis for cache/counters/vectors (later phases). This phase builds the foundation only: no business endpoints yet, but the full data model and a running, migrated, containerized service.

**Tech Stack:** Python 3.12, FastAPI, SQLAlchemy 2.x, PyMySQL, Alembic, redis-py, pydantic-settings, pytest, Docker Compose.

## Global Constraints

- Python **3.12**; backend package root is `backend/app`, imports are `from app....`.
- Stack is fixed: **FastAPI + MySQL 8 + Redis + Docker** (course requirement).
- **MVC layering:** controllers do HTTP only; services hold business rules; repositories own DB access; models are ORM entities. Enums centralized in `app/core/enums.py`.
- Money is **USD**, stored as `DECIMAL(10,2)`; catalog language is **English**.
- **One TEMP order per user** — enforced at the DB level via `UNIQUE(user_id, is_temp)`.
- Passwords are **bcrypt**-hashed (implemented Phase 2; column exists now).
- Single repository; `docker-compose up` must bring up the whole system.
- Unit tests run against **SQLite in-memory** (fast, no infra); infra-dependent checks are marked `integration` and run against the Docker MySQL/Redis.

---

### Task 1: Backend scaffold — config & enums

**Files:**
- Create: `backend/requirements.txt`
- Create: `backend/pyproject.toml`
- Create: `backend/app/__init__.py` (empty)
- Create: `backend/app/core/__init__.py` (empty)
- Create: `backend/app/core/config.py`
- Create: `backend/app/core/enums.py`
- Create: `backend/tests/__init__.py` (empty)
- Test: `backend/tests/test_config.py`, `backend/tests/test_enums.py`

**Interfaces:**
- Produces: `app.core.config.Settings` (pydantic settings) and module-level `settings`; `app.core.enums.{OrderStatus, SearchOp, Role, StockResult}`.

- [ ] **Step 1: Create dependency & tool files**

`backend/requirements.txt`:
```
fastapi>=0.111
uvicorn[standard]>=0.30
sqlalchemy>=2.0
pymysql>=1.1
alembic>=1.13
redis>=5.0
pydantic-settings>=2.2
httpx>=0.27
pytest>=8.0
```

`backend/pyproject.toml`:
```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["."]
markers = [
    "integration: tests that require the Docker MySQL/Redis services running",
]
```

- [ ] **Step 2: Install deps**

Run: `cd backend && python -m venv .venv && . .venv/Scripts/activate && pip install -r requirements.txt`
(On macOS/Linux: `source .venv/bin/activate`.)
Expected: installs without error.

- [ ] **Step 3: Write the failing tests**

`backend/tests/test_enums.py`:
```python
from app.core.enums import OrderStatus, SearchOp, Role, StockResult


def test_order_status_values():
    assert OrderStatus.TEMP.value == "TEMP"
    assert OrderStatus.CLOSE.value == "CLOSE"


def test_search_op_maps_symbols():
    assert SearchOp("<") is SearchOp.LT
    assert SearchOp(">") is SearchOp.GT
    assert SearchOp("=") is SearchOp.EQ


def test_role_and_stock_result_exist():
    assert Role.CUSTOMER.value == "CUSTOMER"
    assert StockResult.OUT_OF_STOCK.value == "OUT_OF_STOCK"
```

`backend/tests/test_config.py`:
```python
def test_settings_reads_env(monkeypatch):
    monkeypatch.setenv("JWT_SECRET", "test-secret")
    monkeypatch.setenv("CHAT_PROMPT_LIMIT", "5")
    from app.core.config import Settings
    s = Settings()
    assert s.jwt_secret == "test-secret"
    assert s.chat_prompt_limit == 5
    assert s.openai_embedding_model == "text-embedding-3-small"
```

- [ ] **Step 4: Run tests to verify they fail**

Run: `cd backend && pytest tests/test_enums.py tests/test_config.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.core.enums'`.

- [ ] **Step 5: Implement enums**

`backend/app/core/enums.py`:
```python
from enum import Enum


class OrderStatus(str, Enum):
    TEMP = "TEMP"
    CLOSE = "CLOSE"


class SearchOp(str, Enum):
    LT = "<"
    GT = ">"
    EQ = "="


class Role(str, Enum):
    CUSTOMER = "CUSTOMER"
    ADMIN = "ADMIN"


class StockResult(str, Enum):
    OK = "OK"
    INSUFFICIENT = "INSUFFICIENT"
    OUT_OF_STOCK = "OUT_OF_STOCK"
```

- [ ] **Step 6: Implement config**

`backend/app/core/config.py`:
```python
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # OpenAI (used from Phase 6)
    openai_api_key: str = "sk-REPLACE_ME"
    openai_chat_model: str = "gpt-4o-mini"
    openai_embedding_model: str = "text-embedding-3-small"
    chat_prompt_limit: int = 5

    # Database / Redis (Docker hostnames overridden via env in compose)
    database_url: str = "mysql+pymysql://shop:shop@localhost:3306/shopdb"
    redis_url: str = "redis://localhost:6379/0"

    # Auth
    jwt_secret: str = "change-me"
    jwt_expire_minutes: int = 1440


settings = Settings()
```

- [ ] **Step 7: Run tests to verify they pass**

Run: `cd backend && pytest tests/test_enums.py tests/test_config.py -v`
Expected: PASS (5 tests).

- [ ] **Step 8: Commit**

```bash
git add backend/requirements.txt backend/pyproject.toml backend/app backend/tests
git commit -m "feat(backend): scaffold config + enums"
```

---

### Task 2: FastAPI app factory + liveness endpoint

**Files:**
- Create: `backend/app/main.py`
- Create: `backend/app/controllers/__init__.py` (empty)
- Create: `backend/app/controllers/health.py`
- Test: `backend/tests/conftest.py`, `backend/tests/test_health.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `app.main.create_app() -> FastAPI` and module-level `app`; `GET /health` → `{"status": "ok"}`; a `client` pytest fixture.

- [ ] **Step 1: Write the failing test**

`backend/tests/conftest.py`:
```python
import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture
def client():
    return TestClient(create_app())
```

`backend/tests/test_health.py`:
```python
def test_health_ok(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/test_health.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.main'`.

- [ ] **Step 3: Implement the health controller**

`backend/app/controllers/health.py`:
```python
from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
def health():
    return {"status": "ok"}
```

- [ ] **Step 4: Implement the app factory**

`backend/app/main.py`:
```python
from fastapi import FastAPI

from app.controllers import health


def create_app() -> FastAPI:
    app = FastAPI(title="AI Shopping API", version="0.1.0")
    app.include_router(health.router)
    return app


app = create_app()
```

- [ ] **Step 5: Run test to verify it passes**

Run: `cd backend && pytest tests/test_health.py -v`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add backend/app/main.py backend/app/controllers backend/tests/conftest.py backend/tests/test_health.py
git commit -m "feat(backend): app factory + /health liveness"
```

---

### Task 3: Database + Redis clients and all ORM models

**Files:**
- Create: `backend/app/core/database.py`
- Create: `backend/app/core/redis_client.py`
- Create: `backend/app/models/__init__.py`
- Create: `backend/app/models/user.py`
- Create: `backend/app/models/product.py`
- Create: `backend/app/models/favorite.py`
- Create: `backend/app/models/order.py`
- Create: `backend/app/models/order_item.py`
- Test: `backend/tests/test_models.py`

**Interfaces:**
- Consumes: `app.core.config.settings`, `app.core.enums.OrderStatus`.
- Produces: `app.core.database.{engine, SessionLocal, Base, get_db}`; `app.core.redis_client.{redis_client, get_redis}`; models `User, Product, Favorite, Order, OrderItem` registered on `Base.metadata`.

- [ ] **Step 1: Write the failing tests**

Extend `backend/tests/conftest.py` — add a SQLite `db_session` fixture:
```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
import app.models  # noqa: F401  registers all models on Base.metadata


@pytest.fixture
def db_session():
    engine = create_engine(
        "sqlite:///:memory:", connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()
```

`backend/tests/test_models.py`:
```python
from decimal import Decimal

import pytest
from sqlalchemy.exc import IntegrityError

from app.core.enums import OrderStatus
from app.models import Order, Product, User


def test_product_roundtrip(db_session):
    db_session.add(Product(name="Test Phone", price_usd=Decimal("199.99"),
                           stock=5, category="phones"))
    db_session.commit()
    p = db_session.query(Product).filter_by(name="Test Phone").one()
    assert p.stock == 5
    assert p.price_usd == Decimal("199.99")


def test_only_one_temp_order_per_user(db_session):
    u = User(username="a", email="a@x.com", password_hash="h")
    db_session.add(u)
    db_session.commit()

    db_session.add(Order(user_id=u.id, status=OrderStatus.TEMP, is_temp=1))
    db_session.commit()

    db_session.add(Order(user_id=u.id, status=OrderStatus.TEMP, is_temp=1))
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_closed_orders_do_not_collide(db_session):
    u = User(username="b", email="b@x.com", password_hash="h")
    db_session.add(u)
    db_session.commit()
    # is_temp NULL for CLOSE → many allowed (NULLs are distinct in unique index)
    db_session.add(Order(user_id=u.id, status=OrderStatus.CLOSE, is_temp=None))
    db_session.add(Order(user_id=u.id, status=OrderStatus.CLOSE, is_temp=None))
    db_session.commit()
    assert db_session.query(Order).filter_by(user_id=u.id).count() == 2
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && pytest tests/test_models.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.core.database'`.

- [ ] **Step 3: Implement database + redis clients**

`backend/app/core/database.py`:
```python
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.config import settings

engine = create_engine(settings.database_url, pool_pre_ping=True, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

`backend/app/core/redis_client.py`:
```python
import redis

from app.core.config import settings

redis_client = redis.from_url(settings.redis_url, decode_responses=True)


def get_redis() -> redis.Redis:
    return redis_client
```

- [ ] **Step 4: Implement the models**

`backend/app/models/user.py`:
```python
from sqlalchemy import Boolean, Column, DateTime, Integer, String, func

from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    first_name = Column(String(80))
    last_name = Column(String(80))
    email = Column(String(120), unique=True, nullable=False, index=True)
    phone = Column(String(40))
    country = Column(String(80))
    city = Column(String(80))
    password_hash = Column(String(255), nullable=False)
    is_synthetic = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, server_default=func.now())
```

`backend/app/models/product.py`:
```python
from sqlalchemy import Column, DateTime, Integer, Numeric, String, Text, func
from sqlalchemy.types import JSON

from app.core.database import Base


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False, index=True)
    description = Column(Text)
    category = Column(String(80), index=True)
    brand = Column(String(80), index=True)
    price_usd = Column(Numeric(10, 2), nullable=False)
    stock = Column(Integer, nullable=False, default=0)
    image_url = Column(String(500))
    specs = Column(JSON)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
```

`backend/app/models/favorite.py`:
```python
from sqlalchemy import Column, DateTime, ForeignKey, Integer, UniqueConstraint, func

from app.core.database import Base


class Favorite(Base):
    __tablename__ = "favorites"
    __table_args__ = (
        UniqueConstraint("user_id", "product_id", name="uq_fav_user_product"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"),
                     nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"),
                        nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now())
```

`backend/app/models/order.py`:
```python
from sqlalchemy import (Column, DateTime, Enum, ForeignKey, Integer, Numeric,
                        SmallInteger, String, UniqueConstraint, func)
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.core.enums import OrderStatus


class Order(Base):
    __tablename__ = "orders"
    __table_args__ = (
        UniqueConstraint("user_id", "is_temp", name="uq_one_temp_per_user"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"),
                     nullable=False, index=True)
    status = Column(Enum(OrderStatus), nullable=False, default=OrderStatus.TEMP)
    is_temp = Column(SmallInteger, nullable=True)  # 1 while TEMP, NULL when CLOSE
    shipping_address = Column(String(255))
    total_price = Column(Numeric(10, 2), default=0)
    created_at = Column(DateTime, server_default=func.now())
    closed_at = Column(DateTime, nullable=True)

    items = relationship("OrderItem", back_populates="order",
                         cascade="all, delete-orphan")
```

`backend/app/models/order_item.py`:
```python
from sqlalchemy import Column, ForeignKey, Integer, Numeric, UniqueConstraint
from sqlalchemy.orm import relationship

from app.core.database import Base


class OrderItem(Base):
    __tablename__ = "order_items"
    __table_args__ = (
        UniqueConstraint("order_id", "product_id", name="uq_order_product"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"),
                      nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    quantity = Column(Integer, nullable=False, default=1)
    unit_price = Column(Numeric(10, 2), nullable=False)

    order = relationship("Order", back_populates="items")
```

`backend/app/models/__init__.py`:
```python
from app.models.favorite import Favorite
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.product import Product
from app.models.user import User

__all__ = ["User", "Product", "Favorite", "Order", "OrderItem"]
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd backend && pytest tests/test_models.py -v`
Expected: PASS (3 tests). Confirms the `UNIQUE(user_id, is_temp)` invariant.

- [ ] **Step 6: Commit**

```bash
git add backend/app/core/database.py backend/app/core/redis_client.py backend/app/models backend/tests/conftest.py backend/tests/test_models.py
git commit -m "feat(backend): db + redis clients and ORM models"
```

---

### Task 4: Readiness endpoint (DB + Redis ping)

**Files:**
- Modify: `backend/app/controllers/health.py`
- Test: `backend/tests/test_health_ready.py`

**Interfaces:**
- Consumes: `app.core.database.engine`, `app.core.redis_client.get_redis`.
- Produces: `GET /health/ready` → `{"status": "ok"|"degraded", "checks": {"database": bool, "redis": bool}}`.

- [ ] **Step 1: Write the failing integration test**

`backend/tests/test_health_ready.py`:
```python
import pytest


@pytest.mark.integration
def test_ready_when_infra_up(client):
    # Requires: docker compose up -d mysql redis
    r = client.get("/health/ready")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["checks"] == {"database": True, "redis": True}
```

- [ ] **Step 2: Run it to verify it fails**

Run: `cd backend && pytest tests/test_health_ready.py -v -m integration`
Expected: FAIL — 404 (route not defined) or connection error.

- [ ] **Step 3: Add the readiness route**

Append to `backend/app/controllers/health.py`:
```python
from sqlalchemy import text

from app.core.database import engine
from app.core.redis_client import get_redis


@router.get("/health/ready")
def ready():
    checks = {"database": False, "redis": False}
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        checks["database"] = True
    except Exception:
        pass
    try:
        get_redis().ping()
        checks["redis"] = True
    except Exception:
        pass
    status = "ok" if all(checks.values()) else "degraded"
    return {"status": status, "checks": checks}
```

- [ ] **Step 4: Bring up infra and verify it passes**

Run:
```bash
docker compose up -d mysql redis
cd backend && pytest tests/test_health_ready.py -v -m integration
```
Expected: PASS. (If MySQL is still initializing, wait ~10s and retry.)

- [ ] **Step 5: Commit**

```bash
git add backend/app/controllers/health.py backend/tests/test_health_ready.py
git commit -m "feat(backend): /health/ready checks db + redis"
```

---

### Task 5: Alembic migrations + startup migrate

**Files:**
- Create: `backend/alembic.ini`
- Create: `backend/alembic/env.py`
- Create: `backend/alembic/script.py.mako`
- Create: `backend/alembic/versions/` (dir; generated file lands here)
- Create: `backend/entrypoint.sh`

**Interfaces:**
- Consumes: `app.core.config.settings`, `app.core.database.Base`, `app.models` (registration).
- Produces: an initial migration that creates all five tables; `alembic upgrade head` builds the schema on MySQL.

- [ ] **Step 1: Initialize Alembic**

Run: `cd backend && alembic init alembic`
Expected: creates `alembic.ini`, `alembic/env.py`, `alembic/script.py.mako`, `alembic/versions/`.

- [ ] **Step 2: Point Alembic at our metadata & settings**

Replace the top of `backend/alembic/env.py` config section so `target_metadata` and the URL come from our app (leave the rest of the generated file intact):
```python
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.core.config import settings
from app.core.database import Base
import app.models  # noqa: F401  register models

config = context.config
config.set_main_option("sqlalchemy.url", settings.database_url)
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata
```
Ensure `backend/alembic.ini` has an (unused, overridden) placeholder line `sqlalchemy.url =` and that Alembic is run from the `backend/` directory so `import app` resolves.

- [ ] **Step 3: Generate the initial migration (infra required)**

Run:
```bash
docker compose up -d mysql
cd backend && alembic revision --autogenerate -m "initial schema"
```
Expected: a new file `backend/alembic/versions/xxxx_initial_schema.py` containing `create_table` for `users`, `products`, `favorites`, `orders`, `order_items`, including the unique constraints.

- [ ] **Step 4: Apply and verify**

Run: `cd backend && alembic upgrade head`
Then verify tables exist:
```bash
docker compose exec mysql mysql -ushop -pshop shopdb -e "SHOW TABLES;"
```
Expected: five tables listed. Re-running `alembic upgrade head` is a no-op.

- [ ] **Step 5: Add container entrypoint that migrates then serves**

`backend/entrypoint.sh`:
```bash
#!/usr/bin/env bash
set -e
alembic upgrade head
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
```

- [ ] **Step 6: Commit**

```bash
git add backend/alembic.ini backend/alembic backend/entrypoint.sh
git commit -m "feat(backend): alembic migrations + startup migrate"
```

---

### Task 6: Dockerize backend + full compose bring-up

**Files:**
- Create: `backend/Dockerfile`
- Create: `backend/.dockerignore`
- Modify: `docker-compose.yml` (repo root) — add `backend` service
- Create: `README.md` (repo root) — run stub

**Interfaces:**
- Consumes: `.env` at repo root; `backend/entrypoint.sh`.
- Produces: `docker-compose up --build` → `http://localhost:8000/health` returns `{"status":"ok"}` and `/health/ready` returns `ok`.

- [ ] **Step 1: Backend Dockerfile**

`backend/Dockerfile`:
```dockerfile
FROM python:3.12-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends default-mysql-client \
    && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN chmod +x entrypoint.sh
EXPOSE 8000
CMD ["./entrypoint.sh"]
```

`backend/.dockerignore`:
```
.venv/
__pycache__/
*.pyc
tests/
.pytest_cache/
```

- [ ] **Step 2: Complete `docker-compose.yml` at repo root**

```yaml
services:
  mysql:
    image: mysql:8
    environment:
      MYSQL_ROOT_PASSWORD: ${MYSQL_ROOT_PASSWORD:-root}
      MYSQL_DATABASE: ${MYSQL_DATABASE:-shopdb}
      MYSQL_USER: ${MYSQL_USER:-shop}
      MYSQL_PASSWORD: ${MYSQL_PASSWORD:-shop}
    ports: ["3306:3306"]
    volumes: ["mysql_data:/var/lib/mysql"]
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost", "-uroot", "-p${MYSQL_ROOT_PASSWORD:-root}"]
      interval: 5s
      timeout: 5s
      retries: 15

  redis:
    image: redis/redis-stack:latest
    ports: ["6379:6379", "8001:8001"]
    volumes: ["redis_data:/data"]

  backend:
    build: ./backend
    env_file: [.env]
    environment:
      DATABASE_URL: mysql+pymysql://${MYSQL_USER:-shop}:${MYSQL_PASSWORD:-shop}@mysql:3306/${MYSQL_DATABASE:-shopdb}
      REDIS_URL: redis://redis:6379/0
    ports: ["8000:8000"]
    depends_on:
      mysql:
        condition: service_healthy
      redis:
        condition: service_started

volumes:
  mysql_data:
  redis_data:
```

- [ ] **Step 3: README run stub**

`README.md` (repo root):
```markdown
# AI Shopping Website

Course final project — AI-enhanced e-commerce (FastAPI + MySQL + Redis + Docker,
Next.js UI, OpenAI agentic RAG assistant, churn-prediction ML).

## Run

    cp .env.example .env     # then paste your OPENAI_API_KEY
    docker compose up --build

- API:      http://localhost:8000
- Swagger:  http://localhost:8000/docs
- Health:   http://localhost:8000/health

See `docs/superpowers/specs/` for the design and `docs/superpowers/plans/` for the build plan.
```

- [ ] **Step 4: Full bring-up verification**

Run:
```bash
docker compose up --build -d
sleep 20
curl -s http://localhost:8000/health
curl -s http://localhost:8000/health/ready
```
Expected: `{"status":"ok"}` then `{"status":"ok","checks":{"database":true,"redis":true}}`.
The backend log shows `alembic upgrade head` ran before uvicorn started.

- [ ] **Step 5: Commit**

```bash
git add backend/Dockerfile backend/.dockerignore docker-compose.yml README.md
git commit -m "feat: dockerize backend + full compose bring-up"
```

---

## Definition of Done (Phase 1)

- [ ] `pytest` (backend) green for config, enums, health, models (SQLite).
- [ ] `docker compose up --build` starts MySQL + Redis + backend.
- [ ] Migrations create all five tables on MySQL automatically at startup.
- [ ] `/health` = ok; `/health/ready` = ok with db+redis true.
- [ ] `UNIQUE(user_id, is_temp)` one-TEMP-per-user invariant verified by test.

**Next phase:** Phase 2 — Auth (register/login/me, bcrypt, JWT, cascade delete).
