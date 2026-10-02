"""Reproducible local CPU fraud experiment; aggregate reports never expose rows."""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import math
import time
from pathlib import Path

import duckdb
import numpy as np
from catboost import CatBoostClassifier
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, brier_score_loss, log_loss, roc_auc_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from factored_banking.data_pipeline import CATEGORICAL, FEATURE_VERSION, NUMERIC, sha256

SEED = 20261002
REVIEW_FRACTION = 0.01


def capacity(y, scores, keys, fraction=REVIEW_FRACTION) -> dict:
    """Fixed capacity ranking; label-independent hash resolves ties reproducibly."""
    k = max(1, math.ceil(len(y) * fraction))
    chosen = np.lexsort((np.asarray(keys), -np.asarray(scores)))[:k]
    positives = int(np.sum(y))
    tp = int(np.sum(np.asarray(y)[chosen]))
    return {
        "review_fraction": fraction,
        "reviewed": k,
        "true_positives": tp,
        "false_positives": k - tp,
        "precision": tp / k,
        "recall": tp / positives if positives else None,
        "false_positive_rate": (k - tp) / (len(y) - positives) if len(y) > positives else None,
        "recall_wilson_95": wilson(tp, positives),
        "precision_wilson_95": wilson(tp, k),
    }


def wilson(success: int, total: int) -> list | None:
    if not total:
        return None
    z = 1.959963984540054
    p = success / total
    denominator = 1 + z * z / total
    center = (p + z * z / (2 * total)) / denominator
    margin = z * math.sqrt(p * (1 - p) / total + z * z / (4 * total * total)) / denominator
    return [max(0, center - margin), min(1, center + margin)]


def metrics(y, scores, keys) -> dict:
    y, scores = np.asarray(y), np.asarray(scores)
    clipped = np.clip(scores, 1e-12, 1 - 1e-12)
    bins = []
    # Quantile bins preserve visibility at ~0.1% prevalence, unlike broad 0.1 bins.
    for indices in np.array_split(np.lexsort((np.asarray(keys), scores)), 10):
        if len(indices):
            bins.append(
                {
                    "rows": len(indices),
                    "mean_probability": float(np.mean(scores[indices])),
                    "observed_rate": float(np.mean(y[indices])),
                }
            )
    return {
        "rows": len(y),
        "fraud_labels": int(y.sum()),
        "prevalence": float(y.mean()),
        "average_precision": float(average_precision_score(y, scores)) if y.sum() else None,
        "roc_auc": float(roc_auc_score(y, scores)) if 0 < y.sum() < len(y) else None,
        "brier": float(brier_score_loss(y, clipped)),
        "log_loss": float(log_loss(y, clipped, labels=[0, 1])),
        "mean_probability": float(scores.mean()),
        "calibration_deciles": bins,
        "capacity_1pct": capacity(y, scores, keys),
        "capacity_5pct": capacity(y, scores, keys, 0.05),
    }


def logit(probabilities):
    p = np.clip(probabilities, 1e-9, 1 - 1e-9)
    return np.log(p / (1 - p)).reshape(-1, 1)


def export_logistic(model, calibration, path: Path, metadata: dict) -> None:
    preprocessing, estimator = model.steps[0][1], model.steps[1][1]
    numeric = preprocessing.named_transformers_["numeric"]
    categorical = preprocessing.named_transformers_["categorical"]
    document = {
        **metadata,
        "kind": "logistic",
        "numeric": NUMERIC,
        "categorical": CATEGORICAL,
        "mean": numeric.mean_.tolist(),
        "scale": numeric.scale_.tolist(),
        "categories": [category.tolist() for category in categorical.categories_],
        "coefficients": estimator.coef_[0].tolist(),
        "intercept": float(estimator.intercept_[0]),
        "calibration_coefficient": float(calibration.coef_[0, 0]),
        "calibration_intercept": float(calibration.intercept_[0]),
    }
    path.write_text(json.dumps(document, indent=2) + "\n")


