"""Synthetic churn dataset generator.

A class-conditional data-generating process: we first draw the label (churn vs
retain), then draw behavioural features conditioned on it, with deliberate overlap
(Gaussian/Poisson noise) so the classes are separable but NOT trivially so. This
guarantees real, learnable signal while staying reproducible (seeded).

Feature columns match app/ml/features.py exactly (no train/serve skew).
"""
import csv
import pathlib

import numpy as np

CHURN_RATE = 0.4
DATA = pathlib.Path(__file__).resolve().parent / "data" / "churn_dataset.csv"


def sample_rows(n: int, seed: int = 42) -> list[dict]:
    rng = np.random.default_rng(seed)
    rows = []
    for _ in range(n):
        churn = int(rng.random() < CHURN_RATE)
        if churn:  # disengaged: rare buyer, long since last seen, few favorites
            frequency = int(max(0, rng.poisson(1.5)))
            recency = float(np.clip(rng.normal(140, 50), 1, 400))
            favorites = int(max(0, rng.poisson(1)))
        else:      # engaged: frequent buyer, recent, more favorites
            frequency = int(max(0, rng.poisson(8)))
            recency = float(np.clip(rng.normal(25, 20), 0, 400))
            favorites = int(max(0, rng.poisson(4)))

        tenure = float(np.clip(rng.normal(365, 150), 30, 900))
        recency = min(recency, tenure)  # can't have been seen before signup
        aov = float(np.clip(rng.normal(280, 90), 20, 1200)) if frequency else 0.0
        monetary = round(frequency * aov, 2)
        avg_order_value = round(monetary / frequency, 2) if frequency else 0.0

        rows.append({
            "recency_days": round(recency, 2),
            "frequency": float(frequency),
            "monetary": monetary,
            "tenure_days": round(tenure, 2),
            "avg_order_value": avg_order_value,
            "favorites_count": float(favorites),
            "churn": churn,
        })
    return rows


def main(n: int = 2000, seed: int = 42) -> None:
    rows = sample_rows(n, seed)
    DATA.parent.mkdir(parents=True, exist_ok=True)
    with open(DATA, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    churn = sum(r["churn"] for r in rows)
    print(f"wrote {len(rows)} rows to {DATA} ({churn} churn / {len(rows) - churn} retain)")


if __name__ == "__main__":
    main()
