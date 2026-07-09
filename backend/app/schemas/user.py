from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr


class UserPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    first_name: str | None = None
    last_name: str | None = None
    email: EmailStr
    phone: str | None = None
    country: str | None = None
    city: str | None = None
    created_at: datetime | None = None
