# AI Shopping Website — Design Spec

**Course:** AI final project (10-month AI course)
**Author:** Adir Buskila
**Date:** 2026-07-09
**Deadline:** 2026-08-01
**Status:** Approved design → ready for implementation plan

---

## 1. Overview & Goals

Build a full end-to-end e-commerce shopping website whose emphasis is the **AI
capabilities and the backend**, per the course brief. The customer can browse a
product catalog, search/filter, keep favorites, place and manage orders with
live stock control, and talk to an **agentic AI shopping assistant** grounded in
the real inventory (RAG). A supervised **churn-prediction** model (bonus) is
trained on a provided dataset and served via a dedicated API.

**Non-code reuse from `mobileforyou`:** we reuse its *domain model*, its *real
product catalog* (phones + accessories, with images), and its *Next.js
storefront UI*. We do **not** reuse its backend — that is rebuilt in the
mandated Python stack. (The stacks are incompatible, so "no copy-paste" is
automatic for the backend.)

### Success criteria
1. Every requirement in the course brief is demonstrably satisfied (see §2).
2. `docker-compose up` starts the whole system (MySQL + Redis + backend + frontend).
3. The AI assistant answers grounded, stock-aware questions and can *act* via tools.
4. The churn model + its training dataset are in the repo and served via an API.
5. One professional GitHub repository with a clear README.

---

## 2. Requirements Traceability

The graded brief maps to the design as follows. This table is the definition of done.

| # | Brief requirement | Where satisfied |
|---|---|---|
| a | Pages: Main, Order, Favorites, Chat | Next.js frontend pages |
| b | Main page: heading, search area, items grid | `/` page |
| c | Items list from DB as dataframe; filter by name/stock/price; item shows name, USD price, stock; ≥10 items | `GET /products`; catalog seeded from mobileforyou |
| d | Search bar: name substring; **multi-term OR**; **range on stock & price (`<`/`>`/`=`)**; no-result notice; result replaces the grid | `GET /products/search` |
| e | Login/register; save all user fields; **bcrypt-encrypted password**; logout → visitor view; **delete account cascades** all associated data | `auth` module + `ON DELETE CASCADE` |
| f | Favorites: per-user; add/remove; each item once; persisted across logout; dataframe view; login-only | `favorites` module |
| g | Chat assistant: ChatGPT-based; knows in-stock **and** out-of-stock products; **max 5 prompts/session** | `ai` module (RAG + agent), Redis counter |
| h | Stock: decrement on purchase; block over-order; show 0 when out; block add-when-out | `stock` service (transactional) |
| i | Orders: order id, user id, date, shipping address, total, items, quantities, **status TEMP/CLOSE**; per-user order list | `orders` module |
| j | Order process: first added item creates TEMP order; **one TEMP per user**; add/remove; totals; purchase → CLOSE + stock decrement; delete order when emptied; TEMP persists across logout; TEMP shown first & styled differently | `orders` service + frontend |
| — | Stack: **Python + FastAPI, MySQL, Redis, Docker**; MVC, config, enums, request→response, proper naming; Redis caching | whole backend |
| — | Notify the user on **every** outcome | typed API responses + frontend toasts |
| bonus | Supervised model + **provided dataset** + dedicated forecast API | `ml` module + `ml-training/` |
| — | Single GitHub repo + professional README | monorepo (§4) |

**Deviations from the brief (deliberate, with rationale):**
- **Frontend is Next.js, not Streamlit.** The brief says "the UI is not the
  important part" and lists Streamlit; we use the polished mobileforyou Next.js
  UI for a stronger result. *Mitigation:* the backend is a clean REST API, so a
  minimal Streamlit view can be added as a compliance fallback if the instructor
  requires it (tracked as an optional deliverable, not built by default).

---

## 3. Tech Stack & Key Decisions

| Concern | Choice | Rationale |
|---|---|---|
| Backend | **FastAPI** (Python 3.12) | Mandated; async, typed, auto Swagger |
| ORM / DB access | **SQLAlchemy 2.x + PyMySQL** | Clean repository layer over **MySQL 8** (mandated) |
| Migrations | **Alembic** | Reproducible schema |
| Cache + counters + vectors | **Redis (redis-stack)** | Mandated; also hosts the vector index (RediSearch), reusing required infra |
| Auth | **JWT (python-jose) + bcrypt (passlib)** | Simple, stateless, spec-compliant password encryption |
| LLM | **OpenAI ChatGPT** (`gpt-4o` class) | Matches "ChatGPT API"; native tool-calling |
| Embeddings | **OpenAI `text-embedding-3-small`** | Cheap, strong; powers RAG + semantic search |
| Agent/RAG | **Native OpenAI tool-calling + hand-written RAG** | Transparent & explainable; no framework magic |
| ML | **scikit-learn + joblib** | Course-aligned supervised learning |
| Frontend | **Next.js** (adapted from mobileforyou) | Impressive UI; talks to FastAPI |
| Packaging | **Docker + docker-compose** | Mandated; one-command run |
| Tests | **pytest** (backend), a few Playwright smoke tests (optional) | Edge-case coverage the brief asks for |

