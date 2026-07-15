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
RETRIEVE_K = 12  # wider net so in-stock alternatives surface even when the top matches are sold out
MAX_TOOL_ROUNDS = 3
COUNTER_TTL = 86400  # 1 day

SYSTEM_PROMPT = (
    "You are the shopping assistant for an online electronics store. "
    "Answer ONLY using our catalog. Use the provided tools to look up products, "
    "check live stock, recommend similar items, and (for signed-in users) add "
    "favorites. All prices are in USD. "
    "IMPORTANT — only ever RECOMMEND products that are IN STOCK. If the closest "
    "match to what the user wants is out of stock, briefly note it's unavailable "
    "and recommend the nearest IN-STOCK alternative instead — never present an "
    "out-of-stock item as a recommendation, and never say 'nothing is available' "
    "when in-stock alternatives exist. "
    "Lead with your single best recommendation first, then optionally mention "
    "alternatives. Always write each product's NAME and its PRICE in bold using "
    "markdown (e.g. **Phone Line F34 32GB** for **$72.63**). "
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

    def _context_block(self, in_stock, out_stock) -> str:
        lines = []
        if in_stock:
            lines.append("IN-STOCK products relevant to the request "
                         "— recommend ONLY from these:")
            for p in in_stock[:8]:
                lines.append(f"- [id {p.id}] {p.name} — ${float(p.price_usd):.2f}, "
                             f"{p.stock} in stock")
        else:
            lines.append("No in-stock products closely match this request.")
        if out_stock:
            lines.append("")
            lines.append("Also matched but OUT OF STOCK — do NOT recommend these; "
                         "mention only if the user asks about them specifically:")
            for p in out_stock[:4]:
                lines.append(f"- [id {p.id}] {p.name} — OUT OF STOCK")
        return "\n".join(lines)

    def _run(self, message: str):
        self.store.ensure_index()
        if self.store.is_empty():
            build_index(self.db, self.store)  # lazy first-time build

        candidates = self._load(self.store.knn(self.embed_fn(message), RETRIEVE_K))
        in_stock = [p for p in candidates if p.stock > 0]
        out_stock = [p for p in candidates if p.stock <= 0]

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "system", "content": self._context_block(in_stock, out_stock)},
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
        # Order the source cards to match the reply: whichever product the model
        # mentioned first becomes the featured (first) card; unmentioned ones follow.
        ranked = sorted(in_stock, key=lambda p: self._mention_pos(p, final))
        sources = [
            {"id": p.id, "name": p.name, "image_url": p.image_url,
             "price_usd": float(p.price_usd)}
            for p in ranked[:4]
        ]
        return final, sources

    def _mention_pos(self, product, reply: str) -> int:
        """Index at which the product is mentioned in the reply (big number if
        not mentioned), so mentioned products sort first, earliest-first."""
        low = reply.lower()
        i = low.find(product.name.lower())
        if i >= 0:
            return i
        parts = product.name.split(" ", 1)  # drop leading brand word, try the model
        if len(parts) > 1:
            j = low.find(parts[1].lower())
            if j >= 0:
                return j
        return len(reply) + 1