def run(features: Path, output: Path, public_output: Path) -> dict:
    output.mkdir(parents=True, exist_ok=True)
    public_output.mkdir(parents=True, exist_ok=True)
    start = time.perf_counter()
    with duckdb.connect() as con:
        con.execute("SET threads=4")
        con.execute("SET memory_limit='2GB'")
        frame = con.execute(
            """
            SELECT *, md5(transaction_id) AS tie_key FROM read_parquet(?)
            WHERE split <> 'train' OR label=1 OR substr(md5(transaction_id),1,1) IN ('0','1')
            ORDER BY available_at,transaction_id
        """,
            [str(features)],
        ).fetchdf()
        training_population = con.execute(
            """
            SELECT count(*),sum(label) FROM read_parquet(?) WHERE split='train'
        """,
            [str(features)],
        ).fetchone()
    for col in CATEGORICAL:
        frame[col] = frame[col].fillna("missing").astype(str)
    partitions = {
        name: frame[frame.split == name].copy()
        for name in ["train", "calibration", "validation", "test"]
    }
    train = partitions["train"]
    x_columns = NUMERIC + CATEGORICAL
    weights = np.where(train.label.to_numpy() == 1, 1.0, 8.0)
    prevalence = training_population[1] / training_population[0]
    print(f"Training on {len(train):,} rows; full population {training_population}", flush=True)
    preprocessing = ColumnTransformer(
        [
            ("numeric", StandardScaler(), NUMERIC),
            (
                "categorical",
                OneHotEncoder(handle_unknown="ignore", sparse_output=False),
                CATEGORICAL,
            ),
        ]
    )
    logistic = make_pipeline(preprocessing, LogisticRegression(max_iter=500, random_state=SEED))
    fit_start = time.perf_counter()
    logistic.fit(train[x_columns], train.label, logisticregression__sample_weight=weights)
    logistic_time = time.perf_counter() - fit_start
    print(f"Logistic trained in {logistic_time:.1f}s", flush=True)
    cat = CatBoostClassifier(
        iterations=180,
        depth=5,
        learning_rate=0.05,
        loss_function="Logloss",
        random_seed=SEED,
        thread_count=4,
        verbose=False,
        allow_writing_files=False,
        l2_leaf_reg=8,
    )
    fit_start = time.perf_counter()
    cat.fit(train[x_columns], train.label, cat_features=CATEGORICAL, sample_weight=weights)
    cat_time = time.perf_counter() - fit_start
    cat.save_model(str(output / "catboost.cbm"))
    print(f"CatBoost trained in {cat_time:.1f}s", flush=True)
    raw_models = {"logistic": logistic, "catboost": cat}
    calibrators = {}
    calibration_frame = partitions["calibration"]
    for name, model in raw_models.items():
        calibrator = LogisticRegression(C=1e6, max_iter=500, random_state=SEED)
        raw = model.predict_proba(calibration_frame[x_columns])[:, 1]
        calibrator.fit(logit(raw), calibration_frame.label)
        calibrators[name] = calibrator
    predictions = {}

    def score_partition(partition):
        group = partitions[partition]
        predictions[partition] = {
            "constant": np.full(len(group), prevalence),
            # A fixed, predeclared anomaly rule, not a calibrated fraud probability.
            "amount_history_rule": np.where(group.log_amount_ratio > math.log(4), 0.01, prevalence),
        }
        for name, model in raw_models.items():
            raw = model.predict_proba(group[x_columns])[:, 1]
            predictions[partition][name + "_raw"] = raw
            predictions[partition][name] = calibrators[name].predict_proba(logit(raw))[:, 1]
        return {
            name: metrics(group.label, scores, group.tie_key)
            for name, scores in predictions[partition].items()
        }

    results = {"validation": score_partition("validation")}
    # Selection uses February only; test is reported after the decision is fixed.
    validation = results["validation"]
    baseline_ap = validation["constant"]["average_precision"]
    candidates = [
        name
        for name in ["logistic", "catboost"]
        if validation[name]["average_precision"] > 1.2 * baseline_ap
        and validation[name]["capacity_1pct"]["precision_wilson_95"][0]
        > validation[name]["prevalence"]
    ]
    selected = (
        max(candidates, key=lambda name: validation[name]["average_precision"])
        if candidates
        else "constant"
    )
    print(f"Development promotion decision fixed: {selected}; evaluating final test", flush=True)
    results["test"] = score_partition("test")
    metadata = {
        "model_version": "fraud-cpu-20261002-v1",
        "feature_version": FEATURE_VERSION,
        "selected_model": selected,
        "training_prevalence": prevalence,
        "domain": "organizer_synthetic_historical",
        "training_end_exclusive": "2026-01-01",
        "evaluation_end": str(frame.available_at.max()),
        "currencies": sorted(train.currency.unique().tolist()),
        "limitations": [
            "Synthetic retrospective labels; no label-adjudication timestamps",
            "No evidence of production generalization or causal fraud explanations",
            "Never override a customer-reported unrecognized payment or scam",
        ],
    }
    if selected == "constant":
        metadata["limitations"].insert(0, "No learned model passed development promotion gates")
    export_logistic(logistic, calibrators["logistic"], output / "logistic.json", metadata)
    from factored_banking.fraud import logistic_probability

    exported_candidate = json.loads((output / "logistic.json").read_text())
    parity_rows = partitions["validation"].iloc[:200]
    exported_scores = np.array(
        [
            logistic_probability(exported_candidate, record)
            for record in parity_rows[x_columns].to_dict(orient="records")
        ]
    )
    expected_scores = predictions["validation"]["logistic"][: len(parity_rows)]
    parity_error = float(np.max(np.abs(exported_scores - expected_scores)))
    if parity_error > 1e-10:
        raise ValueError(f"Export parity failed: {parity_error}")
    if selected == "logistic":
        artifact = json.loads((output / "logistic.json").read_text())
    elif selected == "catboost":
        # Native CatBoost loader is used, never a hand-written tree interpreter.
        cat.save_model(str(public_output / "fraud-catboost.cbm"))
        artifact = {
            **metadata,
            "kind": "catboost",
            "model_file": "fraud-catboost.cbm",
            "numeric": NUMERIC,
            "categorical": CATEGORICAL,
            "calibration_coefficient": float(calibrators["catboost"].coef_[0, 0]),
            "calibration_intercept": float(calibrators["catboost"].intercept_[0]),
        }
    else:
        artifact = {**metadata, "kind": "constant", "probability": prevalence}
    artifact_path = public_output / "fraud-model.json"
    artifact_path.write_text(json.dumps(artifact, indent=2) + "\n")
    test = partitions["test"]
    selected_scores = predictions["test"][selected]
    slices = {}
    for column in [
        "currency",
        "channel",
        "customer_country_slice",
        "gender_slice",
        "seen_customer_in_train",
        "event_after_process_date",
    ]:
        slices[column] = {}
        for value in sorted(test[column].dropna().unique(), key=str):
            mask = (test[column] == value).to_numpy()
            slice_y = test.label.to_numpy()[mask]
            # Do not imply stable per-slice precision when there are very few labels.
            slices[column][str(value)] = metrics(
                slice_y, selected_scores[mask], test.tie_key.to_numpy()[mask]
            )
    diagnostics = {}
    supplied = test.supplied_score_diagnostic_only.fillna(0).to_numpy() > 30
    y = test.label.to_numpy()
    diagnostics["supplied_score_gt_30_not_independent"] = {
        "true_positives": int(np.sum(supplied & (y == 1))),
        "false_positives": int(np.sum(supplied & (y == 0))),
        "false_negatives": int(np.sum(~supplied & (y == 1))),
        "missing_score_rows": int(test.supplied_score_diagnostic_only.isna().sum()),
        "excluded_reason": "Unknown provenance and unexplained label shortcut; not a candidate",
    }
    report = {
        "experiment_version": 1,
        "seed": SEED,
        "feature_version": FEATURE_VERSION,
        "feature_sha256": sha256(features),
        "training_source_sha256": sha256(Path(__file__)),
        "libraries": {
            name: importlib.metadata.version(name)
            for name in ["numpy", "pandas", "scikit-learn", "catboost", "duckdb"]
        },
        "features": {"numeric": NUMERIC, "categorical": CATEGORICAL},
        "excluded": [
            "is_fraud",
            "fraud_score",
            "amount_usd",
            "current customer/product snapshots",
            "customer and transaction identifiers",
            "future/simultaneous events",
            "status/response code",
            "unlinked transcripts and digital sessions",
        ],
        "split_clock": "max(event_at, process_date + 1 day); naive timestamps, timezone unknown",
        "label_availability_assumption": "Labels available at offline fitting; unproven",
        "training_population": {
            "rows": training_population[0],
            "fraud_labels": training_population[1],
        },
        "training_sample": {
            "rows": len(train),
            "fraud_labels": int(train.label.sum()),
            "negative_inclusion_probability": 0.125,
            "negative_inverse_propensity_weight": 8,
            "sampling": "MD5 transaction ID first hex digit 0 or 1; all positives",
        },
        "partitions": {
            name: {"rows": len(group), "fraud_labels": int(group.label.sum())}
            for name, group in partitions.items()
        },
        "calibration": "Sigmoid January; model selection February; final March+ test",
        "promotion_gate": "February AP > 1.2x prior and precision@1% Wilson lower > prevalence",
        "selected": selected,
        "metrics": results,
        "test_slices_selected": slices,
        "unseen_customer_test_rows": int((~test.seen_customer_in_train).sum()),
        "unseen_customer_limitation": "No unseen-customer generalization claim when slice is empty",
        "diagnostics": diagnostics,
        "fit_seconds": {"logistic": logistic_time, "catboost": cat_time},
        "runtime_artifact_sha256": sha256(artifact_path),
        "logistic_export_max_absolute_error": parity_error,
        "elapsed_seconds": time.perf_counter() - start,
        "limitations": metadata["limitations"],
        "hyperparameters": {"logistic": {"C": 1, "max_iter": 500}, "catboost": cat.get_params()},
    }
    (output / "ml-report.json").write_text(json.dumps(report, indent=2) + "\n")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--features", type=Path, default=Path("artifacts/curated/fraud-features.parquet")
    )
    parser.add_argument("--output", type=Path, default=Path("artifacts/models"))
    parser.add_argument("--public-output", type=Path, default=Path("src/factored_banking/models"))
    args = parser.parse_args()
    report = run(args.features, args.output, args.public_output)
    print(
        json.dumps(
            {
                "selected": report["selected"],
                "test": report["metrics"]["test"],
                "seconds": report["elapsed_seconds"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
