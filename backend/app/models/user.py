from sqlalchemy import Boolean, Column, DateTime, Integer, String, func

from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    first_name = Column(String(80))
    last_name = Column(String(80))
    email = Column(String(120), unique=True, nullable=False, index=True)
    phone = Column(String(40))
    country = Column(String(80))
    city = Column(String(80))
    password_hash = Column(String(255), nullable=False)
    is_synthetic = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, server_default=func.now())
