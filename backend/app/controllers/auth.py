from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models import User
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from app.schemas.user import UserPublic
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    return AuthService(db).register(data)


@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    token = AuthService(db).authenticate(data.username, data.password)
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserPublic)
def me(current: User = Depends(get_current_user)):
    return current


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
def delete_me(
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    AuthService(db).delete_account(current)
