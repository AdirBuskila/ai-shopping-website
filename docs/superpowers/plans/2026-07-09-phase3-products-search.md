# Phase 3 — Products & Search Implementation Plan

> **For agentic workers:** Execute task-by-task with TDD. Steps use checkbox (`- [ ]`) syntax.

**Goal:** Seed a real catalog (from mobileforyou, → English + USD) into MySQL, expose a Redis-cached `GET /products` + `GET /products/{id}`, and a `GET /products/search` supporting multi-term OR name search and range filters (`< > =`) on stock and price.

**Architecture:** New product slice on the MVC stack — `schemas/product.py`, `repositories/product_repository.py`, `services/product_service.py`, `controllers/products.py`. Redis caching is **injectable** via `Depends(get_redis)` so unit tests can override it with a no-op fake (avoids cross-test cache contamination). Data prep is a reproducible script that writes a committed seed file.

**Tech Stack:** SQLAlchemy queries (`ilike`, `or_`), Redis (list cache), Pydantic response schema.

## Global Constraints

- Catalog is **English + USD**. Conversion rate **ILS→USD = 0.27** (documented constant); prices rounded to 2 decimals.
- `data/products.seed.json` is committed so the repo is **self-contained** (no dependency on mobileforyou at runtime).
- Product names are **unique** (dedupe in the transform) so seeding is idempotent by name.
- Search: name match is **case-insensitive substring**, multiple terms = **OR**; stock/price use operators from the `SearchOp` enum (`<`,`>`,`=`); no results → empty list + HTTP 200 (frontend notifies).
- Redis caching must **degrade gracefully** — a Redis error falls back to the DB, never 500s.

---

### Task 1: Build the committed seed dataset

**Files:**
- Create: `scripts/__init__.py` (empty), `scripts/build_seed_from_mobileforyou.py`
- Create (generated + committed): `data/products.seed.json`

**Transform** each mobileforyou item → our schema:
- `name` = `"{brand} {model}"` + (` {storage}` if storage not in {N/A, "", None}) + (` (Refurbished)` if condition == refurbished). Dedupe: skip exact-duplicate names.
- `description` = `description_en` if present, else synthesized: `"{name} — a {condition} {category} by {brand}."`
- `category`, `brand` = as-is; `price_usd` = `round(price * 0.27, 2)`; `stock` = as-is.
- `image_url` = as-is (relative path; images wired in Phase 8) or null.
- `specs` = `{model, storage, condition, category, tags, is_best_seller, is_promotion}` (structured, for RAG in Phase 6).

- [ ] **Step 1: Write `scripts/build_seed_from_mobileforyou.py`:**
  ```python
  import json, pathlib

  SRC = r"C:/Users/Adir/Desktop/Coding/Dev/mobileforyou/data/products.json"
  OUT = pathlib.Path(__file__).resolve().parents[1] / "data" / "products.seed.json"
  ILS_TO_USD = 0.27


  def build_name(x):
      storage = x.get("storage")
      name = f"{x['brand']} {x['model']}"
      if storage and storage not in ("N/A", "", None):
          name += f" {storage}"
      if x.get("condition") == "refurbished":
          name += " (Refurbished)"
      return name


  def main():
      src = json.load(open(SRC, encoding="utf-8"))
      out, seen = [], set()
      for x in src:
          if not isinstance(x.get("price"), (int, float)):
              continue
          name = build_name(x)
          if name in seen:
              continue
          seen.add(name)
          desc = x.get("description_en") or (
              f"{name} — a {x.get('condition','new')} {x.get('category','device')} by {x['brand']}."
          )
          out.append({
              "name": name,
              "description": desc,
              "category": x.get("category"),
              "brand": x.get("brand"),
              "price_usd": round(x["price"] * ILS_TO_USD, 2),
              "stock": int(x.get("stock", 0)),
              "image_url": x.get("image_url"),
              "specs": {
                  "model": x.get("model"), "storage": x.get("storage"),
                  "condition": x.get("condition"), "category": x.get("category"),
                  "tags": x.get("tags", []),
                  "is_best_seller": x.get("is_best_seller", False),
                  "is_promotion": x.get("is_promotion", False),
              },
          })
      OUT.parent.mkdir(exist_ok=True)
      json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
      print(f"wrote {len(out)} products to {OUT}")


  if __name__ == "__main__":
      main()
  ```
- [ ] **Step 2: Run it** — `cd backend && ../` … run: `.venv/Scripts/python.exe ../scripts/build_seed_from_mobileforyou.py`
  Expect: `wrote ~140+ products`. Sanity-check `data/products.seed.json` has English names + USD prices.
- [ ] **Step 3: Commit** `data/products.seed.json` + the script → `chore(data): build English/USD product seed from source catalog`.

