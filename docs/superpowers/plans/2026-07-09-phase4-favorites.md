# Phase 4 — Favorites Implementation Plan

> **For agentic workers:** Execute task-by-task with TDD. Steps use checkbox (`- [ ]`) syntax.

**Goal:** A logged-in user can add/remove products to a personal favorites list (each item once, persisted), and view it as products. All routes are login-gated.

**Architecture:** A thin favorites slice reusing existing pieces — `repositories/favorite_repository.py`, `services/favorite_service.py`, `controllers/favorites.py`. Responses reuse `ProductPublic`; auth reuses `get_current_user`; product existence reuses `ProductRepository`.

**Tech Stack:** SQLAlchemy join query, the Phase 2 auth dependency, the Phase 3 product schema.

## Global Constraints

- All three endpoints require a valid JWT (`Depends(get_current_user)`) → 401 otherwise.
- **Uniqueness:** a product appears at most once per user (DB `UNIQUE(user_id, product_id)` + service check). Adding a duplicate is a **no-op**, not an error.
- Favorites are **per-user isolated** and **persisted** (survive logout — they live in MySQL).
- List/add/remove all return the user's current favorites as `list[ProductPublic]` (frontend refreshes in one call).
- Adding a non-existent product → 404. Removing a non-favorited product → no-op.

---

### Task 1: Favorite repository + service

**Files:**
- Create: `backend/app/repositories/favorite_repository.py`, `backend/app/services/favorite_service.py`
- Test: `backend/tests/test_favorite_repo.py`

**Interfaces:**
- `FavoriteRepository(db)`: `exists(user_id, product_id) -> bool`, `add(user_id, product_id)`, `remove(user_id, product_id)`, `list_products(user_id) -> list[Product]`.
- `FavoriteService(db)`: `list(user_id) -> list[dict]`, `add(user_id, product_id) -> list[dict]`, `remove(user_id, product_id) -> list[dict]`.

- [ ] **Step 1: Failing test** — `test_favorite_repo.py`:
  ```python
  from decimal import Decimal
  from app.models import Product, User
  from app.repositories.favorite_repository import FavoriteRepository

  def _uid_pid(db):
      u = User(username="a", email="a@x.com", password_hash="h")
      p = Product(name="Apple iPhone 13", price_usd=Decimal("499"), stock=5)
      db.add_all([u, p]); db.commit()
      return u.id, p.id

  def test_add_exists_list_remove(db_session):
      uid, pid = _uid_pid(db_session)
      repo = FavoriteRepository(db_session)
      assert repo.exists(uid, pid) is False
      repo.add(uid, pid)
      assert repo.exists(uid, pid) is True
      assert [p.id for p in repo.list_products(uid)] == [pid]
      repo.remove(uid, pid)
      assert repo.list_products(uid) == []
  ```

- [ ] **Step 2: Run — expect fail.**

- [ ] **Step 3: Implement repository** — `repositories/favorite_repository.py`:
  ```python
  from sqlalchemy.orm import Session

  from app.models import Favorite, Product


  class FavoriteRepository:
      def __init__(self, db: Session):
          self.db = db

      def exists(self, user_id: int, product_id: int) -> bool:
          return (
              self.db.query(Favorite)
              .filter_by(user_id=user_id, product_id=product_id)
              .first()
              is not None
          )

      def add(self, user_id: int, product_id: int) -> None:
          self.db.add(Favorite(user_id=user_id, product_id=product_id))
          self.db.commit()

      def remove(self, user_id: int, product_id: int) -> None:
          self.db.query(Favorite).filter_by(
              user_id=user_id, product_id=product_id
          ).delete()
          self.db.commit()

      def list_products(self, user_id: int) -> list[Product]:
          return (
              self.db.query(Product)
              .join(Favorite, Favorite.product_id == Product.id)
              .filter(Favorite.user_id == user_id)
              .order_by(Product.id)
              .all()
          )
  ```

- [ ] **Step 4: Implement service** — `services/favorite_service.py`:
  ```python
  from fastapi import HTTPException, status

  from app.repositories.favorite_repository import FavoriteRepository
  from app.repositories.product_repository import ProductRepository
  from app.schemas.product import ProductPublic


  class FavoriteService:
      def __init__(self, db):
          self.favs = FavoriteRepository(db)
          self.products = ProductRepository(db)

      def list(self, user_id: int):
          return [
              ProductPublic.model_validate(p).model_dump(mode="json")
              for p in self.favs.list_products(user_id)
          ]

      def add(self, user_id: int, product_id: int):
          if not self.products.get(product_id):
              raise HTTPException(status.HTTP_404_NOT_FOUND, "Product not found")
          if not self.favs.exists(user_id, product_id):
              self.favs.add(user_id, product_id)  # idempotent: skip if present
          return self.list(user_id)

      def remove(self, user_id: int, product_id: int):
          self.favs.remove(user_id, product_id)
          return self.list(user_id)
  ```

