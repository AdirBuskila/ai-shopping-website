# Phase 5 — Orders & Stock Implementation Plan

> **For agentic workers:** Execute task-by-task with TDD. Steps use checkbox (`- [ ]`) syntax.

**Goal:** A logged-in user has exactly one live shopping cart (a **TEMP** order). Adding
the first item creates it; items can be added/removed with live totals; buying it turns
it **CLOSE**, decrements stock in one transaction (no overselling), and frees the slot
for a new cart. Emptying the cart deletes it. TEMP orders live in MySQL, so they survive
logout. Closed orders are read-only history.

**Architecture:** A new orders slice — `repositories/order_repository.py`,
`services/order_service.py`, `controllers/orders.py`, `schemas/order.py` — reusing the
Phase 2 auth dependency, the Phase 3 `ProductRepository`, and the Phase 3 catalog cache
(invalidated on purchase because stock changes).

**Tech Stack:** SQLAlchemy transactions + `with_for_update()` row locks (real locks on
MySQL, silently ignored on the SQLite test DB — same code path, correct behavior),
the `UNIQUE(user_id, is_temp)` DB invariant from Phase 1, `StockResult` enum for
stock-check outcomes.

## Global Constraints

- All order routes require a valid JWT (`Depends(get_current_user)`) → 401 otherwise.
- **One TEMP per user** (DB `UNIQUE(user_id, is_temp)`, `is_temp=1` while TEMP,
  `NULL` when CLOSE → many CLOSE orders allowed, at most one TEMP).
- **Add item:** first add auto-creates the TEMP order. Adding a product already in the
  cart **increments** its quantity. Reject if the product is out of stock
  (`OUT_OF_STOCK`) or the resulting quantity exceeds stock (`INSUFFICIENT`) → `409`
  with a clear message. Nothing is written when rejected.
- **Remove item:** removes the line; removing the **last** line **deletes the order**
  (returns `null`). Live total recomputed on every mutation.
- **Purchase:** single transaction — lock each ordered product row (`FOR UPDATE`),
  re-validate stock, decrement, set `CLOSE` + `closed_at` + `is_temp=NULL`, save the
  shipping address, invalidate the catalog cache. Empty order or already-closed → `409`.
- **Delete order:** only a TEMP order can be deleted (`204`); deleting a CLOSE order →
  `409`. CLOSE orders are otherwise read-only.
- **Ownership:** a user only ever sees/acts on their own orders (others → `404`).
- **Listing:** TEMP first, then newest CLOSE orders.

---

### Task 1: Order schemas + `OrderItem.product` relationship

**Files:**
- Create: `backend/app/schemas/order.py`
- Modify: `backend/app/models/order_item.py` (add `product` relationship for display name)

**Interfaces:**
- `OrderItemPublic{product_id, name, quantity, unit_price, line_total}`
- `OrderPublic{id, user_id, status, shipping_address, total_price, created_at, closed_at, items}`
- `AddItemRequest{product_id, quantity>=1 (default 1)}`
- `PurchaseRequest{shipping_address?}`

- [ ] **Step 1:** Add `product = relationship("Product")` to `OrderItem` (ORM-only,
      no migration — used to show the product name in an order line).
- [ ] **Step 2:** Write `schemas/order.py` with the four models above.

---

### Task 2: Order repository (TDD)

**Files:**
- Create: `backend/app/repositories/order_repository.py`
- Test: `backend/tests/test_order_repo.py`

**Interfaces:** `OrderRepository(db)`:
`get(order_id)`, `get_temp(user_id)`, `create_temp(user_id)`,
`list_for_user(user_id)` (TEMP first), `get_item(order_id, product_id)`, `delete(order)`.

- [ ] **Step 1: Failing test** — create TEMP, `get_temp` finds it, second `create` is
      avoided by the service (repo just persists), `list_for_user` returns TEMP first,
      `get_item` finds/does-not-find, `delete` removes it (cascades items).
- [ ] **Step 2: Run — expect fail** (module missing).
- [ ] **Step 3: Implement repository.**
- [ ] **Step 4: Run — pass.**

---

### Task 3: Order service + endpoints (TDD through the API)

**Files:**
- Create: `backend/app/services/order_service.py`, `backend/app/controllers/orders.py`
- Modify: `backend/app/main.py` (mount), `backend/tests/conftest.py` (`_FakeCache.delete`)
- Test: `backend/tests/test_orders_api.py`

**Interfaces:** `OrderService(db, cache=None)`:
`list(user_id)`, `get(user_id, order_id)`, `add_item(user_id, product_id, qty)`,
`remove_item(user_id, product_id)`, `purchase(user_id, order_id, shipping_address)`,
`delete(user_id, order_id)`.

**Endpoints (all auth):**
```
GET    /orders                      # list; TEMP first
POST   /orders/items                # add → creates TEMP if none      (201)
DELETE /orders/items/{product_id}   # remove → deletes order if empty (null when empty)
POST   /orders/{order_id}/purchase  # → CLOSE + decrement stock
GET    /orders/{order_id}           # one order (owner only)
DELETE /orders/{order_id}           # delete a TEMP order             (204)
```
> Literal `/items` routes are declared **before** `/{order_id}` routes so `items`
> is never captured as an id.

- [ ] **Step 1: Failing tests** — `test_orders_api.py` covering every invariant:
  login-gate (401); first add auto-creates TEMP; duplicate add increments; multi-product
  total; out-of-stock → 409; over-stock (direct + via increment) → 409; remove updates
  total; remove last → order deleted (`null`); one TEMP per user; TEMP survives a new
  login token; purchase → CLOSE + stock decremented + address saved; purchase empty →
  409; purchase again → 409; purchase blocks later over-order; delete TEMP → 204; delete
  CLOSE → 409; cross-user access → 404; list shows TEMP first.
- [ ] **Step 2: Run — expect fail** (routes missing).
- [ ] **Step 3: Implement** service (stock rules via `StockResult`, purchase txn with
      `with_for_update()`, cache invalidation), controller, mount, `_FakeCache.delete`.
- [ ] **Step 4: Run — pass.**

---

## Definition of Done (Phase 5)

- [ ] All order routes require login (401 otherwise).
- [ ] First add creates the TEMP order; duplicate add increments; totals are live.
- [ ] Cannot add out-of-stock or beyond stock (409, clear message).
- [ ] Removing the last item deletes the order; exactly one TEMP per user.
- [ ] Purchase closes the order, decrements stock transactionally (no oversell), saves
      the address, and invalidates the catalog cache; a later over-order is blocked.
- [ ] CLOSE orders are read-only; only TEMP orders are deletable.
- [ ] TEMP survives logout (persisted in MySQL); orders are per-user isolated.
- [ ] Full suite green + smoke test against live MySQL.
- [ ] Pushed to `main` under Adir's name.

**Next phase:** Phase 6 — the AI layer (embeddings + Redis vector store + agentic RAG
assistant, 5-prompt cap).