---

### Task 2: Product schema + repository

**Files:**
- Create: `backend/app/schemas/product.py`
- Create: `backend/app/repositories/product_repository.py`
- Test: `backend/tests/test_product_repo.py`

**Interfaces:**
- Produces: `ProductPublic` schema; `ProductRepository(db)` with `list_all()`, `get(id)`, `get_by_name(name)`, `search(q, stock_op, stock_value, price_op, price_value)`.

- [ ] **Step 1: Schema** — `schemas/product.py`:
  ```python
  from pydantic import BaseModel, ConfigDict


  class ProductPublic(BaseModel):
      model_config = ConfigDict(from_attributes=True)
      id: int
      name: str
      brand: str | None = None
      category: str | None = None
      price_usd: float
      stock: int
      image_url: str | None = None
      description: str | None = None
  ```

- [ ] **Step 2: Failing test** — `test_product_repo.py`:
  ```python
  from decimal import Decimal
  from app.core.enums import SearchOp
  from app.models import Product
  from app.repositories.product_repository import ProductRepository

  def _seed(db):
      db.add_all([
          Product(name="Apple iPhone 13", brand="Apple", category="smartphone", price_usd=Decimal("499"), stock=5),
          Product(name="Sun Table Lamp", brand="Ikea", category="accessory", price_usd=Decimal("40"), stock=20),
          Product(name="Samsung Galaxy", brand="Samsung", category="smartphone", price_usd=Decimal("300"), stock=0),
      ]); db.commit()

  def test_multi_term_or_name_search(db_session):
      _seed(db_session); repo = ProductRepository(db_session)
      names = {p.name for p in repo.search("iphone, sun", None, None, None, None)}
      assert names == {"Apple iPhone 13", "Sun Table Lamp"}

  def test_stock_greater_than(db_session):
      _seed(db_session); repo = ProductRepository(db_session)
      names = {p.name for p in repo.search(None, SearchOp.GT, 10, None, None)}
      assert names == {"Sun Table Lamp"}

  def test_price_less_than(db_session):
      _seed(db_session); repo = ProductRepository(db_session)
      names = {p.name for p in repo.search(None, None, None, SearchOp.LT, 350)}
      assert names == {"Sun Table Lamp", "Samsung Galaxy"}

  def test_no_match_returns_empty(db_session):
      _seed(db_session); repo = ProductRepository(db_session)
      assert repo.search("zzz", None, None, None, None) == []
  ```

- [ ] **Step 2b: Run — expect fail.**

- [ ] **Step 3: Implement repository** — `repositories/product_repository.py`:
  ```python
  import re
  from sqlalchemy import or_
  from sqlalchemy.orm import Session

  from app.core.enums import SearchOp
  from app.models import Product


  class ProductRepository:
      def __init__(self, db: Session):
          self.db = db

      def list_all(self) -> list[Product]:
          return self.db.query(Product).order_by(Product.id).all()

      def get(self, product_id: int) -> Product | None:
          return self.db.get(Product, product_id)

      def get_by_name(self, name: str) -> Product | None:
          return self.db.query(Product).filter(Product.name == name).first()

      def _cmp(self, col, op: SearchOp, val):
          if op == SearchOp.LT:
              return col < val
          if op == SearchOp.GT:
              return col > val
          return col == val

      def search(self, q, stock_op, stock_value, price_op, price_value) -> list[Product]:
          query = self.db.query(Product)
          if q:
              terms = [t for t in re.split(r"[,\s]+", q.strip()) if t]
              if terms:
                  query = query.filter(or_(*[Product.name.ilike(f"%{t}%") for t in terms]))
          if stock_op and stock_value is not None:
              query = query.filter(self._cmp(Product.stock, stock_op, stock_value))
          if price_op and price_value is not None:
              query = query.filter(self._cmp(Product.price_usd, price_op, price_value))
          return query.order_by(Product.id).all()
  ```

- [ ] **Step 4: Run — expect pass** (4 tests). **Commit** `feat(products): schema + repository with search`.

---

### Task 3: Seeder + load into MySQL

**Files:**
- Create: `scripts/seed_products.py`
- Test: `backend/tests/test_seeder.py`

**Interfaces:**
- Produces: `seed_products(db, items: list[dict]) -> int` (idempotent by name; returns count inserted/updated).

