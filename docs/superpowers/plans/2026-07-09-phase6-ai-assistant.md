# Phase 6 — AI Layer (RAG + Agentic Assistant) Implementation Plan

> **For agentic workers:** Execute task-by-task with TDD. Steps use checkbox (`- [ ]`) syntax.

**Goal:** A ChatGPT-powered shopping assistant that is *grounded* in our live catalog
(RAG over a **Redis vector index**) and can *act* through native OpenAI function-calling
tools (search, stock, recommend, favorite). Capped at 5 prompts/session, and it degrades
gracefully when OpenAI is unavailable.

**Architecture:** A new `app/ai/` package, one file per job. Embeddings (`text-embedding-3-small`)
are stored in a Redis **VSS** index (`FLOAT32[1536]`, COSINE, exact FLAT KNN). A per-request
pipeline: cap-check → embed the message → KNN top-k → load *live* rows from MySQL → build a
grounded context → call ChatGPT with a tool set → run any tool calls → final answer. All
OpenAI touchpoints are injectable so unit tests never call the network.

**Tech Stack:** OpenAI Python SDK (chat + embeddings), Redis Stack vector search via
`redis-py` FT commands, NumPy (float32 vector encoding), the Phase 3 catalog + Phase 4
favorites reused as tools.

## Global Constraints

- OpenAI only (course brief mandates the ChatGPT API). Model ids come from `settings`:
  `openai_chat_model` (`gpt-4o-mini`), `openai_embedding_model` (`text-embedding-3-small`).
- **5 prompts/session** (`settings.chat_prompt_limit`), enforced in Redis; the 6th returns a
  clear "limit reached" message **without** calling OpenAI.
- **Grounded, honest, stock-aware:** answers constrained to our inventory; both in-stock and
  out-of-stock products are retrievable; stock is always read **live** from MySQL, never from
  the vector.
- **Graceful degradation:** if the OpenAI key is missing/placeholder or a call fails, return a
  friendly "assistant is unavailable" reply (HTTP 200, `available: false`) — never a 500.
- **No LangChain** — the RAG pipeline and agent loop are hand-written.
- **Embeddings are not built at `docker up`** (cost/placeholder-key). Built once via
  `scripts/embed_products.py`, or lazily on first chat if the index is empty.
- Every OpenAI seam (`embed`, `embed_many`, chat completion) is injectable → unit tests mock
  them; a live smoke exercises the real thing.

---

### Task 1: Dependencies + embeddings client

**Files:**
- Modify: `backend/requirements.txt` (add `openai`, `numpy`)
- Create: `backend/app/ai/__init__.py` (empty), `backend/app/ai/embeddings.py`
- Test: `backend/tests/test_embeddings.py`

**Interfaces:**
- Produces: `is_configured() -> bool`, `embed(text: str) -> list[float]`,
  `embed_many(texts: list[str]) -> list[list[float]]`.

- [ ] **Step 1: Add deps** to `requirements.txt`: `openai` and `numpy`. `pip install -r requirements.txt`.

- [ ] **Step 2: Failing test** — `test_embeddings.py` (tests only the pure `is_configured`
  logic; network calls are never made in unit tests):
  ```python
  from app.ai import embeddings

  def test_is_configured_false_for_placeholder(monkeypatch):
      monkeypatch.setattr(embeddings.settings, "openai_api_key", "sk-REPLACE_ME")
      assert embeddings.is_configured() is False

  def test_is_configured_true_for_real_key(monkeypatch):
      monkeypatch.setattr(embeddings.settings, "openai_api_key", "sk-proj-abc123")
      assert embeddings.is_configured() is True
  ```

- [ ] **Step 3: Run — expect fail** (module missing).

