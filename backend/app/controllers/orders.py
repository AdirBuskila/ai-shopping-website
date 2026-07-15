from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.redis_client import get_redis
from app.models import User
from app.schemas.order import AddItemRequest, OrderPublic, PurchaseRequest
from app.services.order_service import OrderService

router = APIRouter(prefix="/orders", tags=["orders"])


@router.get("", response_model=list[OrderPublic])
def list_orders(
    current: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    return OrderService(db).list(current.id)


# NOTE: literal /items routes are declared before /{order_id} so "items" is
# never captured as an order id.
@router.post("/items", response_model=OrderPublic,
             status_code=status.HTTP_201_CREATED)
def add_item(
    body: AddItemRequest,
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return OrderService(db).add_item(current.id, body.product_id, body.quantity)


@router.delete("/items/{product_id}", response_model=OrderPublic | None)
def remove_item(
    product_id: int,
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return OrderService(db).remove_item(current.id, product_id)


@router.post("/{order_id}/purchase", response_model=OrderPublic)
def purchase_order(
    order_id: int,
    body: PurchaseRequest | None = None,
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    cache=Depends(get_redis),
):
    address = body.shipping_address if body else None
    return OrderService(db, cache).purchase(current.id, order_id, address)


@router.get("/{order_id}", response_model=OrderPublic)
def get_order(
    order_id: int,
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return OrderService(db).get(current.id, order_id)


@router.delete("/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_order(
    order_id: int,
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    OrderService(db).delete(current.id, order_id)
