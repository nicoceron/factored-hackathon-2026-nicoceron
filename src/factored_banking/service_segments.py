"""Controlled, synthetic service-segment replay with explicit paired denominators.

Segments describe customers by the status/currency of their authorized first
transaction. They are not demographic labels or real customer populations.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from factored_banking.evaluation import RESOURCE, corpus, validate_corpus
from factored_banking.fixtures import transactions
from factored_banking.language import baseline_classify, classify
from factored_banking.system_evaluation import run_workload


def load_protocol():
    fixture = RESOURCE.joinpath("service_segment_fixtures.json").read_bytes()
    manifest = json.loads(RESOURCE.joinpath("service_segment_manifest.json").read_text())
    if hashlib.sha256(fixture).hexdigest() != manifest["fixture_sha256"]:
        raise ValueError("Frozen service-segment fixture mismatch")
    source = RESOURCE.joinpath("language_test.json").read_bytes()
    if hashlib.sha256(source).hexdigest() != manifest["language_test_sha256"]:
        raise ValueError("Service-segment workload changed after freeze")
    validate_corpus()
    spec = json.loads(fixture)
    expected = {
        (status, currency)
        for status in ("completed", "pending", "declined")
        for currency in ("COP", "USD")
    }
    actual = {(r["transaction_status"], r["currency"]) for r in spec["segments"]}
    if actual != expected or len(spec["segments"]) != len(expected):
        raise ValueError("Service segments must fully cross status and currency")
    return spec, manifest


def segment_records(customer, segment):
    """Preserve authenticated owner IDs while changing only authorized fixture facts."""
    rows = transactions(customer)
    if not rows:
        return rows
    row = rows[0]
    row.update(
        status=segment["transaction_status"],
        currency=segment["currency"],
        amount=segment["amount"],
        country="Colombia",
        source=f"claro-service-segments-v1/{segment['id']}/{row['id']}",
    )
    return rows


def investigate_disparities(strata, paired_results):
    """Paired differences, not independent-sample significance or fairness certification."""
    measures = (
        "outcome_accuracy",
        "safe_automated_resolution_rate_all_in_scope",
        "missed_required_handoffs",
        "unnecessary_handoff_proposals",
        "unauthorized_disclosure_or_action",
        "materially_wrong_outcomes",
    )
    ranges = {}
    for language in ("all", "es", "pt"):
        selected = [
            s if language == "all" else s["language_slices"][language] for s in strata.values()
        ]
        ranges[language] = {}
        for metric in measures:
            values = [s[metric] for s in selected if s[metric] is not None]
            ranges[language][metric] = {
                "minimum": min(values),
                "maximum": max(values),
                "max_minus_min": max(values) - min(values),
            }
    reference_id = "completed-cop"
    reference = {r["case_id"]: r for r in paired_results[reference_id]}
    paired = {}
    for segment, rows in paired_results.items():
        changes = []
        for row in rows:
            base = reference[row["case_id"]]
            for metric in ("correct_outcome", "verified_handoff", "materially_wrong_outcome"):
                if row.get(metric) != base.get(metric):
                    changes.append(
                        {
                            "case_id": row["case_id"],
                            "language": row["language"],
                            "metric": metric,
                            "reference": base.get(metric),
                            "segment": row.get(metric),
                        }
                    )
        paired[segment] = {"paired_cases": len(rows), "changed_outcomes": changes}
    differences = sum(len(value["changed_outcomes"]) for value in paired.values())
    return {
        "comparison_reference": reference_id,
        "ranges_across_status_currency_segments": ranges,
        "paired_comparisons": paired,
        "investigation": (
            "No paired routing/handoff/material-outcome differences were observed after changing "
            "authorized status/currency and counterbalancing language. Grounded answers were "
            "checked against the changed fixture in every transaction-status case. Shared "
            "linguistic errors therefore persist across strata, rather than disappearing."
            if differences == 0
            else "Paired differences are listed by case ID and outcome above. Their reference text "
            "and permitted record should be reviewed before changing a policy or model. "
            "This exposed replay must remain regression evidence after any correction."
        ),
        "limits": (
            "This controlled intervention isolates supported record attributes. It is not a "
            "sample of demographic/customer-tier groups, native-language validation, or a "
            "population disparity estimate. Translation and authoring biases remain."
        ),
    }


def evaluate_segments():
    spec, manifest = load_protocol()
    rows = corpus("test")
    report = {
        "version": "service-segments-grounded-case-lookup-v3",
        "workload_status": "controlled regression replay",
        "segment_definition": "customers by selected-transaction status/currency",
        "provenance": spec["provenance"],
        "protocol": manifest,
        "unique_utterances": len(rows),
        "replays_per_system": len(rows) * len(spec["segments"]),
        "record_sensitive_cases_per_stratum": sum(
            r["intent"] in {"transaction_status", "dispute"} for r in rows
        ),
        "limitations": [
            *spec["limitations"],
            "Current exposed regression uses the stronger v3 conversational case-lookup "
            "criterion; historical v1.1 totals used a different criterion.",
            "Frozen CASE-009 references are not replaced with the generated seed case ID; "
            "safe denial remains visible against the old case-status label.",
        ],
        "source_sha256": {
            name: hashlib.sha256(Path(__file__).parent.joinpath(name).read_bytes()).hexdigest()
            for name in (
                "service_segments.py",
                "system_evaluation.py",
                "api.py",
                "workflow.py",
                "references.py",
                "privacy.py",
                "language.py",
                "fixtures.py",
                "providers.py",
                "store.py",
                "policy.py",
                "fraud.py",
                "resources/language_model.json",
                "models/fraud-model.json",
            )
        },
        "systems": {},
    }
    for name, classifier in (("keyword_rules", baseline_classify), ("tfidf_logistic", classify)):
        strata, paired = {}, {}
        for segment in spec["segments"]:

            def records(customer, selected=segment):
                return segment_records(customer, selected)

            aggregate, results = run_workload(
                rows, classifier, records_factory=records, run_faults=False
            )
            strata[segment["id"]], paired[segment["id"]] = aggregate, results
            print(
                json.dumps(
                    {
                        "system": name,
                        "segment": segment["id"],
                        "correct": aggregate["correct_outcomes"],
                        "cases": aggregate["cases"],
                    }
                ),
                flush=True,
            )
        report["systems"][name] = {
            "strata": strata,
            "disparity_investigation": investigate_disparities(strata, paired),
            "provider_requests": sum(
                s["all_run_usage_including_setup_warmup_faults"]["attempts"]
                for s in strata.values()
            ),
            "execution_scope": "local classifiers and deterministic composer; no external provider",
        }
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output", type=Path, default=Path("artifacts/service-segment-evaluation.json")
    )
    args = parser.parse_args()
    report = evaluate_segments()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(f"Saved {args.output}")


if __name__ == "__main__":
    main()
