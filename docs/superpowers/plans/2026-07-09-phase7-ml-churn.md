# Phase 7 — ML Bonus: Churn Prediction Implementation Plan

> **For agentic workers:** Execute task-by-task with TDD. Steps use checkbox (`- [ ]`) syntax.

**Goal:** A supervised model that predicts whether a customer will churn (stop buying),
served at `GET /ml/churn/{user_id}` with an *explainable* answer
(`{probability, label, top_factors}`), computed from the user's **live** RFM + engagement
features in MySQL.

**Architecture:** One canonical feature definition (`app/ml/features.py`) is shared by both
training and serving, so there's **no train/serve skew**. A self-contained
class-conditional data-generating process (`ml-training/generate_dataset.py`) writes a
labeled CSV with real, overlapping signal; `train_churn.py` trains + evaluates
(Logistic Regression vs Random Forest), persists the best model with joblib, and writes a
metrics `report.md`. `seed_synthetic_users.py` backdates users/orders/favorites into MySQL
so the endpoint has realistic rows to score.

**Tech Stack:** scikit-learn (LogisticRegression, RandomForest, StandardScaler), joblib,
pandas/numpy, the existing SQLAlchemy models.

## Global Constraints

- **Features (canonical order, one source of truth in `app/ml/features.py`):**
  `recency_days, frequency, monetary, tenure_days, avg_order_value, favorites_count`.
  - `frequency` / `monetary` count **CLOSE** orders only (real purchases).
  - `recency_days` = days since the last CLOSE order; if none, falls back to `tenure_days`.
  - `avg_order_value` = `monetary / frequency` (0 when `frequency == 0`).
- **Explainable:** `top_factors` are the standardized logistic contributions
  (`coef × scaled_value`), ranked by magnitude, each labeled as raising/lowering risk.
- **Reproducible:** fixed random seed in dataset generation and training. Commit the CSV,
  `report.md`, and the `.joblib` artifact so a grader can run the endpoint without retraining.
- **Artifact location:** `backend/app/ml/artifacts/churn_model.joblib` (inside the backend
  package → copied into the Docker image and loaded once at serving time).
- **Graceful:** if the artifact is missing, `GET /ml/churn/{user_id}` returns `503` with a
  clear "model not trained" message; unknown user → `404`.

---

### Task 1: Canonical feature computation (live from MySQL)

**Files:**
- Create: `backend/app/ml/__init__.py`, `backend/app/ml/features.py`
- Test: `backend/tests/test_ml_features.py`

**Interfaces:**
- Produces: `FEATURE_NAMES: list[str]`; `compute_features(db, user_id) -> dict[str, float]`;
  `feature_vector(features: dict) -> list[float]` (values in `FEATURE_NAMES` order).

- [ ] **Step 1: Failing test** — `test_ml_features.py` seeds a user with one CLOSE order and
  a favorite, asserts frequency=1, monetary=order total, favorites_count=1, avg_order_value=total.
  ```python
  from datetime import datetime, timedelta
  from decimal import Decimal
  from app.core.enums import OrderStatus
  from app.models import Favorite, Order, OrderItem, Product, User
  from app.ml.features import FEATURE_NAMES, compute_features, feature_vector

  def test_features_for_a_buyer(db_session):
      u = User(username="a", email="a@x.com", password_hash="h",
               created_at=datetime.utcnow() - timedelta(days=100))
      p = Product(name="Phone", price_usd=Decimal("500"), stock=5)
      db_session.add_all([u, p]); db_session.commit()
      o = Order(user_id=u.id, status=OrderStatus.CLOSE, is_temp=None,
                total_price=Decimal("500"),
                created_at=datetime.utcnow() - timedelta(days=10),
                closed_at=datetime.utcnow() - timedelta(days=10))
      db_session.add(o); db_session.commit()
      db_session.add(OrderItem(order_id=o.id, product_id=p.id, quantity=1,
                               unit_price=Decimal("500")))
      db_session.add(Favorite(user_id=u.id, product_id=p.id)); db_session.commit()

      f = compute_features(db_session, u.id)
      assert f["frequency"] == 1
      assert f["monetary"] == 500.0
      assert f["avg_order_value"] == 500.0
      assert f["favorites_count"] == 1
      assert 8 <= f["recency_days"] <= 12
      assert len(feature_vector(f)) == len(FEATURE_NAMES)

  def test_features_for_non_buyer(db_session):
      u = User(username="b", email="b@x.com", password_hash="h",
               created_at=datetime.utcnow() - timedelta(days=200))
      db_session.add(u); db_session.commit()
      f = compute_features(db_session, u.id)
      assert f["frequency"] == 0 and f["monetary"] == 0.0
      assert f["avg_order_value"] == 0.0
      assert f["recency_days"] == f["tenure_days"]  # never bought → recency = tenure
  ```

