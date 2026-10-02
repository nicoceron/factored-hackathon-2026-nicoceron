"""Curate organizer data with explicit quarantine and a conservative replay clock.

All row-level output stays in ignored local artifacts. Public reports are aggregate only.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
from contextlib import closing
from pathlib import Path
from tempfile import TemporaryDirectory

import duckdb

CONTRACT_VERSION = "transaction-support-v1"
FEATURE_VERSION = "strict-prior-30d-v1"
REQUIRED = {
    "customers": {"customer_id", "country", "gender"},
    "products": {"product_id", "customer_id", "currency"},
    "transactions": {
        "transaction_id",
        "customer_id",
        "product_id",
        "currency",
        "amount",
        "transaction_date",
        "process_date",
        "transaction_type",
        "transaction_category",
        "channel",
        "transaction_country",
        "transaction_status",
        "merchant_name",
        "is_fraud",
        "fraud_score",
        "filename",
    },
}
CATEGORICAL = [
    "currency",
    "transaction_type",
    "transaction_category",
    "channel",
    "transaction_country",
]
NUMERIC = ["log_amount", "hour", "weekday", "log_prior_count_30d", "log_amount_ratio"]


def sha256(path: Path) -> str:
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def curate(con: duckdb.DuckDBPyConnection) -> dict:
    """Build temporary validated views over tables in `con`, without mutating the audit."""
    for table, expected in REQUIRED.items():
        found = {row[0] for row in con.execute(f"DESCRIBE {table}").fetchall()}
        missing = expected - found
        if missing:
            raise ValueError(f"{table}: missing required columns: {sorted(missing)}")
    con.execute("""
        CREATE OR REPLACE TEMP VIEW customer_contract AS
        SELECT *, CASE WHEN customer_id IS NULL OR trim(customer_id) = '' THEN 'missing_key'
          WHEN count(*) OVER (PARTITION BY customer_id) > 1 THEN 'duplicate_key'
          ELSE NULL END AS quarantine_reason FROM customers
    """)
    con.execute("""
        CREATE OR REPLACE TEMP VIEW product_contract AS
        SELECT *, CASE WHEN product_id IS NULL OR trim(product_id) = '' THEN 'missing_key'
          WHEN count(*) OVER (PARTITION BY product_id) > 1 THEN 'duplicate_key'
          WHEN currency IS NULL OR NOT regexp_full_match(currency, '[A-Z]{3}')
            THEN 'invalid_currency'
          WHEN NOT EXISTS (SELECT 1 FROM customer_contract c
            WHERE c.customer_id=products.customer_id AND c.quarantine_reason IS NULL)
            THEN 'invalid_customer_reference'
          ELSE NULL END AS quarantine_reason FROM products
    """)
    con.execute("""
        CREATE OR REPLACE TEMP TABLE transaction_contract AS
        WITH typed AS (
          SELECT *, try_cast(amount AS DOUBLE) AS typed_amount,
            try_cast(transaction_date AS TIMESTAMP) AS event_at,
            try_cast(process_date AS DATE) AS processed_on,
            count(*) OVER (PARTITION BY transaction_id) AS copies
          FROM transactions
        )
        SELECT *,
          CASE WHEN transaction_id IS NULL OR trim(transaction_id)='' THEN 'missing_key'
            WHEN copies > 1 THEN 'duplicate_key'
            WHEN event_at IS NULL OR processed_on IS NULL THEN 'invalid_time'
            WHEN typed_amount IS NULL OR NOT isfinite(typed_amount) OR typed_amount < 0
              THEN 'invalid_amount'
            WHEN currency IS NULL OR NOT regexp_full_match(currency, '[A-Z]{3}')
              THEN 'invalid_currency'
            WHEN NOT EXISTS (SELECT 1 FROM product_contract p
              WHERE p.product_id=typed.product_id AND p.customer_id=typed.customer_id
                AND p.currency=typed.currency AND p.quarantine_reason IS NULL)
              THEN 'invalid_product_ownership_currency'
            ELSE NULL END AS quarantine_reason,
          event_at::DATE > processed_on AS event_after_process_date,
          greatest(event_at, processed_on + INTERVAL 1 DAY) AS available_at
        FROM typed
    """)
    con.execute("""
        CREATE OR REPLACE TEMP VIEW serving_transactions AS
        SELECT transaction_id, customer_id, product_id, amount, currency,
          event_at AS transaction_date, processed_on AS process_date, available_at,
          transaction_type, transaction_category, channel, transaction_country,
          transaction_status, merchant_name, event_after_process_date,
          'organizer:' || regexp_replace(filename, '^.*[/]data[/]raw[/]', '')
            || '#' || transaction_id AS source_ref,
          'organizer_synthetic_historical' AS provenance
        FROM transaction_contract WHERE quarantine_reason IS NULL
    """)
    tables = {}
    for table, view in [
        ("customers", "customer_contract"),
        ("products", "product_contract"),
        ("transactions", "transaction_contract"),
    ]:
        tables[table] = {
            "rows": con.execute(f"SELECT count(*) FROM {view}").fetchone()[0],
            "accepted": con.execute(
                f"SELECT count(*) FROM {view} WHERE quarantine_reason IS NULL"
            ).fetchone()[0],
            "quarantined_by_primary_reason": dict(
                con.execute(
                    f"SELECT quarantine_reason,count(*) FROM {view} "
                    "WHERE quarantine_reason IS NOT NULL GROUP BY 1 ORDER BY 1"
                ).fetchall()
            ),
        }
    return {
        "contract_version": CONTRACT_VERSION,
        "tables": tables,
        "event_after_process_date": con.execute(
            "SELECT count(*) FROM transaction_contract WHERE event_after_process_date"
        ).fetchone()[0],
        "availability_assumption": "max(event_at, process_date + 1 day); dates have no timezone",
        "timestamp_anomaly_policy": "Preserve and flag; do not claim a timezone correction",
        "scope": "Customer/product keys and transaction fields; other tables remain audit-only",
    }


def create_features(con: duckdb.DuckDBPyConnection) -> None:
    """Strict-prior RANGE excludes the current row AND every simultaneous peer."""
    con.execute("""
        CREATE OR REPLACE TEMP TABLE fraud_features AS
        WITH numeric_transactions AS (
          SELECT * REPLACE (try_cast(amount AS DOUBLE) AS amount),
            try_cast(amount AS DECIMAL(38,8)) AS history_amount
          FROM serving_transactions
        ), history AS (
          SELECT *, count(*) OVER prior AS prior_count_30d,
            sum(history_amount) OVER prior / nullif(count(*) OVER prior,0)
              AS prior_mean_amount_30d
          FROM numeric_transactions
          WINDOW prior AS (PARTITION BY customer_id,currency ORDER BY available_at
            RANGE BETWEEN INTERVAL 30 DAYS PRECEDING AND INTERVAL 1 MICROSECOND PRECEDING)
        )
        SELECT h.transaction_id,h.customer_id,h.available_at,h.transaction_date,
          h.process_date,h.event_after_process_date,h.amount,
          h.prior_count_30d,h.prior_mean_amount_30d,
          ln(1+h.amount) AS log_amount,
          date_part('hour',h.transaction_date) AS hour,
          date_part('isodow',h.transaction_date) AS weekday,
          ln(1+h.prior_count_30d) AS log_prior_count_30d,
          ln(1+h.amount / greatest(coalesce(h.prior_mean_amount_30d,h.amount),1))
            AS log_amount_ratio,
          h.currency,h.transaction_type,coalesce(h.transaction_category,'missing')
            AS transaction_category,h.channel,h.transaction_country,
          CASE WHEN h.available_at < TIMESTAMP '2026-01-01' THEN 'train'
               WHEN h.available_at < TIMESTAMP '2026-02-01' THEN 'calibration'
               WHEN h.available_at < TIMESTAMP '2026-03-01' THEN 'validation'
               ELSE 'test' END AS split,
          CASE WHEN t.is_fraud='True' THEN 1 WHEN t.is_fraud='False' THEN 0 END AS label,
          try_cast(t.fraud_score AS DOUBLE) AS supplied_score_diagnostic_only,
          c.country AS customer_country_slice,c.gender AS gender_slice,
          EXISTS (SELECT 1 FROM serving_transactions seen
            WHERE seen.customer_id=h.customer_id
              AND seen.available_at < TIMESTAMP '2026-01-01') AS seen_customer_in_train
        FROM history h JOIN transaction_contract t USING(transaction_id)
        JOIN customer_contract c ON c.customer_id=h.customer_id
        WHERE t.is_fraud IN ('True','False')
    """)


def export_serving(con: duckdb.DuckDBPyConnection, output: Path) -> int:
    """Atomic local SQLite export. Caller must still enforce session authorization."""
    temporary = output.with_suffix(".building.sqlite")
    temporary.unlink(missing_ok=True)
    source = con.execute("SELECT * FROM serving_transactions ORDER BY transaction_id")
    columns = [item[0] for item in source.description]
    with closing(sqlite3.connect(temporary)) as target, target:
        target.execute("PRAGMA journal_mode=OFF")
        # Monetary evidence retains the exact source decimal string. Floating-point
        # transforms exist only in the offline ML feature table, never record tools.
        definitions = ",".join(f'"{name}" TEXT' for name in columns)
        target.execute(f"CREATE TABLE transactions ({definitions})")
        count = 0
        while batch := source.fetchmany(10000):
            target.executemany(
                "INSERT INTO transactions VALUES (" + ",".join("?" for _ in columns) + ")",
                [
                    tuple(
                        str(value)
                        if value is not None and not isinstance(value, (str, int, float))
                        else value
                        for value in row
                    )
                    for row in batch
                ],
            )
            count += len(batch)
        target.execute("CREATE UNIQUE INDEX transaction_id ON transactions(transaction_id)")
        target.execute("CREATE INDEX customer_id ON transactions(customer_id)")
        target.execute("CREATE TABLE metadata (key TEXT PRIMARY KEY,value TEXT)")
        target.executemany(
            "INSERT INTO metadata VALUES (?,?)",
            [
                ("contract_version", CONTRACT_VERSION),
                ("provenance", "organizer_synthetic_historical"),
                ("source_freshness", "historical; not live bank data"),
            ],
        )
    # Read the committed staging database through a new handle before promotion.
    with closing(sqlite3.connect(temporary)) as verification:
        if verification.execute("SELECT count(*) FROM transactions").fetchone()[0] != count:
            raise RuntimeError("Serving snapshot read-back count mismatch")
    temporary.replace(output)
    return count


def run(database: Path, output: Path, export_sqlite: bool = False) -> dict:
    output.mkdir(parents=True, exist_ok=True)
    with (
        TemporaryDirectory(prefix="duckdb-", dir=output) as temporary,
        duckdb.connect(str(database), read_only=True) as con,
    ):
        con.execute("SET temp_directory=?", [temporary])
        # Fixed-point history sums avoid order-dependent parallel float accumulation.
        con.execute("SET threads=4")
        con.execute("SET memory_limit='3GB'")
        report = curate(con)
        print("Contracts evaluated; building strict-prior features", flush=True)
        create_features(con)
        feature_path = output / "fraud-features.parquet"
        con.execute(
            "COPY (SELECT * FROM fraud_features ORDER BY transaction_id) "
            "TO ? (FORMAT PARQUET, COMPRESSION ZSTD)",
            [str(feature_path)],
        )
        con.execute(
            "COPY (SELECT * FROM transaction_contract WHERE quarantine_reason IS NOT NULL) "
            "TO ? (FORMAT PARQUET, COMPRESSION ZSTD)",
            [str(output / "quarantine.parquet")],
        )
        report["feature_version"] = FEATURE_VERSION
        report["feature_sha256"] = sha256(feature_path)
        report["partitions"] = {
            split: {"rows": rows, "fraud_labels": labels}
            for split, rows, labels in con.execute(
                "SELECT split,count(*),sum(label) FROM fraud_features GROUP BY 1 ORDER BY 1"
            ).fetchall()
        }
        report["unusable_labels"] = con.execute(
            "SELECT count(*) FROM transaction_contract WHERE quarantine_reason IS NULL "
            "AND (is_fraud IS NULL OR is_fraud NOT IN ('True','False'))"
        ).fetchone()[0]
        if export_sqlite:
            report["serving_rows"] = export_serving(con, output / "serving.sqlite")
    profile = database.with_suffix(".json")
    if profile.exists():
        report["source_manifest_sha256"] = json.loads(profile.read_text()).get("manifest_sha256")
    report["pipeline_source_sha256"] = sha256(Path(__file__))
    report["source_database_sha256"] = sha256(database)
    (output / "pipeline-report.json").write_text(json.dumps(report, indent=2) + "\n")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, default=Path("artifacts/data-profile.duckdb"))
    parser.add_argument("--output", type=Path, default=Path("artifacts/curated"))
    parser.add_argument("--export-sqlite", action="store_true")
    args = parser.parse_args()
    print(json.dumps(run(args.database, args.output, args.export_sqlite), indent=2))


if __name__ == "__main__":
    main()
