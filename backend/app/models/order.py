from sqlalchemy import (Column, DateTime, Enum, ForeignKey, Integer, Numeric,
                        SmallInteger, String, UniqueConstraint, func)
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.core.enums import OrderStatus


class Order(Base):
    __tablename__ = "orders"
    __table_args__ = (
        UniqueConstraint("user_id", "is_temp", name="uq_one_temp_per_user"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"),
                     nullable=False, index=True)
    status = Column(Enum(OrderStatus), nullable=False, default=OrderStatus.TEMP)
    is_temp = Column(SmallInteger, nullable=True)  # 1 while TEMP, NULL when CLOSE
    shipping_address = Column(String(255))
    total_price = Column(Numeric(10, 2), default=0)
    created_at = Column(DateTime, server_default=func.now())
    closed_at = Column(DateTime, nullable=True)

    items = relationship("OrderItem", back_populates="order",
                         cascade="all, delete-orphan")
