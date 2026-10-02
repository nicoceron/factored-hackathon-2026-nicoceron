import sqlite3
from datetime import datetime

import duckdb
import pytest

from factored_banking.data_pipeline import REQUIRED, create_features, curate, export_serving


def source_database(rows, customers=None, products=None):
    con = duckdb.connect()
    customer_rows = customers or [("C1", "Colombia", "F")]
    product_rows = products or [("P1", "C1", "COP")]
    con.execute("CREATE TABLE customers(customer_id VARCHAR,country VARCHAR,gender VARCHAR)")
    con.executemany("INSERT INTO customers VALUES (?,?,?)", customer_rows)
    con.execute("CREATE TABLE products(product_id VARCHAR,customer_id VARCHAR,currency VARCHAR)")
    con.executemany("INSERT INTO products VALUES (?,?,?)", product_rows)
    columns = sorted(REQUIRED["transactions"])
    con.execute("CREATE TABLE transactions(" + ",".join(f"{c} VARCHAR" for c in columns) + ")")
    defaults = {
        "customer_id": "C1",
        "product_id": "P1",
        "currency": "COP",
        "amount": "100",
        "transaction_date": "2025-12-01 10:00:00",
        "process_date": "2025-12-01",
        "transaction_type": "Purchase",
        "transaction_category": "Food",
        "channel": "POS",
        "transaction_country": "Colombia",
        "transaction_status": "Approved",
        "merchant_name": "Team generated fixture",
        "is_fraud": "False",
        "fraud_score": "10",
        "filename": "data/raw/transactions/fixture.csv",
    }
    con.executemany(
        "INSERT INTO transactions VALUES (" + ",".join("?" for _ in columns) + ")",
        [tuple({**defaults, **row}.get(c) for c in columns) for row in rows],
    )
    return con


def test_quarantine_all_duplicate_keys_and_invalid_ownership():
    with source_database(
        [
            {"transaction_id": "T1"},
            {"transaction_id": "T1", "amount": "2"},
            {"transaction_id": "T2", "customer_id": "OTHER"},
            {"transaction_id": "T3", "amount": "nan"},
            {"transaction_id": "T4", "transaction_date": "not-date"},
            {"transaction_id": "T5"},
        ]
    ) as con:
        report = curate(con)
        assert report["tables"]["transactions"]["accepted"] == 1
        assert report["tables"]["transactions"]["quarantined_by_primary_reason"] == {
            "duplicate_key": 2,
            "invalid_product_ownership_currency": 1,
            "invalid_amount": 1,
            "invalid_time": 1,
        }


def test_ambiguous_parent_quarantines_children():
    with source_database(
        [{"transaction_id": "T1"}], customers=[("C1", "Colombia", "F"), ("C1", "Colombia", "M")]
    ) as con:
        result = curate(con)
        assert result["tables"]["transactions"]["accepted"] == 0
        assert result["tables"]["products"]["accepted"] == 0


def test_history_excludes_future_and_simultaneous_events_and_other_currency():
    with source_database(
        [
            {
                "transaction_id": "PAST",
                "amount": "50",
                "transaction_date": "2025-11-30 01:00:00",
                "process_date": "2025-11-30",
            },
            {"transaction_id": "CURRENT", "amount": "100"},
            {"transaction_id": "SIMULTANEOUS", "amount": "10000"},
            {
                "transaction_id": "FUTURE",
                "amount": "900000",
                "transaction_date": "2025-12-02",
                "process_date": "2025-12-02",
            },
            {
                "transaction_id": "OTHER-CURRENCY",
                "product_id": "P2",
                "currency": "USD",
                "amount": "5000",
                "transaction_date": "2025-11-30",
                "process_date": "2025-11-30",
            },
        ],
        products=[("P1", "C1", "COP"), ("P2", "C1", "USD")],
    ) as con:
        curate(con)
        create_features(con)
        rows = dict(
            (row[0], row[1:])
            for row in con.execute(
                "SELECT transaction_id,prior_count_30d,prior_mean_amount_30d FROM fraud_features"
            ).fetchall()
        )
        assert rows["CURRENT"] == (1, 50.0)
        assert rows["SIMULTANEOUS"] == (1, 50.0)
        assert rows["PAST"][0] == 0
        assert rows["OTHER-CURRENCY"][0] == 0