- [ ] **Step 4: Implement** `app/ai/embeddings.py`:
  ```python
  from openai import OpenAI

  from app.core.config import settings

  _client = None


  def _get_client() -> OpenAI:
      global _client
      if _client is None:
          _client = OpenAI(api_key=settings.openai_api_key)
      return _client


  def is_configured() -> bool:
      key = settings.openai_api_key or ""
      return bool(key) and not key.startswith("sk-REPLACE")


  def embed(text: str) -> list[float]:
      resp = _get_client().embeddings.create(
          model=settings.openai_embedding_model, input=text)
      return resp.data[0].embedding


  def embed_many(texts: list[str]) -> list[list[float]]:
      out: list[list[float]] = []
      for i in range(0, len(texts), 100):           # OpenAI batch-size safety
          chunk = texts[i:i + 100]
          resp = _get_client().embeddings.create(
              model=settings.openai_embedding_model, input=chunk)
          out.extend(d.embedding for d in resp.data)
      return out
  ```

- [ ] **Step 5: Run — pass.** **Commit** `feat(ai): openai embeddings client + deps`.

---

### Task 2: Redis vector store (VSS) + product text + indexer

**Files:**
- Create: `backend/app/ai/product_text.py`, `backend/app/ai/vector_store.py`,
  `backend/app/ai/indexer.py`, `backend/scripts/embed_products.py`
- Test: `backend/tests/test_product_text.py`, `backend/tests/test_vector_store.py` (integration)

**Interfaces:**
- Produces:
  - `build_blob(product) -> str`
  - `VectorStore(redis)`: `ensure_index()`, `is_empty() -> bool`, `upsert(product_id, vector, name)`,
    `knn(query_vector, k, exclude_id=None) -> list[int]`, `clear()`
  - `build_index(db, store, embed_many_fn=embed_many) -> int`

- [ ] **Step 1: Failing test** — `test_product_text.py`:
  ```python
  from decimal import Decimal
  from app.models import Product
  from app.ai.product_text import build_blob

  def test_blob_includes_name_brand_and_stock():
      p = Product(name="Apple iPhone 13", brand="Apple", category="smartphone",
                  description="A great phone", price_usd=Decimal("499"), stock=0,
                  specs={"storage": "128GB"})
      blob = build_blob(p)
      assert "Apple iPhone 13" in blob
      assert "Apple" in blob
      assert "storage" in blob and "128GB" in blob
      assert "Out of stock" in blob
  ```

- [ ] **Step 2: Run — expect fail.**

- [ ] **Step 3: Implement** `app/ai/product_text.py`:
  ```python
  def build_blob(product) -> str:
      parts = [product.name]
      if product.brand:
          parts.append(f"Brand: {product.brand}")
      if product.category:
          parts.append(f"Category: {product.category}")
      if product.description:
          parts.append(product.description)
      if product.specs:
          parts.append("Specs: " + ", ".join(
              f"{k}: {v}" for k, v in product.specs.items()))
      parts.append("In stock" if (product.stock or 0) > 0 else "Out of stock")
      return " | ".join(parts)
  ```

- [ ] **Step 4: Implement** `app/ai/vector_store.py` (real Redis Stack VSS):
  ```python
  import numpy as np
  from redis.commands.search.field import NumericField, TextField, VectorField
  from redis.commands.search.indexDefinition import IndexDefinition, IndexType
  from redis.commands.search.query import Query

  DIM = 1536  # text-embedding-3-small


  def _to_bytes(vector) -> bytes:
      return np.asarray(vector, dtype=np.float32).tobytes()


  class VectorStore:
      INDEX = "idx:products"
      PREFIX = "product:vec:"

      def __init__(self, redis):
          self.r = redis

      def ensure_index(self) -> None:
          try:
              self.r.ft(self.INDEX).info()
              return                                    # already exists
          except Exception:
              pass
          schema = (
              VectorField("embedding", "FLAT",
                          {"TYPE": "FLOAT32", "DIM": DIM, "DISTANCE_METRIC": "COSINE"}),
              NumericField("product_id"),
              TextField("name"),
          )
          definition = IndexDefinition(prefix=[self.PREFIX], index_type=IndexType.HASH)
          self.r.ft(self.INDEX).create_index(schema, definition=definition)

      def is_empty(self) -> bool:
          try:
              return int(self.r.ft(self.INDEX).info()["num_docs"]) == 0
          except Exception:
              return True

      def upsert(self, product_id: int, vector, name: str) -> None:
          self.r.hset(f"{self.PREFIX}{product_id}", mapping={
              "product_id": product_id, "name": name, "embedding": _to_bytes(vector)})

      def knn(self, query_vector, k: int, exclude_id: int | None = None) -> list[int]:
          n = k + (1 if exclude_id is not None else 0)
          q = (Query(f"*=>[KNN {n} @embedding $vec AS score]")
               .sort_by("score").return_fields("product_id", "score").dialect(2))
          res = self.r.ft(self.INDEX).search(
              q, query_params={"vec": _to_bytes(query_vector)})
          ids = [int(doc.product_id) for doc in res.docs]
          if exclude_id is not None:
              ids = [i for i in ids if i != exclude_id]
          return ids[:k]

      def clear(self) -> None:
          for key in self.r.scan_iter(f"{self.PREFIX}*"):
              self.r.delete(key)
  ```