- [ ] **Step 2: Run — expect fail.**
- [ ] **Step 3: Implement** `features.py`: `FEATURE_NAMES` constant; `compute_features`
  queries CLOSE orders (count, sum total_price, max closed_at/created_at), user.created_at,
  favorites count; derives the six values; `feature_vector` maps a dict → ordered list.
- [ ] **Step 4: Run — pass.** **Commit** `feat(ml): live churn feature computation`.

---

### Task 2: Synthetic dataset generation (class-conditional DGP)

**Files:**
- Create: `ml-training/generate_dataset.py`, `ml-training/__init__.py`
- Test: `backend/tests/test_dataset_gen.py`

**Interfaces:**
- Produces: `sample_rows(n, seed) -> list[dict]` (each row has the six features + `churn`).

- [ ] **Step 1: Failing test** — assert the DGP has real signal and both classes:
  ```python
  from ml_training.generate_dataset import sample_rows

  def test_dataset_has_signal_and_both_classes():
      rows = sample_rows(400, seed=42)
      churn = [r for r in rows if r["churn"] == 1]
      keep = [r for r in rows if r["churn"] == 0]
      assert 0 < len(churn) < 400 and len(keep) > 0
      avg = lambda xs, k: sum(r[k] for r in xs) / len(xs)
      # churners buy less and were seen longer ago
      assert avg(churn, "frequency") < avg(keep, "frequency")
      assert avg(churn, "recency_days") > avg(keep, "recency_days")
  ```
  (Test imports `ml_training` — add `ml-training` to `pythonpath` in `pyproject.toml`, or
  keep the package importable as `ml_training`.)

- [ ] **Step 2: Run — expect fail.**
- [ ] **Step 3: Implement** `generate_dataset.py`:
  - `sample_rows(n, seed)`: for each user draw `churn ~ Bernoulli(0.4)`, then draw features
    **class-conditionally** with overlap (churners: higher `recency_days`, lower
    `frequency`/`monetary`/`favorites_count`; keepers: the reverse), `avg_order_value =
    monetary/max(frequency,1)`, all clipped to sane ranges via a seeded `numpy` RNG.
  - `main()`: write `ml-training/data/churn_dataset.csv` (columns = FEATURE_NAMES + `churn`).
- [ ] **Step 4: Run — pass.** Run `python ml-training/generate_dataset.py` to write the CSV.
  **Commit** `feat(ml): synthetic churn dataset generator + data`.

---

### Task 3: Training + evaluation + artifact

**Files:**
- Create: `ml-training/train_churn.py`
- Generated: `ml-training/report.md`, `backend/app/ml/artifacts/churn_model.joblib`
- Test: `backend/tests/test_churn_artifact.py`

- [ ] **Step 1: Implement** `train_churn.py`:
  - Load the CSV, split train/test (stratified, fixed seed).
  - Pipeline `StandardScaler → LogisticRegression`; also fit a `RandomForestClassifier`;
    pick the higher test ROC-AUC.
  - Print + write to `report.md`: accuracy, ROC-AUC, precision/recall/F1, confusion matrix,
    and the logistic coefficients (feature importances).
  - `joblib.dump({"model", "scaler", "features": FEATURE_NAMES, "kind"}, artifact_path)`.
- [ ] **Step 2: Run** `python ml-training/train_churn.py` → writes `report.md` + the artifact.
- [ ] **Step 3: Test** — `test_churn_artifact.py` loads the artifact and asserts it predicts:
  ```python
  import joblib, pathlib
  ART = pathlib.Path("app/ml/artifacts/churn_model.joblib")

  def test_artifact_loads_and_predicts():
      bundle = joblib.load(ART)
      assert bundle["features"]
      # a clear churner profile scores higher than a clear keeper
      from app.ml.churn_model import predict_from_vector
      churner = [180, 0, 0, 300, 0, 0]
      keeper = [5, 12, 4000, 300, 333, 6]
      assert predict_from_vector(churner)["probability"] > \
             predict_from_vector(keeper)["probability"]
  ```
