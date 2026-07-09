import re

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.enums import SearchOp
from app.models import Product


class ProductRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_all(self) -> list[Product]:
        return self.db.query(Product).order_by(Product.id).all()

    def get(self, product_id: int) -> Product | None:
        return self.db.get(Product, product_id)

    def get_by_name(self, name: str) -> Product | None:
        return self.db.query(Product).filter(Product.name == name).first()

    def _cmp(self, col, op: SearchOp, val):
        if op == SearchOp.LT:
            return col < val
        if op == SearchOp.GT:
            return col > val
        return col == val

    def search(self, q, stock_op, stock_value, price_op, price_value) -> list[Product]:
        query = self.db.query(Product)
        if q:
            terms = [t for t in re.split(r"[,\s]+", q.strip()) if t]
            if terms:
                query = query.filter(
                    or_(*[Product.name.ilike(f"%{t}%") for t in terms])
                )
        if stock_op and stock_value is not None:
            query = query.filter(self._cmp(Product.stock, stock_op, stock_value))
        if price_op and price_value is not None:
            query = query.filter(self._cmp(Product.price_usd, price_op, price_value))
        return query.order_by(Product.id).all()
