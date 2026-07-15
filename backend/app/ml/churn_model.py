"""Serving-side churn model: load the joblib artifact once and predict with an
explainable breakdown of which features drove the score."""
import pathlib

import joblib
import numpy as np

from app.ml.features import FEATURE_NAMES

_ARTIFACT = pathlib.Path(__file__).resolve().parent / "artifacts" / "churn_model.joblib"
_bundle = None


def is_ready() -> bool:
    return _ARTIFACT.exists()


def _load():
    global _bundle
    if _bundle is None:
        _bundle = joblib.load(_ARTIFACT)
    return _bundle


def predict_from_vector(vec: list[float]) -> dict:
    bundle = _load()
    scaler, model, kind = bundle["scaler"], bundle["model"], bundle["kind"]
    scaled = scaler.transform([vec])
    proba = float(model.predict_proba(scaled)[0][1])

    if kind == "logreg":
        # contribution of each feature to the log-odds = coef * scaled_value
        contributions = model.coef_[0] * scaled[0]
    else:
        # RF: importance magnitude, signed by whether the value is above/below average
        contributions = model.feature_importances_ * np.sign(scaled[0])

    order = np.argsort(np.abs(contributions))[::-1][:3]
    top_factors = [{
        "feature": FEATURE_NAMES[i],
        "direction": "raises" if contributions[i] > 0 else "lowers",
    } for i in order]

    return {
        "probability": round(proba, 4),
        "label": "churn" if proba >= 0.5 else "retain",
        "top_factors": top_factors,
    }