- [ ] **Step 4: Run — pass.** **Commit**
  `feat(ml): train + evaluate churn model (LogReg vs RF) + report + artifact`.

---

### Task 4: Model serving wrapper

**Files:**
- Create: `backend/app/ml/churn_model.py`
- Test: covered by `test_churn_artifact.py` (Task 3) + `test_ml_api.py` (Task 5)

**Interfaces:**
- Produces: `predict_from_vector(vec: list[float]) -> {probability, label, top_factors}`;
  `is_ready() -> bool`.

- [ ] **Step 1:** Implement lazy singleton load of the joblib bundle (`is_ready()` False when
  the file is absent). `predict_from_vector` scales the vector, calls
  `predict_proba`, thresholds at 0.5 for `label`, and builds `top_factors` from
  `coef × scaled_value` (top 3 by |contribution|, each `{feature, direction}`). For the RF
  fallback, derive `top_factors` from `feature_importances_`.
- [ ] **Step 2:** Green via Task 3's test. **Commit** `feat(ml): explainable churn prediction wrapper`.

---

### Task 5: `GET /ml/churn/{user_id}` endpoint

**Files:**
- Create: `backend/app/controllers/ml.py`, `backend/app/schemas/ml.py`
- Modify: `backend/app/main.py` (mount)
- Test: `backend/tests/test_ml_api.py`

**Interfaces:**
- `GET /ml/churn/{user_id}` → `{user_id, probability, label, top_factors, features}`.
  Unknown user → `404`; artifact missing → `503`.

- [ ] **Step 1: Failing test** — seed a user, assert 200 + a probability in `[0,1]` + a label;
  unknown id → 404.
  ```python
  def test_churn_for_user(client, db_session):
      # seed a buyer (as in test_ml_features) ...
      r = client.get(f"/ml/churn/{uid}")
      assert r.status_code == 200
      body = r.json()
      assert 0.0 <= body["probability"] <= 1.0
      assert body["label"] in ("churn", "retain")
      assert len(body["top_factors"]) >= 1

  def test_churn_unknown_user_404(client):
      assert client.get("/ml/churn/999999").status_code == 404
  ```

- [ ] **Step 2: Run — expect fail.**
- [ ] **Step 3: Implement** `schemas/ml.py` (`ChurnResponse`), `controllers/ml.py`
  (`ChurnService`-free: load user → 404 if missing; `is_ready()` else 503;
  `compute_features` → `feature_vector` → `predict_from_vector`; return the response), mount
  `ml.router` in `main.py`.
- [ ] **Step 4: Run — pass.** **Commit** `feat(ml): GET /ml/churn/{user_id} serving endpoint`.

---

### Task 6: Seed synthetic users into MySQL (demo realism)

**Files:**
- Create: `backend/scripts/seed_synthetic_users.py`
- Modify: `backend/requirements.txt` (add `scikit-learn`, `joblib`, `pandas`)

- [ ] **Step 1:** Implement `seed_synthetic_users.py` (path detection like `seed_products.py`):
  insert ~300 users with **backdated** `created_at`, a class-conditional number of **CLOSE**
  orders (backdated `created_at`/`closed_at`, real product ids, correct `total_price`) and
  favorites — so the endpoint scores realistic, varied users. Idempotent by a `synthetic_`
  username prefix.
- [ ] **Step 2:** Add the deps; `pip install -r requirements.txt`.
- [ ] **Step 3:** Run against live MySQL; spot-check a few `GET /ml/churn/{id}` responses.
  **Commit** `feat(ml): synthetic user/order seeder for churn demo`.

---

## Definition of Done (Phase 7)

- [ ] `generate_dataset.py` writes a labeled CSV with real, learnable signal (both classes).
- [ ] `train_churn.py` trains LogReg vs RF, writes `report.md` (accuracy, ROC-AUC,
      precision/recall, confusion matrix) and the joblib artifact.
- [ ] `GET /ml/churn/{user_id}` returns `{probability, label, top_factors}` from live
      features; unknown user → 404; missing artifact → 503.
- [ ] Serving and training share one feature definition (no skew).
- [ ] `seed_synthetic_users.py` populates MySQL so the endpoint is demonstrable.
- [ ] Full suite green + a live smoke against MySQL.
- [ ] Pushed to `main` under Adir's name.

**Next phase:** Phase 8 — the Next.js storefront (the visual reveal): Main, Orders, Favorites,
Chat, and auth, adapted from mobileforyou.
