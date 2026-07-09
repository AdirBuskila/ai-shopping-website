from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password, verify_password
from app.models import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import RegisterRequest


class AuthService:
    def __init__(self, db: Session):
        self.repo = UserRepository(db)

    def register(self, data: RegisterRequest) -> User:
        if self.repo.get_by_username(data.username):
            raise HTTPException(status.HTTP_409_CONFLICT, "Username already taken")
        if self.repo.get_by_email(data.email):
            raise HTTPException(status.HTTP_409_CONFLICT, "Email already registered")
        user = User(
            username=data.username,
            email=data.email,
            first_name=data.first_name,
            last_name=data.last_name,
            phone=data.phone,
            country=data.country,
            city=data.city,
            password_hash=hash_password(data.password),
        )
        return self.repo.create(user)

    def authenticate(self, username: str, password: str) -> str:
        user = self.repo.get_by_username(username)
        if not user or not verify_password(password, user.password_hash):
            raise HTTPException(
                status.HTTP_401_UNAUTHORIZED, "Invalid username or password"
            )
        return create_access_token(str(user.id))

    def delete_account(self, user: User) -> None:
        self.repo.delete(user)