- [ ] **Step 5: Run — pass.** **Commit** `feat(favorites): repository + service`.

---

### Task 2: Favorites endpoints (login-gated)

**Files:**
- Create: `backend/app/controllers/favorites.py`
- Modify: `backend/app/main.py` (mount)
- Test: `backend/tests/test_favorites_api.py`

**Interfaces:**
- `GET /favorites`, `POST /favorites/{product_id}` (201), `DELETE /favorites/{product_id}` — all return `list[ProductPublic]`.

- [ ] **Step 1: Failing tests** — `test_favorites_api.py`:
  ```python
  from decimal import Decimal
  from app.models import Product

  def _headers(client, username="adir"):
      client.post("/auth/register", json=dict(username=username, password="pw12345", email=f"{username}@x.com"))
      tok = client.post("/auth/login", json=dict(username=username, password="pw12345")).json()["access_token"]
      return {"Authorization": f"Bearer {tok}"}

  def _product(db, name="Apple iPhone 13"):
      p = Product(name=name, brand="Apple", category="smartphone", price_usd=Decimal("499"), stock=5)
      db.add(p); db.commit(); return p.id

  def test_favorites_require_login(client):
      assert client.get("/favorites").status_code == 401
      assert client.post("/favorites/1").status_code == 401
      assert client.delete("/favorites/1").status_code == 401

  def test_add_then_list(client, db_session):
      h = _headers(client); pid = _product(db_session)
      r = client.post(f"/favorites/{pid}", headers=h)
      assert r.status_code == 201
      assert [p["id"] for p in r.json()] == [pid]
      assert [p["id"] for p in client.get("/favorites", headers=h).json()] == [pid]

  def test_add_is_unique(client, db_session):
      h = _headers(client); pid = _product(db_session)
      client.post(f"/favorites/{pid}", headers=h)
      body = client.post(f"/favorites/{pid}", headers=h).json()
      assert [p["id"] for p in body] == [pid]  # still once

  def test_remove(client, db_session):
      h = _headers(client); pid = _product(db_session)
      client.post(f"/favorites/{pid}", headers=h)
      assert client.delete(f"/favorites/{pid}", headers=h).json() == []

  def test_add_missing_product_404(client):
      h = _headers(client)
      assert client.post("/favorites/999", headers=h).status_code == 404

  def test_favorites_isolated_per_user(client, db_session):
      pid = _product(db_session)
      ha = _headers(client, "usera"); hb = _headers(client, "userb")
      client.post(f"/favorites/{pid}", headers=ha)
      assert client.get("/favorites", headers=hb).json() == []
  ```

- [ ] **Step 2: Run — expect fail.**

- [ ] **Step 3: Implement controller** — `controllers/favorites.py`:
  ```python
  from fastapi import APIRouter, Depends, status
  from sqlalchemy.orm import Session

  from app.core.database import get_db
  from app.core.deps import get_current_user
  from app.models import User
  from app.schemas.product import ProductPublic
  from app.services.favorite_service import FavoriteService

  router = APIRouter(prefix="/favorites", tags=["favorites"])


  @router.get("", response_model=list[ProductPublic])
  def list_favorites(current: User = Depends(get_current_user), db: Session = Depends(get_db)):
      return FavoriteService(db).list(current.id)


  @router.post("/{product_id}", response_model=list[ProductPublic],
               status_code=status.HTTP_201_CREATED)
  def add_favorite(product_id: int, current: User = Depends(get_current_user),
                   db: Session = Depends(get_db)):
      return FavoriteService(db).add(current.id, product_id)


  @router.delete("/{product_id}", response_model=list[ProductPublic])
  def remove_favorite(product_id: int, current: User = Depends(get_current_user),
                      db: Session = Depends(get_db)):
      return FavoriteService(db).remove(current.id, product_id)
  ```
  Mount in `main.py`: add `favorites` to the import and `app.include_router(favorites.router)`.

- [ ] **Step 4: Run — pass.** **Commit** `feat(favorites): login-gated add/remove/list endpoints`.

---

## Definition of Done (Phase 4)

- [ ] All favorites routes require login (401 otherwise).
- [ ] Add → product appears; adding twice keeps it once; remove clears it.
- [ ] Adding a missing product → 404.
- [ ] Favorites are per-user isolated and persisted (survive re-login).
- [ ] Full suite green + smoke test against live MySQL.
- [ ] Pushed to `main` under Adir's name.

**Next phase:** Phase 5 — Orders & Stock (the trickiest: TEMP/CLOSE, purchase transaction, oversell prevention).