def test_timestamps_preserved_and_labels_excluded_from_serving(tmp_path):
    with source_database(
        [{"transaction_id": "T1", "transaction_date": "2025-12-03 14:00:00"}]
    ) as con:
        report = curate(con)
        assert report["event_after_process_date"] == 1
        row = con.execute("SELECT available_at FROM serving_transactions").fetchone()
        assert row[0] == datetime(2025, 12, 3, 14)
        cols = {row[0] for row in con.execute("DESCRIBE serving_transactions").fetchall()}
        assert not {"is_fraud", "fraud_score", "gender", "email", "product_number"} & cols
        assert export_serving(con, tmp_path / "serving.sqlite") == 1


def test_missing_schema_fails_before_output():
    with duckdb.connect() as con:
        con.execute("CREATE TABLE customers(customer_id VARCHAR)")
        with pytest.raises(ValueError, match="missing required columns"):
            curate(con)


def test_serving_export_preserves_exact_decimal_evidence(tmp_path):
    exact = "123456789.12000001"
    with source_database([{"transaction_id": "T1", "amount": exact}]) as con:
        curate(con)
        path = tmp_path / "serving.sqlite"
        export_serving(con, path)
    with sqlite3.connect(path) as database:
        assert database.execute("SELECT amount FROM transactions").fetchone()[0] == exact


def test_full_snapshot_rebuild_applies_changes_deletions_and_late_arrivals(tmp_path):
    """Team-generated update fixture; no change-feed exists in the organizer snapshot."""
    path = tmp_path / "serving.sqlite"
    with source_database(
        [
            {"transaction_id": "CHANGE", "amount": "100.00"},
            {"transaction_id": "DELETE", "amount": "20.00"},
        ]
    ) as initial:
        curate(initial)
        export_serving(initial, path)
    with source_database(
        [
            {"transaction_id": "CHANGE", "amount": "125.00"},
            {
                "transaction_id": "LATE",
                "amount": "50.00",
                "transaction_date": "2025-11-15 12:00:00",
                "process_date": "2025-12-05",
            },
        ]
    ) as replacement:
        curate(replacement)
        assert export_serving(replacement, path) == 2
    with sqlite3.connect(path) as database:
        assert database.execute(
            "SELECT transaction_id,amount FROM transactions ORDER BY transaction_id"
        ).fetchall() == [("CHANGE", "125.00"), ("LATE", "50.00")]
        assert database.execute(
            "SELECT transaction_date,available_at FROM transactions WHERE transaction_id='LATE'"
        ).fetchone() == ("2025-11-15 12:00:00", "2025-12-06 00:00:00")


def test_failed_snapshot_export_preserves_previous_committed_file(tmp_path):
    """Inject failure after a staging batch, before atomic snapshot replacement."""
    path = tmp_path / "serving.sqlite"
    with source_database([{"transaction_id": "PREVIOUS", "amount": "100.00"}]) as con:
        curate(con)
        export_serving(con, path)
    original = path.read_bytes()

    class InterruptedSource:
        description = [("transaction_id",), ("customer_id",), ("amount",)]
        batches = 0

        def execute(self, _query):
            return self

        def fetchmany(self, _count):
            self.batches += 1
            if self.batches == 1:
                return [("NEW", "C1", "500.00")]
            raise RuntimeError("Injected source interruption")

    with pytest.raises(RuntimeError, match="Injected source interruption"):
        export_serving(InterruptedSource(), path)
    assert path.read_bytes() == original
    with sqlite3.connect(path) as database:
        assert database.execute("SELECT transaction_id FROM transactions").fetchall() == [
            ("PREVIOUS",)
        ]
