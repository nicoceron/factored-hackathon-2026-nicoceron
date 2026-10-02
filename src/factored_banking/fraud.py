"""Bounded local fraud inference. A score is evidence, never action authorization."""

from __future__ import annotations

import json
import math
from collections.abc import Mapping
from functools import lru_cache
from pathlib import Path

from factored_banking.data_pipeline import FEATURE_VERSION

MODEL_PATH = Path(__file__).with_name("models") / "fraud-model.json"


@lru_cache(maxsize=1)
def load_model() -> dict:
    return json.loads(MODEL_PATH.read_text())


def feature_values(transaction: Mapping) -> dict:
    """Shared feature formula; history must be computed by the strict-prior pipeline."""
    from datetime import datetime

    amount = float(transaction["amount"])
    timestamp = datetime.fromisoformat(str(transaction["transaction_date"]))
    count = int(transaction["prior_count_30d"])
    mean = transaction.get("prior_mean_amount_30d")
    mean = float(mean) if mean is not None else amount
    if not all(math.isfinite(value) and value >= 0 for value in [amount, count, mean]):
        raise ValueError("Invalid numeric features")
    return {
        **{
            key: str(transaction.get(key) or "missing")
            for key in [
                "currency",
                "transaction_type",
                "transaction_category",
                "channel",
                "transaction_country",
            ]
        },
        "log_amount": math.log1p(amount),
        "hour": timestamp.hour,
        "weekday": timestamp.isoweekday(),
        "log_prior_count_30d": math.log1p(count),
        "log_amount_ratio": math.log1p(amount / max(mean, 1)),
    }


def sigmoid(value: float) -> float:
    return 1 / (1 + math.exp(-max(-700, min(700, value))))


def logistic_probability(model: dict, features: Mapping) -> float:
    vector = [
        (float(features[name]) - mean) / scale
        for name, mean, scale in zip(model["numeric"], model["mean"], model["scale"], strict=True)
    ]
    for name, categories in zip(model["categorical"], model["categories"], strict=True):
        vector.extend(float(features[name] == category) for category in categories)
    score = model["intercept"] + sum(
        value * coefficient
        for value, coefficient in zip(vector, model["coefficients"], strict=True)
    )
    return sigmoid(model["calibration_intercept"] + model["calibration_coefficient"] * score)


def assess(transaction: Mapping) -> dict:
    """Assess a historical organizer transaction; fail closed on unvalidated applicability.

    Callers provide permitted records only. IDs, targets and supplied scores are ignored.
    No result can decline a dispute, refund money, freeze a card or prove guilt.
    """
    result = {
        "status": "unavailable",
        "probability": None,
        "model_version": None,
        "feature_version": FEATURE_VERSION,
        "recommended_action": "review_only",
        "reasons": [],
        "limitations": [],
    }
    try:
        model = load_model()
        result.update(model_version=model["model_version"], limitations=model["limitations"])
        provenance = transaction.get("provenance")
        if provenance != model["domain"]:
            result.update(
                status="out_of_domain", reasons=["Record is outside evaluated organizer domain"]
            )
            return result
        if transaction.get("currency") not in model["currencies"]:
            result.update(status="out_of_domain", reasons=["Currency absent from training data"])
            return result
        if model["kind"] == "constant":
            result.update(
                status="population_baseline",
                probability=model["probability"],
                reasons=["Historical dataset prevalence; not a personalized risk estimate"],
            )
            return result
        if transaction.get("feature_version") != FEATURE_VERSION:
            result["reasons"] = ["Missing or incompatible validated historical features"]
            return result
        features = feature_values(transaction)
        if model["kind"] == "logistic":
            probability = logistic_probability(model, features)
        elif model["kind"] == "catboost":
            from catboost import CatBoostClassifier

            classifier = CatBoostClassifier()
            classifier.load_model(str(MODEL_PATH.with_name(model["model_file"])))
            ordered = [features[key] for key in model["numeric"] + model["categorical"]]
            raw = float(classifier.predict_proba([ordered])[0, 1])
            odds = math.log(max(raw, 1e-9) / max(1 - raw, 1e-9))
            probability = sigmoid(
                model["calibration_intercept"] + model["calibration_coefficient"] * odds
            )
        else:
            raise ValueError("Unsupported model kind")
        result.update(
            status="available",
            probability=probability,
            reasons=["Retrospective association in synthetic organizer data"],
        )
    except (OSError, ValueError, KeyError, TypeError, ImportError):
        result["reasons"] = ["Model or validated feature input unavailable"]
    return result
