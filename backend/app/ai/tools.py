"""The agent's tool set: implementations + their OpenAI function-calling schemas.

Each tool returns a plain JSON-serializable dict (the model reads it back as a tool
result). Product lookups always read LIVE rows from MySQL, so stock is never stale.
"""
from app.ai.product_text import build_blob
from app.core.enums import SearchOp
from app.models import Product
from app.repositories.product_repository import ProductRepository
from app.schemas.product import ProductPublic
from app.services.favorite_service import FavoriteService
from app.services.product_service import ProductService

TOP_K = 5
SEARCH_LIMIT = 10


TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "search_products",
            "description": "Keyword search of the catalog by name, with optional "
                           "max price and in-stock-only filters.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string",
                              "description": "words to match in the product name"},
                    "max_price": {"type": "number",
                                  "description": "only products cheaper than this (USD)"},
                    "in_stock_only": {"type": "boolean"},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "semantic_search",
            "description": "Find products by meaning (vector similarity), even when "
                           "the wording doesn't match exactly.",
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_product_details",
            "description": "Full details for one product by id.",
            "parameters": {
                "type": "object",
                "properties": {"product_id": {"type": "integer"}},
                "required": ["product_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "check_stock",
            "description": "Live stock level for one product by id.",
            "parameters": {
                "type": "object",
                "properties": {"product_id": {"type": "integer"}},
                "required": ["product_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "recommend_similar",
            "description": "Recommend products similar to a given product id "
                           "(nearest neighbours in the vector store).",
            "parameters": {
                "type": "object",
                "properties": {"product_id": {"type": "integer"}},
                "required": ["product_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "add_to_favorites",
            "description": "Add a product to the signed-in user's favorites. "
                           "Only works when the user is logged in.",
            "parameters": {
                "type": "object",
                "properties": {"product_id": {"type": "integer"}},
                "required": ["product_id"],
            },
        },
    },
]


class ToolExecutor:
    def __init__(self, db, store, embed_fn, user=None):
        self.db = db
        self.store = store
        self.embed_fn = embed_fn
        self.user = user
        self.products = ProductRepository(db)

    # --- dispatch ------------------------------------------------------------

    def run(self, name: str, args: dict) -> dict:
        method = getattr(self, f"_{name}", None)
        if method is None:
            return {"error": f"unknown tool: {name}"}
        try:
            return method(**(args or {}))
        except TypeError as exc:
            return {"error": f"bad arguments for {name}: {exc}"}

    # --- helpers -------------------------------------------------------------

    def _serialize(self, rows) -> list[dict]:
        return [ProductPublic.model_validate(p).model_dump(mode="json") for p in rows]

    def _load_by_ids(self, ids: list[int]):
        rows = {p.id: p for p in
                self.db.query(Product).filter(Product.id.in_(ids)).all()}
        return [rows[i] for i in ids if i in rows]

    # --- tools ---------------------------------------------------------------

    def _search_products(self, query, max_price=None, in_stock_only=False) -> dict:
        stock_op, stock_value = (SearchOp.GT, 0) if in_stock_only else (None, None)
        price_op, price_value = (SearchOp.LT, max_price) if max_price else (None, None)
        rows = ProductService(self.db).repo.search(
            query, stock_op, stock_value, price_op, price_value)
        return {"products": self._serialize(rows[:SEARCH_LIMIT])}

    def _semantic_search(self, query) -> dict:
        ids = self.store.knn(self.embed_fn(query), TOP_K * 2)
        rows = self._load_by_ids(ids)
        rows.sort(key=lambda p: p.stock <= 0)  # in-stock first, for recommendations
        return {"products": self._serialize(rows[:TOP_K])}

    def _get_product_details(self, product_id) -> dict:
        p = self.products.get(product_id)
        if not p:
            return {"error": "product not found"}
        return {"product": ProductPublic.model_validate(p).model_dump(mode="json")}

    def _check_stock(self, product_id) -> dict:
        p = self.products.get(product_id)
        if not p:
            return {"error": "product not found"}
        return {"product_id": p.id, "name": p.name,
                "stock": p.stock, "in_stock": p.stock > 0}

    def _recommend_similar(self, product_id) -> dict:
        p = self.products.get(product_id)
        if not p:
            return {"error": "product not found"}
        ids = self.store.knn(self.embed_fn(build_blob(p)), TOP_K * 2, exclude_id=product_id)
        rows = self._load_by_ids(ids)
        rows.sort(key=lambda x: x.stock <= 0)  # in-stock first
        return {"products": self._serialize(rows[:TOP_K])}

    def _add_to_favorites(self, product_id) -> dict:
        if self.user is None:
            return {"error": "login required to add favorites"}
        FavoriteService(self.db).add(self.user.id, product_id)
        return {"added": True, "product_id": product_id}
