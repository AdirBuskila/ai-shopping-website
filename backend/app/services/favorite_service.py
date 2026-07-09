from fastapi import HTTPException, status

from app.repositories.favorite_repository import FavoriteRepository
from app.repositories.product_repository import ProductRepository
from app.schemas.product import ProductPublic


class FavoriteService:
    def __init__(self, db):
        self.favs = FavoriteRepository(db)
        self.products = ProductRepository(db)

    def list(self, user_id: int):
        return [
            ProductPublic.model_validate(p).model_dump(mode="json")
            for p in self.favs.list_products(user_id)
        ]

    def add(self, user_id: int, product_id: int):
        if not self.products.get(product_id):
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Product not found")
        if not self.favs.exists(user_id, product_id):
            self.favs.add(user_id, product_id)  # idempotent: skip if already present
        return self.list(user_id)

    def remove(self, user_id: int, product_id: int):
        self.favs.remove(user_id, product_id)
        return self.list(user_id)
