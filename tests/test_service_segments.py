"""Counterbalance permitted record attributes without inventing customer demographics."""

from factored_banking.language import classify
from factored_banking.service_segments import load_protocol, segment_records
from factored_banking.system_evaluation import run_workload


def test_segments_cross_language_status_currency_and_keep_scoped_record_ids():
    spec, manifest = load_protocol()
    assert manifest["total_replays_per_system"] == 840
    for segment in spec["segments"]:
        for language in ("es", "pt"):
            rows = segment_records(f"demo-{language}", segment)
            assert rows[0]["id"] == f"TX-{language.upper()}-101"
            assert rows[0]["status"] == segment["transaction_status"]
            assert rows[0]["currency"] == segment["currency"]
            assert rows[0]["country"] == "Colombia"
            assert rows[0]["provenance"] == "team_authored_synthetic"
        assert segment_records("not-an-authorized-customer", segment) == []


def test_grounded_status_changes_with_each_authorized_fixture():
    spec, _ = load_protocol()
    rows = [
        {
            "id": f"status-{language}",
            "semantic_group": "status-check",
            "text": message,
            "language": language,
            "intent": "transaction_status",
        }
        for language, message in (
            ("es", "Quiero consultar el estado de mi pago."),
            ("pt", "Quero consultar o estado do meu pagamento."),
        )
    ]
    for segment in spec["segments"]:

        def records(customer, selected=segment):
            return segment_records(customer, selected)

        report, results = run_workload(rows, classify, records_factory=records, run_faults=False)
        assert report["correct_outcomes"] == 2
        assert all(row["successful_automated_resolution"] for row in results)
        assert report["provider_usage"]["attempts"] == 0