- [ ] **Step 5: Implement** `app/ai/indexer.py`:
  ```python
  from app.ai.embeddings import embed_many
  from app.ai.product_text import build_blob
  from app.repositories.product_repository import ProductRepository


  def build_index(db, store, embed_many_fn=embed_many) -> int:
      products = ProductRepository(db).list_all()
      store.ensure_index()
      vectors = embed_many_fn([build_blob(p) for p in products])
      for p, v in zip(products, vectors):
          store.upsert(p.id, v, p.name)
      return len(products)
  ```

- [ ] **Step 6: Implement** `scripts/embed_products.py` (path detection mirrors
  `scripts/seed_products.py`; builds `SessionLocal` + `redis_client`, calls `build_index`,
  prints the count).

- [ ] **Step 7: Integration test** — `test_vector_store.py` (marked `@pytest.mark.integration`,
  needs real redis-stack; deterministic hand-made vectors, no OpenAI):
  ```python
  import pytest
  from app.ai.vector_store import VectorStore, DIM
  from app.core.redis_client import redis_client

  @pytest.mark.integration
  def test_knn_returns_nearest_first():
      store = VectorStore(redis_client)
      store.clear()
      store.ensure_index()
      base = [0.0] * DIM
      near = base.copy(); near[0] = 1.0
      far = base.copy(); far[1] = 1.0
      store.upsert(1, near, "near")
      store.upsert(2, far, "far")
      query = base.copy(); query[0] = 0.9
      assert store.knn(query, k=1) == [1]
      assert store.knn(query, k=2, exclude_id=1) == [2]
  ```

- [ ] **Step 8: Run** unit tests (pass) + the integration test against live redis
  (`pytest -m integration tests/test_vector_store.py`). **Commit**
  `feat(ai): redis vector store + product embeddings indexer`.

---

### Task 3: Agent tools (implementations + schemas)

**Files:**
- Create: `backend/app/ai/tools.py`
- Modify: `backend/app/core/deps.py` (add `get_optional_user`)
- Test: `backend/tests/test_ai_tools.py`

**Interfaces:**
- Produces: `TOOL_SCHEMAS: list[dict]` (OpenAI function-calling format);
  `ToolExecutor(db, store, embed_fn, user=None)` with `run(name, args) -> dict`.

- [ ] **Step 1: Failing test** — `test_ai_tools.py` (uses SQLite `db_session` + a fake store):
  ```python
  from decimal import Decimal
  from app.models import Product
  from app.ai.tools import ToolExecutor

  class _FakeStore:
      def knn(self, vec, k, exclude_id=None): return self.ids

  def _p(db, name, stock, price="499"):
      p = Product(name=name, brand="Apple", category="smartphone",
                  price_usd=Decimal(price), stock=stock)
      db.add(p); db.commit(); return p.id

  def test_check_stock_reports_live_value(db_session):
      pid = _p(db_session, "Apple iPhone 13", stock=0)
      ex = ToolExecutor(db_session, _FakeStore(), embed_fn=lambda t: [0.0])
      out = ex.run("check_stock", {"product_id": pid})
      assert out["in_stock"] is False and out["stock"] == 0

  def test_semantic_search_maps_knn_ids_to_products(db_session):
      pid = _p(db_session, "Apple iPhone 13", stock=5)
      store = _FakeStore(); store.ids = [pid]
      ex = ToolExecutor(db_session, store, embed_fn=lambda t: [0.0] * 3)
      out = ex.run("semantic_search", {"query": "a phone"})
      assert out["products"][0]["id"] == pid

  def test_add_to_favorites_requires_login(db_session):
      pid = _p(db_session, "Apple iPhone 13", stock=5)
      ex = ToolExecutor(db_session, _FakeStore(), embed_fn=lambda t: [0.0], user=None)
      out = ex.run("add_to_favorites", {"product_id": pid})
      assert "error" in out
  ```

