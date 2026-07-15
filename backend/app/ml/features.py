"""Canonical churn features — the SINGLE source of truth shared by training
(via the dataset generator's schema) and serving, so there is no train/serve skew.

RFM + engagement, all computable live from MySQL:
  recency_days, frequency, monetary, tenure_days, avg_order_value, favorites_count
"""
from datetime import datetime, timezone

from app.core.enums import OrderStatus
from app.models import Favorite, Order, User

# Model features. avg_order_value (= monetary / frequency) is intentionally NOT a
# model input: being a deterministic combination of frequency and monetary it adds
# no information and makes the linear coefficients collinear/uninterpretable. We
# still compute and RETURN it below for display context.
FEATURE_NAMES = [
    "recency_days",
    "frequency",
    "monetary",
    "tenure_days",
    "favorites_count",
]


def _utcnow() -> datetime:
    # naive UTC, to match the naive DATETIME columns
    return datetime.now(timezone.utc).replace(tzinfo=None)


def compute_features(db, user_id: int) -> dict[str, float]:
    user = db.get(User, user_id)
    now = _utcnow()

    tenure_days = (now - user.created_at).total_seconds() / 86400 if user.created_at else 0.0
    tenure_days = max(0.0, tenure_days)

    close_orders = (db.query(Order)
                    .filter_by(user_id=user_id, status=OrderStatus.CLOSE)
                    .all())
    frequency = len(close_orders)
    monetary = float(sum((o.total_price or 0) for o in close_orders))

    if close_orders:
        last = max((o.closed_at or o.created_at) for o in close_orders)
        recency_days = max(0.0, (now - last).total_seconds() / 86400)
    else:
        recency_days = tenure_days  # never bought → "last seen" is signup

    avg_order_value = monetary / frequency if frequency else 0.0
    favorites_count = db.query(Favorite).filter_by(user_id=user_id).count()

    return {
        "recency_days": round(recency_days, 2),
        "frequency": float(frequency),
        "monetary": round(monetary, 2),
        "tenure_days": round(tenure_days, 2),
        "avg_order_value": round(avg_order_value, 2),
        "favorites_count": float(favorites_count),
    }


def feature_vector(features: dict) -> list[float]:
    return [float(features[name]) for name in FEATURE_NAMES]
