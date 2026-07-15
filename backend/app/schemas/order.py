from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.core.enums import OrderStatus


class OrderItemPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    product_id: int
    name: str
    quantity: int
    unit_price: float
    line_total: float


class OrderPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    status: OrderStatus
    shipping_address: str | None = None
    total_price: float
    created_at: datetime | None = None
    closed_at: datetime | None = None
    items: list[OrderItemPublic] = []


class AddItemRequest(BaseModel):
    product_id: int
    quantity: int = Field(default=1, ge=1)


class PurchaseRequest(BaseModel):
    shipping_address: str | None = None
