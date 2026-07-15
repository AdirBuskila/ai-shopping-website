# Phase 9 — Polish & Submit Implementation Plan

> **For agentic workers:** Execute task-by-task. Steps use checkbox (`- [ ]`) syntax.

**Goal:** Make the whole project run with a single `docker compose up` (storefront + API +
AI + ML), ship a professional README with screenshots, and verify the whole thing from a
clean slate — ready for submission.

**Architecture:** Add a production `frontend` container (Next.js standalone build) to the
existing compose stack (mysql + redis + backend). The browser calls the API at
`http://localhost:8000` (CORS already allows the web origin), so no network rewrites needed.

**Tech Stack:** Next.js standalone output, multi-stage Docker build (node:22-alpine), the
existing FastAPI/MySQL/Redis/Docker stack.

## Global Constraints

- One command — `docker compose up --build` — must serve everything; no host steps.
- Keep the catalog auto-seeded (already) and document the one-time AI embedding + ML seed.
- README must be professional: what it is, screenshots, architecture, features, run steps,
  tech stack, testing. English.
- All commits under Adir's name, no co-author trailers.

---

### Task 1: Dockerize the frontend

**Files:**
- Modify: `frontend/next.config.ts` (`output: "standalone"`)
- Create: `frontend/Dockerfile`, `frontend/.dockerignore`
- Modify: `docker-compose.yml` (add `frontend` service)

- [ ] **Step 1:** Set `output: "standalone"` in `next.config.ts` so the build emits a
      self-contained server.
- [ ] **Step 2:** Multi-stage `frontend/Dockerfile`: `deps` (npm ci) → `builder`
      (npm run build) → `runner` (copy `.next/standalone`, `.next/static`, `public`; run
      `node server.js` on port 3000).
- [ ] **Step 3:** `frontend/.dockerignore` (node_modules, .next, .git).
- [ ] **Step 4:** Add the `frontend` service to `docker-compose.yml`
      (`build: ./frontend`, `ports: ["3000:3000"]`, `depends_on: [backend]`).
- [ ] **Step 5:** `docker compose up --build` → open http://localhost:3000, confirm the
      store loads and talks to the API. **Commit** `feat(docker): serve the Next.js storefront in compose`.

---

### Task 2: Professional README + screenshots

**Files:**
- Create: `docs/screenshots/*.png` (home, product, chat, orders)
- Rewrite: `README.md`

- [ ] **Step 1:** Capture screenshots of the running app (home, product page, AI chat, orders).
- [ ] **Step 2:** Rewrite `README.md`: one-paragraph pitch, a screenshot, the one-command run,
      the AI/ML one-time steps, feature list, architecture (MVC + AI + ML + web), tech stack,
      project layout, testing, and a link to the design/plan docs.
- [ ] **Step 3:** **Commit** `docs: professional README with screenshots`.

---

### Task 3: Final clean-slate verification

- [ ] **Step 1:** Full backend suite green (`pytest`); frontend `next build` green.
- [ ] **Step 2:** `docker compose down -v && docker compose up --build` from scratch;
      confirm: catalog auto-seeds, storefront serves, `embed_products.py` + `seed_synthetic_users.py`
      make chat + churn demoable, a full click-through works.
- [ ] **Step 3:** Git hygiene — clean tree, all commits under Adir's name, no secrets, no
      Claude trailers. Merge to `main`, push. **Commit** any fixes found.

---

## Definition of Done (Phase 9)

- [ ] `docker compose up --build` serves the storefront (:3000) + API (:8000) together.
- [ ] Professional README with screenshots, run steps, architecture, and features.
- [ ] Whole app verified from a clean `down -v` slate.
- [ ] All tests green; pushed to `main` under Adir's name.

**This is the final phase — after it, the project is submission-ready.**
