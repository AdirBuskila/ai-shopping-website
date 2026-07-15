"""Train + evaluate the churn model and persist an artifact for serving.

Compares Logistic Regression (explainable) against Random Forest (nonlinear),
prints and writes a metrics report, and saves the better model (by ROC-AUC) with
its scaler and feature order to backend/app/ml/artifacts/churn_model.joblib.
"""
import pathlib
import sys

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (accuracy_score, confusion_matrix, f1_score,
                             precision_score, recall_score, roc_auc_score)
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

# import the canonical feature order from the backend package
_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "backend"))
from app.ml.features import FEATURE_NAMES  # noqa: E402

DATA = _ROOT / "ml_training" / "data" / "churn_dataset.csv"
ARTIFACT = _ROOT / "backend" / "app" / "ml" / "artifacts" / "churn_model.joblib"
REPORT = _ROOT / "ml_training" / "report.md"
SEED = 42


def _metrics(y_true, y_pred, y_proba) -> dict:
    return {
        "accuracy": accuracy_score(y_true, y_pred),
        "roc_auc": roc_auc_score(y_true, y_proba),
        "precision": precision_score(y_true, y_pred),
        "recall": recall_score(y_true, y_pred),
        "f1": f1_score(y_true, y_pred),
        "confusion": confusion_matrix(y_true, y_pred).tolist(),
    }


def main() -> None:
    df = pd.read_csv(DATA)
    X = df[FEATURE_NAMES].to_numpy(dtype=float)
    y = df["churn"].to_numpy(dtype=int)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, stratify=y, random_state=SEED)

    scaler = StandardScaler().fit(X_train)
    Xtr, Xte = scaler.transform(X_train), scaler.transform(X_test)

    models = {
        "logreg": LogisticRegression(max_iter=1000, random_state=SEED),
        "rf": RandomForestClassifier(n_estimators=200, random_state=SEED),
    }
    results = {}
    for kind, model in models.items():
        model.fit(Xtr, y_train)
        proba = model.predict_proba(Xte)[:, 1]
        pred = (proba >= 0.5).astype(int)
        results[kind] = _metrics(y_test, pred, proba)

    best = max(results, key=lambda k: results[k]["roc_auc"])
    ARTIFACT.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({"model": models[best], "scaler": scaler,
                 "features": FEATURE_NAMES, "kind": best}, ARTIFACT)

    _write_report(results, best, models["logreg"])
    print(f"served model: {best} (ROC-AUC {results[best]['roc_auc']:.3f})")
    print(f"artifact -> {ARTIFACT}")


def _write_report(results, best, logreg) -> None:
    lines = ["# Churn Model — Training Report", "",
             f"**Served model:** `{best}` (chosen by ROC-AUC). "
             "Features are standardized; both models compared below.", "",
             "| Model | Accuracy | ROC-AUC | Precision | Recall | F1 |",
             "|---|---|---|---|---|---|"]
    for kind, m in results.items():
        star = " ⭐" if kind == best else ""
        lines.append(f"| {kind}{star} | {m['accuracy']:.3f} | {m['roc_auc']:.3f} | "
                     f"{m['precision']:.3f} | {m['recall']:.3f} | {m['f1']:.3f} |")
    lines += ["", "## Confusion matrix (served model)", "",
              "Rows = actual, Cols = predicted `[retain, churn]`.", "",
              f"```\n{np.array(results[best]['confusion'])}\n```", "",
              "## Logistic-regression coefficients (feature influence on churn)", "",
              "| Feature | Coefficient |", "|---|---|"]
    for name, coef in zip(FEATURE_NAMES, logreg.coef_[0]):
        lines.append(f"| {name} | {coef:+.3f} |")
    lines += ["", "_Positive coefficient → raises churn risk; negative → lowers it._", ""]
    REPORT.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