- [ ] **Step 1: Failing test** — `test_seeder.py`:
  ```python
  from scripts.seed_products import seed_products
  from app.models import Product

  ITEMS = [{"name": "X Phone", "description": "d", "category": "smartphone",
            "brand": "X", "price_usd": 100, "stock": 3, "image_url": None, "specs": {}}]

  def test_seed_inserts(db_session):
      n = seed_products(db_session, ITEMS)
      assert n == 1
      assert db_session.query(Product).filter_by(name="X Phone").one().stock == 3

  def test_seed_is_idempotent(db_session):
      seed_products(db_session, ITEMS)
      seed_products(db_session, [{**ITEMS[0], "stock": 9}])
      rows = db_session.query(Product).filter_by(name="X Phone").all()
      assert len(rows) == 1 and rows[0].stock == 9   # updated, not duplicated
  ```

- [ ] **Step 2: Implement** — `scripts/seed_products.py`:
  ```python
  import json, pathlib

  from app.core.database import SessionLocal
  from app.models import Product
  from app.repositories.product_repository import ProductRepository

  SEED = pathlib.Path(__file__).resolve().parents[1] / "data" / "products.seed.json"


  def seed_products(db, items) -> int:
      repo = ProductRepository(db)
      for it in items:
          existing = repo.get_by_name(it["name"])
          if existing:
              existing.stock = it["stock"]
              existing.price_usd = it["price_usd"]
              existing.description = it.get("description")
              existing.image_url = it.get("image_url")
              existing.specs = it.get("specs")
          else:
              db.add(Product(
                  name=it["name"], description=it.get("description"),
                  category=it.get("category"), brand=it.get("brand"),
                  price_usd=it["price_usd"], stock=it["stock"],
                  image_url=it.get("image_url"), specs=it.get("specs"),
              ))
      db.commit()
      return len(items)


  def main():
      items = json.load(open(SEED, encoding="utf-8"))
      db = SessionLocal()
      try:
          print("seeded", seed_products(db, items), "products")
      finally:
          db.close()


  if __name__ == "__main__":
      main()
  ```

- [ ] **Step 3: Run tests — pass.** **Step 4: Load MySQL** (containers up): from `backend/`,
  `DATABASE_URL=mysql+pymysql://shop:shop@localhost:3306/shopdb .venv/Scripts/python.exe ../scripts/seed_products.py`
  Then verify: `docker exec projectiv-mysql-1 mysql -ushop -pshop shopdb -e "SELECT COUNT(*) FROM products;"`
- [ ] **Step 5: Commit** `feat(products): idempotent seeder`.

---

### Task 4: GET /products (Redis-cached) + GET /products/{id}

**Files:**
- Create: `backend/app/services/product_service.py`, `backend/app/controllers/products.py`
- Modify: `backend/app/main.py` (mount), `backend/tests/conftest.py` (override `get_redis` with a no-op fake)
- Test: `backend/tests/test_products_api.py`

**Interfaces:**
- Produces: `ProductService(db, cache).list_all() -> list[dict]`, `.get(id)`; `GET /products`, `GET /products/{id}`.

- [ ] **Step 1: conftest — override `get_redis`** with a fake so tests never touch real Redis:
  ```python
  # add to conftest.py imports:
  from app.core.redis_client import get_redis

  class _FakeCache:
      def get(self, k): return None
      def setex(self, k, ttl, v): pass

  # in the client fixture, after dependency_overrides[get_db] = ...:
      app.dependency_overrides[get_redis] = lambda: _FakeCache()
  ```

- [ ] **Step 2: Failing test** — `test_products_api.py`:
  ```python
  from decimal import Decimal
  from app.models import Product

  def _seed(db):
      db.add(Product(name="Apple iPhone 13", brand="Apple", category="smartphone",
                     price_usd=Decimal("499.00"), stock=5, image_url="/x.jpg",
                     description="d")); db.commit()

  def test_list_products(client, db_session):
      _seed(db_session)
      r = client.get("/products")
      assert r.status_code == 200
      body = r.json(); assert len(body) == 1
      assert body[0]["name"] == "Apple iPhone 13"
      assert body[0]["price_usd"] == 499.0 and body[0]["stock"] == 5

  def test_get_product_by_id(client, db_session):
      _seed(db_session)
      pid = db_session.query(Product).one().id
      assert client.get(f"/products/{pid}").json()["name"] == "Apple iPhone 13"

  def test_get_missing_product_404(client):
      assert client.get("/products/999").status_code == 404
  ```

