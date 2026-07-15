from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.ml.churn_model import is_ready, predict_from_vector
from app.ml.features import compute_features, feature_vector
from app.models import User
from app.schemas.ml import ChurnResponse

router = APIRouter(prefix="/ml", tags=["ml"])


@router.get("/churn/{user_id}", response_model=ChurnResponse)
def predict_churn(user_id: int, db: Session = Depends(get_db)):
    if not db.get(User, user_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    if not is_ready():
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "Churn model is not trained (run ml_training/train_churn.py)")
    features = compute_features(db, user_id)
    prediction = predict_from_vector(feature_vector(features))
    return {"user_id": user_id, **prediction, "features": features}
