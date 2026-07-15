# AI Shopping Website

Course final project — an AI-enhanced e-commerce shop. FastAPI + MySQL + Redis +
Docker backend, a Next.js storefront, an OpenAI **agentic RAG** shopping
assistant, and a **churn-prediction** ML model.

## Run

```bash
cp .env.example .env      # then paste your OPENAI_API_KEY into .env
docker compose up --build
```

That single command starts MySQL + Redis + the API, **runs database migrations,
and auto-seeds the catalog (151 products)** — no extra steps.

- API:      http://localhost:8000
- Swagger:  http://localhost:8000/docs
- Health:   http://localhost:8000/health
- Products: http://localhost:8000/products
- Chat:     `POST http://localhost:8000/chat` — the AI shopping assistant

### AI assistant (RAG + tools)

The `/chat` assistant is grounded in the catalog via a **Redis vector index**. The
index builds **lazily on the first chat request**, or you can build it up front:

```bash
docker compose exec backend python scripts/embed_products.py
```

It needs a real `OPENAI_API_KEY` in `.env`; without one, `/chat` returns a friendly
"assistant unavailable" message (the rest of the API is unaffected).

### Churn prediction (ML bonus)

`GET /ml/churn/{user_id}` returns `{probability, label, top_factors}` from the user's
live RFM + engagement features. The trained model ships in the repo
(`backend/app/ml/artifacts/churn_model.joblib`); to reproduce it:

```bash
python ml_training/generate_dataset.py   # synthetic labeled data -> data/churn_dataset.csv
python ml_training/train_churn.py         # LogReg vs RF -> report.md + artifact
```

For a populated demo, seed synthetic customers with order history:

```bash
docker compose exec backend python scripts/seed_synthetic_users.py
```

## Storefront (Next.js)

A polished storefront (Shop, Favorites, Orders/checkout, and an AI Chat page) lives in
`frontend/`. With the backend running (`docker compose up`), start it:

```bash
cd frontend
npm install
npm run dev        # http://localhost:3000
```

The API allows CORS from `http://localhost:3000` by default. Set
`NEXT_PUBLIC_API_URL` if the backend runs elsewhere.

## Documentation

- Design spec: `docs/superpowers/specs/`
- Build plans: `docs/superpowers/plans/`

## Tech Stack

Python 3.12 · FastAPI · SQLAlchemy · MySQL 8 · Redis · Alembic · Docker Compose ·
OpenAI (chat + embeddings) · scikit-learn · Next.js.
