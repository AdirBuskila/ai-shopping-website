from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models import User
from app.schemas.product import ProductPublic
from app.services.favorite_service import FavoriteService

router = APIRouter(prefix="/favorites", tags=["favorites"])


@router.get("", response_model=list[ProductPublic])
def list_favorites(
    current: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    return FavoriteService(db).list(current.id)


@router.post("/{product_id}", response_model=list[ProductPublic],
             status_code=status.HTTP_201_CREATED)
def add_favorite(
    product_id: int,
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return FavoriteService(db).add(current.id, product_id)


@router.delete("/{product_id}", response_model=list[ProductPublic])
def remove_favorite(
    product_id: int,
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return FavoriteService(db).remove(current.id, product_id)