**Vector store:** abstracted behind a `VectorStore` interface. Primary
implementation uses **Redis (RediSearch KNN)**; a trivial in-process
numpy-cosine implementation exists as a zero-dependency fallback (the catalog is
small, ~30–60 products). This keeps the demo robust while reusing mandated infra.

---

## 4. Architecture & Repository Layout

Single git repository (the deliverable):

```
project-iv/
├── backend/                       # FastAPI service — the graded core (MVC)
│   ├── app/
│   │   ├── main.py                # app factory, router mounting, middleware
│   │   ├── core/                  # config (env), enums, security, db, redis, logging
│   │   ├── models/                # SQLAlchemy ORM models (M)
│   │   ├── schemas/               # Pydantic request/response DTOs
│   │   ├── repositories/          # data access over MySQL
│   │   ├── services/              # business logic (orders, stock, search, favorites)
│   │   ├── controllers/           # FastAPI routers (C — request→response)
│   │   ├── ai/                    # embeddings, vector store, retriever, agent, tools
│   │   └── ml/                    # churn model loading + prediction service
│   ├── alembic/                   # migrations
│   ├── tests/                     # pytest
│   ├── Dockerfile
│   └── pyproject.toml
├── frontend/                      # Next.js storefront (adapted from mobileforyou)
│   ├── app/ (or src/app)          # /, /orders, /favorites, /chat, /login, /register
│   ├── components/                # reused mobileforyou components
│   ├── lib/api.ts                 # typed client for the FastAPI backend
│   └── Dockerfile
├── ml-training/                   # bonus: reproducible training
│   ├── generate_dataset.py        # synthetic users/orders → labeled dataset
│   ├── train_churn.py             # trains, evaluates, saves model.joblib
│   ├── data/churn_dataset.csv     # the PROVIDED dataset (deliverable)
│   ├── model/churn_model.joblib   # trained artifact
│   └── report.md (or notebook)    # metrics: accuracy, ROC-AUC, confusion matrix
├── data/
│   └── products.seed.json         # catalog from mobileforyou → English + USD
├── scripts/
│   ├── seed_products.py           # load catalog into MySQL + build embeddings
│   └── seed_synthetic_users.py    # demo users + order history (for ML + demo realism)
├── docker-compose.yml             # mysql + redis-stack + backend + frontend
├── .env.example
└── README.md                      # professional: project, logic, stack, run steps
```

