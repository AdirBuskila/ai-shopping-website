from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError

from app.core.enums import OrderStatus, StockResult
from app.models import OrderItem, Product
from app.repositories.order_repository import OrderRepository
from app.repositories.product_repository import ProductRepository
from app.services.product_service import CACHE_KEY


class OrderService:
    """The cart/order state machine + transactional stock control.

    A user has at most one TEMP order (the live cart). Buying it closes the
    order and decrements stock inside one transaction that locks the product
    rows, so two concurrent buyers can never oversell the same unit.
    """

    def __init__(self, db, cache=None):
        self.db = db
        self.orders = OrderRepository(db)
        self.products = ProductRepository(db)
        self.cache = cache

    # --- helpers -------------------------------------------------------------

    def _stock_check(self, product: Product, desired: int):
        if product.stock <= 0:
            return StockResult.OUT_OF_STOCK, f"'{product.name}' is out of stock"
        if desired > product.stock:
            return (StockResult.INSUFFICIENT,
                    f"Only {product.stock} of '{product.name}' left in stock")
        return StockResult.OK, ""

    def _total(self, order) -> Decimal:
        return sum((i.unit_price * i.quantity for i in order.items), Decimal("0"))

    def _serialize(self, order) -> dict:
        items = []
        for it in order.items:
            items.append({
                "product_id": it.product_id,
                "name": it.product.name,
                "quantity": it.quantity,
                "unit_price": float(it.unit_price),
                "line_total": float(it.unit_price * it.quantity),
            })
        return {
            "id": order.id,
            "user_id": order.user_id,
            "status": order.status.value,
            "shipping_address": order.shipping_address,
            "total_price": float(order.total_price or 0),
            "created_at": order.created_at,
            "closed_at": order.closed_at,
            "items": items,
        }

    def _get_or_create_temp(self, user_id: int):
        order = self.orders.get_temp(user_id)
        if order:
            return order
        try:
            return self.orders.create_temp(user_id)
        except IntegrityError:  # a concurrent request won the UNIQUE(user, is_temp)
            self.db.rollback()
            return self.orders.get_temp(user_id)

    def _invalidate_catalog_cache(self):
        if self.cache:
            try:
                self.cache.delete(CACHE_KEY)  # stock changed → drop the cached catalog
            except Exception:
                pass

    def _owned_or_404(self, user_id: int, order_id: int):
        order = self.orders.get(order_id)
        if not order or order.user_id != user_id:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Order not found")
        return order

    # --- reads ---------------------------------------------------------------

    def list(self, user_id: int):
        return [self._serialize(o) for o in self.orders.list_for_user(user_id)]

    def get(self, user_id: int, order_id: int):
        return self._serialize(self._owned_or_404(user_id, order_id))

    # --- cart mutations ------------------------------------------------------

    def add_item(self, user_id: int, product_id: int, quantity: int = 1):
        product = self.products.get(product_id)
        if not product:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Product not found")

        # Validate against the (possibly already-present) quantity BEFORE we
        # touch the cart, so a rejected add never leaves an empty TEMP order.
        order = self.orders.get_temp(user_id)
        existing = self.orders.get_item(order.id, product_id) if order else None
        desired = (existing.quantity if existing else 0) + quantity
        result, message = self._stock_check(product, desired)
        if result is not StockResult.OK:
            raise HTTPException(status.HTTP_409_CONFLICT, message)

        if order is None:
            order = self._get_or_create_temp(user_id)
            existing = self.orders.get_item(order.id, product_id)

        if existing:
            existing.quantity = desired
        else:
            order.items.append(OrderItem(
                product_id=product_id, quantity=quantity,
                unit_price=product.price_usd))
        order.total_price = self._total(order)
        self.db.commit()
        self.db.refresh(order)
        return self._serialize(order)

    def remove_item(self, user_id: int, product_id: int):
        order = self.orders.get_temp(user_id)
        if not order:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "No active order")
        item = self.orders.get_item(order.id, product_id)
        if not item:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Item not in order")

        self.db.delete(item)
        self.db.flush()
        remaining = self.db.query(OrderItem).filter_by(order_id=order.id).all()
        if not remaining:
            self.orders.delete(order)  # empty cart deletes itself
            return None
        order.total_price = sum(
            (i.unit_price * i.quantity for i in remaining), Decimal("0"))
        self.db.commit()
        self.db.refresh(order)
        return self._serialize(order)

    # --- checkout ------------------------------------------------------------

    def purchase(self, user_id: int, order_id: int, shipping_address: str | None = None):
        order = self._owned_or_404(user_id, order_id)
        if order.status is not OrderStatus.TEMP:
            raise HTTPException(status.HTTP_409_CONFLICT, "Order is already closed")
        if not order.items:
            raise HTTPException(status.HTTP_409_CONFLICT, "Cannot purchase an empty order")

        # One transaction: lock each product row, re-validate, decrement.
        # with_for_update() takes real row locks on MySQL (ignored on SQLite),
        # so concurrent buyers cannot both pass the stock check and oversell.
        for item in order.items:
            product = (self.db.query(Product)
                       .filter_by(id=item.product_id)
                       .with_for_update()
                       .first())
            have = product.stock if product else 0
            if have < item.quantity:
                name = item.product.name
                self.db.rollback()
                raise HTTPException(
                    status.HTTP_409_CONFLICT,
                    f"Only {have} of '{name}' left — cannot complete purchase")
            product.stock -= item.quantity

        order.status = OrderStatus.CLOSE
        order.is_temp = None
        order.closed_at = func.now()
        if shipping_address is not None:
            order.shipping_address = shipping_address
        order.total_price = self._total(order)
        self.db.commit()
        self.db.refresh(order)
        self._invalidate_catalog_cache()
        return self._serialize(order)

    def delete(self, user_id: int, order_id: int):
        order = self._owned_or_404(user_id, order_id)
        if order.status is not OrderStatus.TEMP:
            raise HTTPException(
                status.HTTP_409_CONFLICT, "Only a temporary order can be deleted")
        self.orders.delete(order)