- [ ] **Step 3: Implement service** — `services/product_service.py`:
  ```python
  import json

  from fastapi import HTTPException, status

  from app.repositories.product_repository import ProductRepository
  from app.schemas.product import ProductPublic

  CACHE_KEY = "products:all"
  CACHE_TTL = 300


  class ProductService:
      def __init__(self, db, cache=None):
          self.repo = ProductRepository(db)
          self.cache = cache

      def _serialize(self, products):
          return [ProductPublic.model_validate(p).model_dump(mode="json") for p in products]

      def list_all(self):
          if self.cache:
              try:
                  hit = self.cache.get(CACHE_KEY)
                  if hit:
                      return json.loads(hit)
              except Exception:
                  pass
          data = self._serialize(self.repo.list_all())
          if self.cache:
              try:
                  self.cache.setex(CACHE_KEY, CACHE_TTL, json.dumps(data))
              except Exception:
                  pass
          return data

      def get(self, product_id: int):
          p = self.repo.get(product_id)
          if not p:
              raise HTTPException(status.HTTP_404_NOT_FOUND, "Product not found")
          return ProductPublic.model_validate(p).model_dump(mode="json")

      def search(self, q, stock_op, stock_value, price_op, price_value):
          return self._serialize(
              self.repo.search(q, stock_op, stock_value, price_op, price_value)
          )
  ```

- [ ] **Step 4: Controller** — `controllers/products.py` ( `/search` declared before `/{product_id}` ):
  ```python
  from fastapi import APIRouter, Depends
  from sqlalchemy.orm import Session

  from app.core.database import get_db
  from app.core.enums import SearchOp
  from app.core.redis_client import get_redis
  from app.schemas.product import ProductPublic
  from app.services.product_service import ProductService

  router = APIRouter(prefix="/products", tags=["products"])


  @router.get("", response_model=list[ProductPublic])
  def list_products(db: Session = Depends(get_db), cache=Depends(get_redis)):
      return ProductService(db, cache).list_all()


  @router.get("/search", response_model=list[ProductPublic])
  def search_products(
      q: str | None = None,
      stock_op: SearchOp | None = None,
      stock_value: int | None = None,
      price_op: SearchOp | None = None,
      price_value: float | None = None,
      db: Session = Depends(get_db),
  ):
      return ProductService(db).search(q, stock_op, stock_value, price_op, price_value)


  @router.get("/{product_id}", response_model=ProductPublic)
  def get_product(product_id: int, db: Session = Depends(get_db)):
      return ProductService(db).get(product_id)
  ```
  Mount in `main.py`: `from app.controllers import auth, health, products` + `app.include_router(products.router)`.

- [ ] **Step 5: Run — pass** (3 tests). **Commit** `feat(products): cached list + detail endpoints`.

---

### Task 5: GET /products/search endpoint tests

**Files:**
- Test: `backend/tests/test_products_search.py` (endpoint-level; repo logic already covered)

- [ ] **Step 1: Tests** — `test_products_search.py`:
  ```python
  from decimal import Decimal
  from app.models import Product

  def _seed(db):
      db.add_all([
          Product(name="Apple iPhone 13", brand="Apple", category="smartphone", price_usd=Decimal("499"), stock=5),
          Product(name="Sun Table Lamp", brand="Ikea", category="accessory", price_usd=Decimal("40"), stock=20),
          Product(name="Samsung Galaxy", brand="Samsung", category="smartphone", price_usd=Decimal("300"), stock=0),
      ]); db.commit()

  def test_search_multi_term(client, db_session):
      _seed(db_session)
      names = {p["name"] for p in client.get("/products/search", params={"q": "iphone, sun"}).json()}
      assert names == {"Apple iPhone 13", "Sun Table Lamp"}

  def test_search_stock_range(client, db_session):
      _seed(db_session)
      r = client.get("/products/search", params={"stock_op": ">", "stock_value": 10})
      assert {p["name"] for p in r.json()} == {"Sun Table Lamp"}

  def test_search_price_range(client, db_session):
      _seed(db_session)
      r = client.get("/products/search", params={"price_op": "<", "price_value": 350})
      assert {p["name"] for p in r.json()} == {"Sun Table Lamp", "Samsung Galaxy"}

  def test_search_empty_result_is_200_empty(client, db_session):
      _seed(db_session)
      r = client.get("/products/search", params={"q": "zzz"})
      assert r.status_code == 200 and r.json() == []
  ```

- [ ] **Step 2: Run — pass** (endpoints already implemented in Task 4). **Commit** `test(products): search endpoint coverage`.

---

## Definition of Done (Phase 3)

- [ ] `data/products.seed.json` committed (English + USD, ~140+ real items).
- [ ] MySQL seeded; `SELECT COUNT(*) FROM products` matches.
- [ ] `GET /products` returns the catalog (Redis-cached, degrades gracefully); `GET /products/{id}` 200/404.
- [ ] `GET /products/search`: multi-term OR name, `<`/`>`/`=` on stock & price, empty → 200 `[]`.
- [ ] Full suite green + smoke test against live MySQL/Redis.
- [ ] Pushed to `main` under Adir's name.

**Next phase:** Phase 4 — Favorites.