- [ ] **Step 2: Run — expect fail.**

- [ ] **Step 3: Implement** `app/ai/tools.py` — `TOOL_SCHEMAS` for the six tools and a
  `ToolExecutor` dispatching `run(name, args)` to `_search_products`, `_semantic_search`
  (embed → `store.knn` → load live rows), `_get_product_details`, `_check_stock`,
  `_recommend_similar` (`store.knn(exclude_id=...)`), `_add_to_favorites` (returns
  `{"error": "login required"}` when `user is None`, else reuses `FavoriteService`).
  Product-shaped results reuse `ProductPublic.model_dump(mode="json")`; each method returns a
  JSON-serializable dict. Reuse `ProductService.search` for `_search_products`.

- [ ] **Step 4: Add** `get_optional_user` to `deps.py` (same as `get_current_user` but returns
  `None` instead of raising when there is no/invalid token).

- [ ] **Step 5: Run — pass.** **Commit** `feat(ai): agentic tool set (search, stock, recommend, favorite)`.

---

### Task 4: Assistant — grounding, agent loop, prompt cap, degradation

**Files:**
- Create: `backend/app/ai/assistant.py`
- Test: `backend/tests/test_assistant.py`

**Interfaces:**
- Consumes: `embeddings.is_configured/embed`, `VectorStore`, `ToolExecutor`, `TOOL_SCHEMAS`.
- Produces: `Assistant(db, redis, user=None, embed_fn=embed, chat_fn=None, store=None)` with
  `reply(message: str, session_id: str) -> dict` returning
  `{reply, remaining_prompts, available, sources}`.

- [ ] **Step 1: Failing tests** — `test_assistant.py`. A fake redis (get/incr/expire), a fake
  store (`knn` → preset ids), a fake `chat_fn` that scripts one tool call then a final answer,
  and `embed_fn=lambda t: [0.0]`:
  ```python
  # cap: the 6th prompt is refused without invoking chat_fn
  def test_five_prompt_cap(db_session):
      calls = []
      def chat_fn(messages, tools):
          calls.append(1)
          return {"content": "hi", "tool_calls": []}
      a = Assistant(db_session, FakeRedis(), embed_fn=lambda t: [0.0],
                    chat_fn=chat_fn, store=FakeStore([]))
      for _ in range(5):
          r = a.reply("hello", "s1")
          assert r["available"] is True
      blocked = a.reply("hello", "s1")
      assert blocked["remaining_prompts"] == 0
      assert "limit" in blocked["reply"].lower()
      assert len(calls) == 5           # 6th never hit OpenAI

  # graceful degradation when the key is a placeholder
  def test_unavailable_when_not_configured(db_session, monkeypatch):
      monkeypatch.setattr("app.ai.assistant.is_configured", lambda: False)
      a = Assistant(db_session, FakeRedis(), store=FakeStore([]))
      r = a.reply("hello", "s1")
      assert r["available"] is False

  # agent loop: a tool call is executed and fed back for a grounded answer
  def test_agent_runs_tool_then_answers(db_session):
      pid = _seed_phone(db_session)
      scripted = [
          {"content": None, "tool_calls": [
              {"id": "t1", "name": "check_stock", "arguments": {"product_id": pid}}]},
          {"content": "It's in stock.", "tool_calls": []},
      ]
      def chat_fn(messages, tools):
          return scripted.pop(0)
      a = Assistant(db_session, FakeRedis(), embed_fn=lambda t: [0.0],
                    chat_fn=chat_fn, store=FakeStore([pid]))
      r = a.reply("is it available?", "s1")
      assert r["reply"] == "It's in stock."
  ```

