from sqlalchemy import Column, DateTime, Integer, Numeric, String, Text, func
from sqlalchemy.types import JSON

from app.core.database import Base


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False, index=True)
    description = Column(Text)
    category = Column(String(80), index=True)
    brand = Column(String(80), index=True)
    price_usd = Column(Numeric(10, 2), nullable=False)
    stock = Column(Integer, nullable=False, default=0)
    image_url = Column(String(500))
    specs = Column(JSON)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
