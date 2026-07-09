from pydantic import BaseModel, ConfigDict


class ProductPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    brand: str | None = None
    category: str | None = None
    price_usd: float
    stock: int
    image_url: str | None = None
    description: str | None = None
