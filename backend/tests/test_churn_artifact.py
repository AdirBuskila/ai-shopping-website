from app.ml.churn_model import is_ready, predict_from_vector

# FEATURE_NAMES order:
# [recency_days, frequency, monetary, tenure_days, favorites_count]
CHURNER = [180, 0, 0, 300, 0]           # gone quiet, never bought, no favorites
KEEPER = [5, 12, 4000, 300, 6]          # recent, frequent, big spender, engaged


def test_artifact_is_ready():
    assert is_ready() is True


def test_churner_scores_higher_than_keeper():
    pc = predict_from_vector(CHURNER)
    pk = predict_from_vector(KEEPER)
    assert pc["probability"] > pk["probability"]
    assert 0.0 <= pc["probability"] <= 1.0
    assert pc["label"] == "churn"
    assert pk["label"] == "retain"


def test_top_factors_are_explained():
    pc = predict_from_vector(CHURNER)
    assert len(pc["top_factors"]) == 3
    for factor in pc["top_factors"]:
        assert factor["feature"]
        assert factor["direction"] in ("raises", "lowers")
