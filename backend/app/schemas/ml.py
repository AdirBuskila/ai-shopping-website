from pydantic import BaseModel


class ChurnFactor(BaseModel):
    feature: str
    direction: str  # "raises" or "lowers" churn risk


class ChurnResponse(BaseModel):
    user_id: int
    probability: float
    label: str  # "churn" or "retain"
    top_factors: list[ChurnFactor]
    features: dict[str, float]
