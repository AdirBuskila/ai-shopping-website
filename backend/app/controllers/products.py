from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.enums import SearchOp
from app.core.redis_client import get_redis
from app.schemas.product import ProductPublic
from app.services.product_service import ProductService

router = APIRouter(prefix="/products", tags=["products"])


@router.get("", response_model=list[ProductPublic])
def list_products(db: Session = Depends(get_db), cache=Depends(get_redis)):
    return ProductService(db, cache).list_all()


# NOTE: /search must be declared before /{product_id} so it isn't captured as an id.
@router.get("/search", response_model=list[ProductPublic])
def search_products(
    q: str | None = None,
    stock_op: SearchOp | None = None,
    stock_value: int | None = None,
    price_op: SearchOp | None = None,
    price_value: float | None = None,
    db: Session = Depends(get_db),
):
    return ProductService(db).search(q, stock_op, stock_value, price_op, price_value)


@router.get("/{product_id}", response_model=ProductPublic)
def get_product(product_id: int, db: Session = Depends(get_db)):
    return ProductService(db).get(product_id)