- [ ] **Step 2: Run — expect fail.**

- [ ] **Step 3: Implement** `app/ai/assistant.py`:
  - `chat_fn` default wraps OpenAI: `client.chat.completions.create(model=..., messages,
    tools, tool_choice="auto")`, normalized to `{"content": str|None, "tool_calls":[{id,name,arguments(dict)}]}`.
  - `reply()`:
    1. `remaining = limit - used(session)`; if `<= 0` → `{reply:"You've reached the 5-prompt
       limit for this session.", remaining_prompts:0, available:True, sources:[]}` (no OpenAI).
    2. if `not is_configured()` → unavailable reply (`available:False`), do **not** count it.
    3. `store.ensure_index()`; if `store.is_empty()` → `build_index(db, store, ...)` (lazy).
    4. `vec = embed_fn(message)`; `ids = store.knn(vec, k=5)`; load live products → context block.
    5. messages = `[system, context, user]`; loop ≤3: `chat_fn(messages, TOOL_SCHEMAS)`; if
       `tool_calls`, run each via `ToolExecutor` and append tool results; else break with content.
    6. increment the session counter; return `{reply, remaining_prompts, available:True, sources}`.
  - Wrap the OpenAI call path in `try/except` → on error return the unavailable reply.

- [ ] **Step 4: Run — pass.** **Commit** `feat(ai): grounded agent loop + 5-prompt cap + graceful degradation`.

---

### Task 5: `/chat` endpoint

**Files:**
- Create: `backend/app/controllers/chat.py`, `backend/app/schemas/chat.py`
- Modify: `backend/app/main.py` (mount)
- Test: `backend/tests/test_chat_api.py`

**Interfaces:**
- `POST /chat` body `{message: str, session_id: str}` → `{reply, remaining_prompts, available, sources}`.
- Auth is **optional** (`get_optional_user`); the `add_to_favorites` tool only works when logged in.

- [ ] **Step 1: Failing test** — `test_chat_api.py`. Override the `get_assistant` dependency to
  build a real `Assistant` wired with fakes (fake redis, fake store, scripted `chat_fn`,
  `embed_fn`), so the real endpoint + assistant logic run with zero network:
  ```python
  def test_chat_returns_reply_and_remaining(client_with_fake_assistant):
      r = client_with_fake_assistant.post(
          "/chat", json={"message": "hi", "session_id": "s1"})
      assert r.status_code == 200
      body = r.json()
      assert body["reply"]
      assert body["remaining_prompts"] == 4
      assert body["available"] is True
  ```
  (Fixture lives in the test module: overrides `get_assistant` on the app.)

- [ ] **Step 2: Run — expect fail** (route missing).

- [ ] **Step 3: Implement** `schemas/chat.py` (`ChatRequest`, `ChatResponse`),
  `controllers/chat.py` with a `get_assistant(db, redis, user)` dependency + the `POST /chat`
  handler, and mount `chat.router` in `main.py`.

- [ ] **Step 4: Run — pass.** **Commit** `feat(ai): POST /chat endpoint`.

---

## Definition of Done (Phase 6)

- [ ] `scripts/embed_products.py` embeds all 151 products into the Redis VSS index; the chat
      path lazily builds it if empty.
- [ ] `POST /chat` returns grounded, stock-aware answers; both in- and out-of-stock products
      are retrievable; stock is read live from MySQL.
- [ ] Native function-calling works end-to-end (a tool call is executed and fed back).
- [ ] 5 prompts/session enforced in Redis; the 6th is refused without an OpenAI call.
- [ ] Missing/placeholder key or an OpenAI error → friendly "unavailable" (no 500).
- [ ] `add_to_favorites` works only for authenticated users.
- [ ] Full unit suite green (OpenAI mocked) + VSS integration test + a **live smoke** with the
      real key (grounded answer, a tool fires, the 6th prompt blocked).
- [ ] Pushed to `main` under Adir's name.

**Next phase:** Phase 7 — ML churn prediction (synthetic data → labeled dataset → scikit-learn
model → `GET /ml/churn/{user_id}`).
