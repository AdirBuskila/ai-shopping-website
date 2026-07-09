import json

from fastapi import HTTPException, status

from app.repositories.product_repository import ProductRepository
from app.schemas.product import ProductPublic

CACHE_KEY = "products:all"
CACHE_TTL = 300


class ProductService:
    def __init__(self, db, cache=None):
        self.repo = ProductRepository(db)
        self.cache = cache

    def _serialize(self, products):
        return [ProductPublic.model_validate(p).model_dump(mode="json") for p in products]

    def list_all(self):
        if self.cache:
            try:
                hit = self.cache.get(CACHE_KEY)
                if hit:
                    return json.loads(hit)
            except Exception:
                pass  # Redis down → fall back to DB, never 500
        data = self._serialize(self.repo.list_all())
        if self.cache:
            try:
                self.cache.setex(CACHE_KEY, CACHE_TTL, json.dumps(data))
            except Exception:
                pass
        return data

    def get(self, product_id: int):
        p = self.repo.get(product_id)
        if not p:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Product not found")
        return ProductPublic.model_validate(p).model_dump(mode="json")

    def search(self, q, stock_op, stock_value, price_op, price_value):
        return self._serialize(
            self.repo.search(q, stock_op, stock_value, price_op, price_value)
        )
