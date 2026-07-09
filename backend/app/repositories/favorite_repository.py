from sqlalchemy.orm import Session

from app.models import Favorite, Product


class FavoriteRepository:
    def __init__(self, db: Session):
        self.db = db

    def exists(self, user_id: int, product_id: int) -> bool:
        return (
            self.db.query(Favorite)
            .filter_by(user_id=user_id, product_id=product_id)
            .first()
            is not None
        )

    def add(self, user_id: int, product_id: int) -> None:
        self.db.add(Favorite(user_id=user_id, product_id=product_id))
        self.db.commit()

    def remove(self, user_id: int, product_id: int) -> None:
        self.db.query(Favorite).filter_by(
            user_id=user_id, product_id=product_id
        ).delete()
        self.db.commit()

    def list_products(self, user_id: int) -> list[Product]:
        return (
            self.db.query(Product)
            .join(Favorite, Favorite.product_id == Product.id)
            .filter(Favorite.user_id == user_id)
            .order_by(Product.id)
            .all()
        )
