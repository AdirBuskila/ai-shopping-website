from sqlalchemy.orm import Session

from app.core.enums import OrderStatus
from app.models import Order, OrderItem


class OrderRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, order_id: int) -> Order | None:
        return self.db.get(Order, order_id)

    def get_temp(self, user_id: int) -> Order | None:
        return (
            self.db.query(Order)
            .filter_by(user_id=user_id, status=OrderStatus.TEMP)
            .first()
        )

    def create_temp(self, user_id: int) -> Order:
        order = Order(user_id=user_id, status=OrderStatus.TEMP, is_temp=1,
                      total_price=0)
        self.db.add(order)
        self.db.commit()
        self.db.refresh(order)
        return order

    def list_for_user(self, user_id: int) -> list[Order]:
        # is_temp = 1 for TEMP, NULL for CLOSE. Both MySQL and SQLite rank NULL
        # lowest, so DESC pins the TEMP order first; then newest CLOSE orders.
        return (
            self.db.query(Order)
            .filter_by(user_id=user_id)
            .order_by(Order.is_temp.desc(), Order.created_at.desc(), Order.id.desc())
            .all()
        )

    def get_item(self, order_id: int, product_id: int) -> OrderItem | None:
        return (
            self.db.query(OrderItem)
            .filter_by(order_id=order_id, product_id=product_id)
            .first()
        )

    def delete(self, order: Order) -> None:
        self.db.delete(order)
        self.db.commit()
