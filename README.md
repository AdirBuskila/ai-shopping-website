# 🛍️ Shopwise — an AI-powered e-commerce store

A full-stack electronics store where the **backend and the AI are the stars**: browse a real
151-product catalog, search and filter, keep favorites, build a cart and check out with live
stock control, and chat with an **agentic AI assistant** that actually knows the inventory
(RAG) and can take actions. Plus a bonus **churn-prediction** ML model served over the API.

**Stack:** FastAPI · MySQL · Redis · Docker · OpenAI (chat + embeddings) · scikit-learn ·
Next.js.

![Shopwise storefront](docs/screenshots/home.png)

---

## Run it (one command)

```bash
cp .env.example .env      # paste your OPENAI_API_KEY into .env
docker compose up --build
```

That starts **everything** — MySQL, Redis, the FastAPI API, and the Next.js storefront —
runs database migrations, and **auto-seeds the catalog (151 real products)**.

| Surface | URL |
|---|---|
| 🛍️ Storefront | http://localhost:3000 |
| ⚙️ API | http://localhost:8000 |
| 📖 Swagger (interactive API) | http://localhost:8000/docs |

**Two one-time steps to light up the AI + ML demos:**

```bash
docker compose exec backend python scripts/embed_products.py       # build the chat's vector index
docker compose exec backend python scripts/seed_synthetic_users.py # customers for the churn demo
```

(The chat index also builds lazily on first use. The assistant needs a real `OPENAI_API_KEY`;
without one, `/chat` returns a friendly "unavailable" message and the rest of the app is
unaffected.)

---

## Features

**Store**
- 151 real products (name, USD price, live stock) in a responsive grid
- Search: name **multi-term OR**, plus **range filters** on stock & price (`<` `>` `=`)
- Favorites (login-gated, unique, persisted), product detail pages
- Cart → checkout: **one TEMP order per user**, transactional purchase with **no overselling**
  (`SELECT … FOR UPDATE`), auto-delete emptied cart, order history
- Register / login / logout / delete-account (bcrypt + JWT), toast feedback on every action

**AI assistant** (the centerpiece)
- **RAG** grounded in the live catalog via a **Redis vector index** (VSS, cosine KNN)
- **Agentic tool-calling** (native OpenAI functions): search, semantic search, product
  details, live stock, recommend-similar, add-to-favorites
- Recommends **only in-stock** products and pivots to in-stock alternatives; **5 prompts/session**
  cap (Redis); graceful degradation when OpenAI is off

**ML bonus**
- `GET /ml/churn/{user_id}` — explainable churn probability from live RFM features
  (Logistic Regression vs Random Forest, ROC-AUC ≈ 0.85, per-user reason codes)

<p align="center">
  <img src="docs/screenshots/chat.png" width="49%" alt="AI shopping assistant" />
  <img src="docs/screenshots/product.png" width="49%" alt="Product page" />
</p>

---

## Architecture

```
┌────────────┐   HTTP/JSON   ┌────────────────────────────┐
│  Next.js   │──────────────▶│  FastAPI  (MVC)            │
│  storefront│   Bearer JWT  │  controllers → services →  │
│  :3000     │◀──────────────│  repositories → models     │
└────────────┘               └───────┬─────────┬──────────┘
                                     │         │
                          ┌──────────▼───┐ ┌───▼──────────┐
                          │  MySQL 8     │ │  Redis        │
                          │  truth       │ │  cache +      │
                          │  (catalog,   │ │  vector index │
                          │  orders…)    │ │  + prompt cap │
                          └──────────────┘ └───────────────┘
                                     ▲
                          ┌──────────┴───────────┐
                          │  OpenAI (chat +       │
                          │  text-embedding-3)    │
                          └───────────────────────┘
```

- **Backend** — FastAPI with a clean **MVC** layering (controllers → services →
  repositories → models), SQLAlchemy + Alembic, Pydantic schemas, centralized enums/config.
- **MySQL = truth, Redis = speed.** Redis caches the catalog, holds the vector index, and
  enforces the per-session prompt cap.
- **AI** — a hand-written RAG + agent loop (no LangChain); every OpenAI touchpoint is
  injectable, so the whole thing is unit-tested offline.
- **Frontend** — Next.js 16 / React 19 / Tailwind, JWT in `localStorage`, cart/favorites
  React contexts.

## Project layout

```
backend/        FastAPI app (app/), tests/, Dockerfile, migrations
  app/ai/       embeddings, Redis vector store, tools, the agent assistant
  app/ml/       churn features + model serving
frontend/       Next.js storefront (src/app, src/components, src/context)
ml_training/    synthetic dataset generator + churn training + report
data/           products.seed.json (151 products)
scripts/        seed_products, embed_products, seed_synthetic_users
docs/           design spec, per-phase plans, screenshots
```

## Testing

```bash
cd backend && pytest              # 98 unit tests (SQLite; OpenAI mocked)
pytest -m integration             # Redis VSS test (needs the stack up)
cd ../frontend && npm run build   # type-check + production build
```

Backend logic is covered by **98 tests**; the AI and ML layers were also verified with live
smokes (grounded chat + tool calls, churn scoring across 300 seeded users).

## Documentation

- Design spec & per-phase build plans: `docs/superpowers/`
- The build was done in nine documented phases (foundation → auth → catalog → favorites →
  orders → **AI** → **ML** → **frontend** → polish).
