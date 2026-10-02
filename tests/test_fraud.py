import math

import pytest

from factored_banking import fraud


def test_public_fixture_is_not_presented_as_validated_risk():
    result = fraud.assess({"provenance": "team_generated_fixture", "currency": "COP"})
    assert result["status"] == "out_of_domain"
    assert result["probability"] is None
    assert result["recommended_action"] == "review_only"


def test_constant_release_does_not_use_label_or_supplied_score():
    a = fraud.assess(
        {
            "provenance": "organizer_synthetic_historical",
            "currency": "COP",
            "is_fraud": True,
            "fraud_score": 100,
        }
    )
    b = fraud.assess(
        {
            "provenance": "organizer_synthetic_historical",
            "currency": "COP",
            "is_fraud": False,
            "fraud_score": 0,
        }
    )
    assert a == b
    assert a["status"] == "population_baseline"
    assert a["probability"] == pytest.approx(3712 / 3735596)


def test_model_failure_does_not_silently_mean_low_risk(monkeypatch):
    def missing():
        raise OSError("missing model")

    monkeypatch.setattr(fraud, "load_model", missing)
    result = fraud.assess({"provenance": "organizer_synthetic_historical", "currency": "COP"})
    assert result["status"] == "unavailable"
    assert result["probability"] is None


def test_feature_formula_has_no_targets_and_rejects_nonfinite():
    row = {
        "amount": 100,
        "transaction_date": "2026-01-05 14:00:00",
        "prior_count_30d": 4,
        "prior_mean_amount_30d": 50,
    }
    values = fraud.feature_values(row)
    assert values["log_amount_ratio"] == pytest.approx(math.log(3))
    assert values["weekday"] == 1
    with pytest.raises(ValueError):
        fraud.feature_values({**row, "amount": float("nan")})


def test_safe_logistic_export_math():
    model = {
        "numeric": ["n"],
        "mean": [2],
        "scale": [2],
        "categorical": ["c"],
        "categories": [["a", "b"]],
        "coefficients": [2, 3, 4],
        "intercept": -1,
        "calibration_intercept": 0,
        "calibration_coefficient": 1,
    }
    assert fraud.logistic_probability(model, {"n": 4, "c": "b"}) == pytest.approx(fraud.sigmoid(5))
    assert fraud.logistic_probability(model, {"n": 4, "c": "unknown"}) == pytest.approx(
        fraud.sigmoid(1)
    )
