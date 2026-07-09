# AI Shopping Website

Course final project — an AI-enhanced e-commerce shop. FastAPI + MySQL + Redis +
Docker backend, a Next.js storefront, an OpenAI **agentic RAG** shopping
assistant, and a **churn-prediction** ML model.

## Run

```bash
cp .env.example .env      # then paste your OPENAI_API_KEY into .env
docker compose up --build
```

- API:      http://localhost:8000
- Swagger:  http://localhost:8000/docs
- Health:   http://localhost:8000/health

## Documentation

- Design spec: `docs/superpowers/specs/`
- Build plans: `docs/superpowers/plans/`

## Tech Stack

Python 3.12 · FastAPI · SQLAlchemy · MySQL 8 · Redis · Alembic · Docker Compose ·
OpenAI (chat + embeddings) · scikit-learn · Next.js.
