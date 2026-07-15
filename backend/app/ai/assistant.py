"""The grounded, agentic shopping assistant.

Per request: enforce the 5-prompt cap, embed the message, retrieve the nearest
catalog items (RAG grounding), then run a short native function-calling loop where
ChatGPT may call our tools. Every OpenAI touchpoint is injectable so tests run
offline; any failure degrades to a friendly "unavailable" message (never a 500).
"""
import json

from app.ai.embeddings import embed, is_configured
from app.ai.indexer import build_index
from app.ai.tools import TOOL_SCHEMAS, ToolExecutor
from app.ai.vector_store import VectorStore
from app.core.config import settings
from app.models import Product

TOP_K = 5
MAX_TOOL_ROUNDS = 3
COUNTER_TTL = 86400  # 1 day

SYSTEM_PROMPT = (
    "You are the shopping assistant for an online electronics store. "
    "Answer ONLY using our catalog. Use the provided tools to look up products, "
    "check live stock, recommend similar items, and (for signed-in users) add "
    "favorites. Be concise and honest: if an item is out of stock or we don't "
    "carry it, say so plainly. All prices are in USD. "
    "Do NOT include images, photos, or markdown image syntax (no ![]() and no "
    "image URLs) in your reply — the app shows product images and clickable "
    "product links separately, below your message."
)
LIMIT_MSG = ("You've reached the 5-prompt limit for this session. "
             "Start a new session to keep chatting.")
UNAVAILABLE_MSG = ("The shopping assistant is currently unavailable. "
                   "Please try again later.")


def _default_chat_fn(messages, tools):
    """Call OpenAI chat completions and normalise the reply to
    {content, tool_calls:[{id,name,arguments}], raw}."""
    from app.ai.embeddings import _get_client

    resp = _get_client().chat.completions.create(
        model=settings.openai_chat_model,
        messages=messages,
        tools=tools,
        tool_choice="auto",
    )
    msg = resp.choices[0].message
    tool_calls = []
    for tc in (msg.tool_calls or []):
        try:
            args = json.loads(tc.function.arguments or "{}")
        except json.JSONDecodeError:
            args = {}
        tool_calls.append({"id": tc.id, "name": tc.function.name, "arguments": args})
    return {"content": msg.content, "tool_calls": tool_calls, "raw": msg}


class Assistant:
    def __init__(self, db, redis, user=None, embed_fn=embed, chat_fn=None, store=None):
        self.db = db
        self.redis = redis
        self.user = user
        self.embed_fn = embed_fn
        self.chat_fn = chat_fn or _default_chat_fn
        self.store = store or VectorStore(redis)

    # --- prompt cap ----------------------------------------------------------

    def _used(self, session_id: str) -> int:
        return int(self.redis.get(f"chat:count:{session_id}") or 0)

    def _increment(self, session_id: str) -> int:
        key = f"chat:count:{session_id}"
        n = self.redis.incr(key)
        if n == 1:
            self.redis.expire(key, COUNTER_TTL)
        return n

    # --- public --------------------------------------------------------------

    def reply(self, message: str, session_id: str) -> dict:
        remaining = settings.chat_prompt_limit - self._used(session_id)
        if remaining <= 0:
            return self._envelope(LIMIT_MSG, 0, available=True, sources=[])
        if not is_configured():
            return self._envelope(UNAVAILABLE_MSG, remaining, available=False, sources=[])
        try:
            reply_text, sources = self._run(message)
        except Exception:
            return self._envelope(UNAVAILABLE_MSG, remaining, available=False, sources=[])
        used = self._increment(session_id)
        return self._envelope(
            reply_text, max(0, settings.chat_prompt_limit - used),
            available=True, sources=sources)

    # --- internals -----------------------------------------------------------

    def _envelope(self, reply, remaining, available, sources) -> dict:
        return {"reply": reply, "remaining_prompts": remaining,
                "available": available, "sources": sources}

    def _load(self, ids: list[int]):
        rows = {p.id: p for p in
                self.db.query(Product).filter(Product.id.in_(ids)).all()}
        return [rows[i] for i in ids if i in rows]

    def _context_block(self, products) -> str:
        if not products:
            return "No catalog matches were retrieved for this query."
        lines = ["Relevant products from our live catalog "
                 "(use tools for full details or actions):"]
        for p in products:
            status = f"{p.stock} in stock" if p.stock > 0 else "OUT OF STOCK"
            lines.append(f"- [id {p.id}] {p.name} — ${float(p.price_usd):.2f}, {status}")
        return "\n".join(lines)

    def _run(self, message: str):
        self.store.ensure_index()
        if self.store.is_empty():
            build_index(self.db, self.store)  # lazy first-time build

        grounded = self._load(self.store.knn(self.embed_fn(message), TOP_K))
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "system", "content": self._context_block(grounded)},
            {"role": "user", "content": message},
        ]
        executor = ToolExecutor(self.db, self.store, self.embed_fn, self.user)

        final = ""
        for _ in range(MAX_TOOL_ROUNDS):
            result = self.chat_fn(messages, TOOL_SCHEMAS)
            tool_calls = result.get("tool_calls") or []
            if not tool_calls:
                final = result.get("content") or ""
                break
            messages.append(result.get("raw") or {
                "role": "assistant", "content": result.get("content")})
            for tc in tool_calls:
                out = executor.run(tc["name"], tc["arguments"])
                messages.append({"role": "tool", "tool_call_id": tc["id"],
                                 "content": json.dumps(out)})
        if not final:
            final = "I wasn't able to complete that — please try rephrasing."
        sources = [
            {"id": p.id, "name": p.name, "image_url": p.image_url,
             "price_usd": float(p.price_usd)}
            for p in grounded
        ]
        return final, sources
