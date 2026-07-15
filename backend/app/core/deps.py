from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_token
from app.models import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login", auto_error=False)


def get_current_user(
    token: str | None = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    exc = HTTPException(
        status.HTTP_401_UNAUTHORIZED,
        "Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not token:
        raise exc
    sub = decode_token(token)
    if sub is None:
        raise exc
    user = db.get(User, int(sub))
    if user is None:
        raise exc
    return user


def get_optional_user(
    token: str | None = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User | None:
    """Like get_current_user but returns None instead of raising when the caller
    is anonymous — used by the chat endpoint (browsing is allowed logged-out;
    only the add_to_favorites tool needs a real user)."""
    if not token:
        return None
    sub = decode_token(token)
    if sub is None:
        return None
    return db.get(User, int(sub))
