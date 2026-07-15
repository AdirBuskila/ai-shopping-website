from ml_training.generate_dataset import sample_rows


def _avg(rows, key):
    return sum(r[key] for r in rows) / len(rows)


def test_dataset_has_both_classes_and_signal():
    rows = sample_rows(400, seed=42)
    assert len(rows) == 400
    churn = [r for r in rows if r["churn"] == 1]
    keep = [r for r in rows if r["churn"] == 0]
    assert 0 < len(churn) < 400 and len(keep) > 0

    # churners buy less often, spend less, and were last seen longer ago
    assert _avg(churn, "frequency") < _avg(keep, "frequency")
    assert _avg(churn, "monetary") < _avg(keep, "monetary")
    assert _avg(churn, "recency_days") > _avg(keep, "recency_days")


def test_dataset_is_reproducible():
    a = sample_rows(50, seed=7)
    b = sample_rows(50, seed=7)
    assert a == b


def test_rows_have_all_feature_columns():
    from app.ml.features import FEATURE_NAMES
    row = sample_rows(1, seed=1)[0]
    for name in FEATURE_NAMES:
        assert name in row
    assert "churn" in row