**Layering (the course's MVC):** `controller → service → repository → model`.
Controllers do HTTP only; services hold business rules; repositories own SQL;
models are the ORM entities. Config is env-driven; enums are centralized.

---

## 5. Data Model (MySQL)

```
users
  id            PK, auto-increment
  username      VARCHAR, UNIQUE, NOT NULL
  first_name    VARCHAR
  last_name     VARCHAR
  email         VARCHAR, UNIQUE, NOT NULL
  phone         VARCHAR
  country       VARCHAR
  city          VARCHAR
  password_hash VARCHAR              # bcrypt
  is_synthetic  BOOL DEFAULT 0       # seeded demo/ML users
  created_at    DATETIME

products
  id            PK
  name          VARCHAR, indexed
  description   TEXT
  category      VARCHAR
  brand         VARCHAR
  price_usd     DECIMAL(10,2)
  stock         INT                  # 0 = out of stock
  image_url     VARCHAR
  specs         JSON                 # structured attributes for RAG
  created_at / updated_at

favorites
  id            PK
  user_id       FK users(id)  ON DELETE CASCADE
  product_id    FK products(id) ON DELETE CASCADE
  created_at
  UNIQUE(user_id, product_id)         # each item once

orders
  id                PK
  user_id           FK users(id) ON DELETE CASCADE
  status            ENUM('TEMP','CLOSE')
  is_temp           TINYINT NULL       # 1 while TEMP, NULL when CLOSE
  shipping_address  VARCHAR
  total_price       DECIMAL(10,2)
  created_at
  closed_at         DATETIME NULL
  UNIQUE(user_id, is_temp)             # enforces AT MOST ONE TEMP per user
                                       # (MySQL treats NULLs as distinct)

order_items
  id            PK
  order_id      FK orders(id) ON DELETE CASCADE
  product_id    FK products(id)
  quantity      INT
  unit_price    DECIMAL(10,2)          # price snapshot at add time
  UNIQUE(order_id, product_id)
```

The `UNIQUE(user_id, is_temp)` trick enforces the "one TEMP order per user"
invariant at the database level (belt-and-suspenders with the service guard).
Cascade deletes satisfy "deleting a user removes everything associated."

---

## 6. Backend Design

### Enums (`core/enums.py`)
`OrderStatus{TEMP, CLOSE}`, `SearchOp{LT, GT, EQ}`, `Role{CUSTOMER, ADMIN}` (admin
used only for the optional insights surface), `StockResult{OK, INSUFFICIENT, OUT_OF_STOCK}`.

### Config (`core/config.py`)
Pydantic `Settings` from env: DB URL, Redis URL, JWT secret/expiry, OpenAI key,
model names, chat prompt limit (default 5), cache TTLs.

### API surface (representative)
```
Auth
  POST   /auth/register            # create account (bcrypt)
  POST   /auth/login               # → JWT
  GET    /auth/me                  # current user
  DELETE /auth/me                  # delete account (cascade)

Products / Search
  GET    /products                 # full catalog (Redis-cached)
  GET    /products/{id}
  GET    /products/search          # name (multi-term OR) + stock/price ranges
  GET    /products/semantic        # Tier-2: embedding search (used by chat & "smart search")

Favorites (auth)
  GET    /favorites
  POST   /favorites/{product_id}
  DELETE /favorites/{product_id}

Orders (auth)
  GET    /orders                   # list; TEMP first
  GET    /orders/{id}
  POST   /orders/items             # add item → creates TEMP if none
  DELETE /orders/items/{product_id}# remove item → deletes order if now empty
  POST   /orders/{id}/purchase     # → CLOSE + decrement stock (transactional)
  DELETE /orders/{id}              # delete a TEMP order

Chat (auth or session)
  POST   /chat                     # {session_id, message} → grounded answer; 5/session

ML
  GET    /ml/churn/{user_id}       # churn probability + label + top factors
```

### Redis usage (mandated caching)
- **Catalog cache:** `products:all` — the "get all items" call the brief calls
  out; invalidated on any stock/product mutation.
- **Chat limiter:** `chat:{session_id}:count` with TTL; blocks the 6th prompt.
- **Vector index:** RediSearch product-embedding index for semantic retrieval.

### Stock & order invariants (the careful part)
- **Add item:** reject if product out of stock or requested qty would exceed
  stock (`StockResult`), with a clear message.
- **Purchase:** single DB transaction with `SELECT … FOR UPDATE` on the ordered
  product rows → re-validate stock → decrement → set `CLOSE` + `closed_at` +
  frozen `total_price` → invalidate catalog cache. Prevents oversell under
  concurrency.
- **Empty TEMP:** removing the last item deletes the order.
- **Persistence:** TEMP orders live in MySQL, so they survive logout.

### Notifications
Every endpoint returns a typed envelope (`{ ok, data|error, message }`) so the
frontend can toast a specific outcome for success *and* failure — satisfying
"notify the user on any outcome."

---

## 7. AI Layer (RAG + Agentic Assistant)

**Indexing (offline/seed):** each product → a text blob (name, brand, category,
description, key specs, stock status) → `text-embedding-3-small` → stored in the
vector store keyed by product id. Re-embedded when products change.

**Retrieval (per query):** embed the user message → KNN top-k products (in- and
out-of-stock both retrievable, per the brief) → build a compact, grounded
context block including live stock.

**Agentic generation:** call ChatGPT with the retrieved context **and a tool
set** using native function-calling. If the model requests a tool, the backend
executes it and returns the result for a grounded final answer.

**Tools:**
- `search_products(query, filters)` — keyword/range search
- `semantic_search(query)` — embedding search
- `get_product_details(product_id)`
- `check_stock(product_id)`
- `recommend_similar(product_id)` — nearest-neighbor recommender
- `add_to_favorites(product_id)` — only when the user is authenticated

**Guardrails / limits:**
- **5 prompts/session** enforced in Redis; the 6th returns a clear "limit
  reached" message.
- The system prompt constrains answers to store inventory; retrieval grounds
  claims (mitigates hallucination).
- If OpenAI is unavailable/misconfigured, the endpoint returns a friendly
  "assistant is not available" message (brief requirement).

**Recommendations (Tier 2):** the same embedding index powers "similar items"
on product and favorites views via `recommend_similar`.

---

## 8. ML Bonus — Churn Prediction

**Goal:** predict whether a user will churn (stop purchasing), served via API and
surfaced as an insight.

**Dataset (provided deliverable):** `seed_synthetic_users.py` populates MySQL
with a few hundred synthetic users and realistic order histories.
`generate_dataset.py` derives a labeled table and writes
`ml-training/data/churn_dataset.csv`. A plausible data-generating process links
churn to RFM-style signals plus noise so the model has real signal to learn.

**Features (RFM + engagement):** recency (days since last order), frequency
(order count), monetary (total spend), tenure (days since signup), average order
value, favorites count. All computable live from the DB at serving time.

**Model:** scikit-learn (start with Logistic Regression for explainability;
compare against Gradient Boosting / Random Forest). Persist with joblib.
`train_churn.py` prints and saves **accuracy, ROC-AUC, precision/recall, and a
confusion matrix** to `report.md`.

**Serving:** `GET /ml/churn/{user_id}` loads the artifact once, computes the
user's live features, returns `{ probability, label, top_factors }`.

**Surface:** primarily the API + Swagger + README demo; optionally a small
"customer insight" card in a lightweight admin/insights view (stretch, not on
the critical path).

---

## 9. Frontend (Next.js, adapted from mobileforyou)

Reuse mobileforyou's component library, styling, and layout shell; repoint data
access from Supabase to the FastAPI client (`lib/api.ts`); convert to
English + USD.

**Pages:**
- `/` — **Main:** heading, search area (name multi-term + stock/price ranges),
  product grid (name, USD price, stock); results replace the grid; empty-state notice.
- `/orders` — **Order list:** TEMP order pinned first and visually distinct;
  clicking TEMP opens the order-process form (add/remove, totals, address,
  Purchase); clicking a CLOSE order shows read-only details.
- `/favorites` — grid of the user's favorites; add/remove; login-gated.
- `/chat` — chat UI: prompt history + responses; shows remaining prompts; blocks
  after 5.
- `/login`, `/register`, account menu with **logout** and **delete account**.

**Auth on the client:** JWT stored client-side; sent as `Authorization: Bearer`.
Logged-out users see the visitor view. Every action shows a toast (success/error).

---

## 10. Deployment & Run

`docker-compose.yml` services: `mysql:8`, `redis/redis-stack`, `backend`
(uvicorn), `frontend` (Next.js). `.env.example` documents required vars
(`OPENAI_API_KEY`, DB/Redis URLs, JWT secret). Canonical run:

```
cp .env.example .env    # fill OPENAI_API_KEY
docker-compose up --build
# then run scripts/seed_products.py (+ optional seed_synthetic_users.py)
```

Optional stretch: deploy frontend to Vercel + backend to a container host for a
live demo link (not required; local docker-compose is the graded path).

---

## 11. Testing & Edge Cases

pytest coverage for the invariants that matter:
- Register/login, bcrypt hash never stored in plaintext, JWT required on guarded routes.
- Search: multi-term OR, each range operator (`<`/`>`/`=`) on stock and price, empty-result path.
- Stock: cannot add out-of-stock; cannot exceed stock; purchase decrements; oversell blocked under concurrency.
- Orders: one TEMP per user; empty TEMP auto-deleted; purchase → CLOSE; CLOSE is read-only.
- Favorites: uniqueness; login-gating; persistence.
- Chat: 5-prompt cap; graceful "unavailable" path; out-of-stock product is answerable.
- Account deletion cascades favorites + orders + order_items.

---

## 12. Deliverables Checklist

- [ ] Single GitHub repo, professional README (project, logic, stack, run steps, screenshots).
- [ ] `docker-compose up` brings up the full system.
- [ ] All §2 requirements implemented and manually verified.
- [ ] Agentic RAG assistant with tools + 5-prompt limit.
- [ ] Churn model + **`churn_dataset.csv`** + training script/report + serving API.
- [ ] Product catalog seeded (≥10, actually ~30–60 real items) with embeddings.
- [ ] Test suite passing.

---

## 13. Timeline (→ 2026-08-01)

| Window | Focus |
|---|---|
| Week 1 (Jul 9–15) | Repo + docker-compose skeleton; DB schema + Alembic; config/enums; auth; products + keyword/range search; catalog seed (mobileforyou → English/USD). |
| Week 2 (Jul 16–22) | Favorites; orders + stock invariants (TEMP/CLOSE, purchase txn); frontend wiring of Main/Orders/Favorites + auth; notifications. |
| Week 3 (Jul 23–29) | Embeddings + vector store; agentic chat + tools + 5-prompt limit; recommendations; churn dataset + model + serving; insight surface. |
| Jul 30–Aug 1 | Edge-case hardening, tests, README, screenshots, final Docker run-through, submit. |

---

## 14. Prerequisites & Risks

- **OpenAI API key with a little credit** (embeddings + chat). Small cost.
- **Redis Stack** image for vector search (numpy fallback de-risks this).
- **Scope discipline:** admin/insights UI and live cloud deploy are explicitly
  optional; the critical path is the brief's requirements + Tier-2 AI + churn bonus.

---

## 15. Out of Scope (YAGNI — dropped from mobileforyou)

Real payment gateway (Takbull/Stripe) — "purchase" just closes the order and
decrements stock; real transactional email; Hebrew/RTL; full admin panel;
multi-currency; product reviews; delivery-driver flows. These add no graded
value and cost time.
