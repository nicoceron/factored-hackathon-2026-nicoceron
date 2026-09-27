"""Reproducible raw-data audit, not a cleaned serving dataset or model evaluation."""

import argparse
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

import duckdb

# Minimum audit contracts from the supplied dictionary. Full serving contracts are pending.
TABLES = {
    "customers": ("customer_id", "country", "segment", "last_updated"),
    "products": ("product_id", "customer_id", "currency", "current_balance", "last_updated"),
    "branches": ("branch_id",),
    "service_agents": ("agent_id",),
    "marketing_campaigns": ("campaign_id",),
    "transactions": (
        "transaction_id",
        "customer_id",
        "product_id",
        "transaction_date",
        "process_date",
        "currency",
        "amount",
        "transaction_status",
    ),
    "call_center_interactions": (
        "interaction_id",
        "customer_id",
        "interaction_date",
        "process_date",
        "contact_reason",
        "reason_category",
        "was_resolved",
        "was_escalated",
    ),
    "call_transcripts": (
        "transcript_id",
        "interaction_id",
        "customer_id",
        "full_text",
        "customer_text",
        "detected_language",
    ),
    "satisfaction_surveys": ("survey_id", "customer_id", "interaction_id"),
    "digital_events": ("event_id", "customer_id"),
    "complaints": (
        "complaint_id",
        "customer_id",
        "origin_interaction_id",
        "category",
        "description",
    ),
    "campaign_sends": ("send_id", "customer_id"),
    "daily_exchange_rates": ("date", "source_currency", "target_currency", "exchange_rate"),
}


def identifier(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def rows(con: duckdb.DuckDBPyConnection, sql: str) -> list[dict]:
    result = con.execute(sql)
    names = [column[0] for column in result.description]
    return [dict(zip(names, row, strict=True)) for row in result.fetchall()]


def load_table(con: duckdb.DuckDBPyConnection, name: str, paths: list[Path]) -> None:
    # Preserve source strings. Explicit casts in audit queries expose invalid values.
    con.execute(
        f"CREATE OR REPLACE TABLE {identifier(name)} AS "
        "SELECT * FROM read_csv(?, header=true, delim=',', all_varchar=true, "
        "union_by_name=true, filename=true, hive_partitioning=false, ignore_errors=false)",
        [[str(path) for path in paths]],
    )


def profile_table(con: duckdb.DuckDBPyConnection, name: str) -> dict:
    table = identifier(name)
    columns = [row[0] for row in con.execute(f"DESCRIBE {table}").fetchall()]
    missing = sorted(set(TABLES[name]) - set(columns))
    count = con.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
    report = {"rows": count, "columns": columns, "missing_required_columns": missing}
    if missing:
        report["contract_status"] = "failed"
        return report
    keys = list(TABLES[name][:1])
    if name == "daily_exchange_rates":
        keys = ["date", "source_currency", "target_currency"]
    key_columns = ", ".join(map(identifier, keys))
    nonnull = " AND ".join(f"{identifier(key)} IS NOT NULL" for key in keys)
    key_stats = rows(
        con,
        f"SELECT count(*) AS key_rows, count(*) FILTER (WHERE {nonnull}) AS nonnull_key_rows "
        f"FROM {table}",
    )[0]
    unique = con.execute(
        f"SELECT count(*) FROM (SELECT DISTINCT {key_columns} FROM {table} WHERE {nonnull})"
    ).fetchone()[0]
    report.update(
        primary_key=keys,
        null_key_rows=count - key_stats["nonnull_key_rows"],
        duplicate_key_excess_rows=key_stats["nonnull_key_rows"] - unique,
    )
    null_expressions = ", ".join(
        f"count(*) FILTER (WHERE {identifier(column)} IS NULL) AS {identifier(column)}"
        for column in columns
        if column != "filename"
    )
    report["null_counts"] = rows(con, f"SELECT {null_expressions} FROM {table}")[0]
    report["contract_status"] = (
        "failed" if report["null_key_rows"] or report["duplicate_key_excess_rows"] else "passed"
    )
    report["contract_scope"] = "Required column presence and primary key integrity only"
    for column in ("country", "currency", "detected_language", "contact_reason", "reason_category"):
        if column in columns:
            report[column + "_counts"] = rows(
                con,
                f"SELECT {identifier(column)} AS value, count(*) AS rows FROM {table} "
                f"GROUP BY 1 ORDER BY rows DESC, value NULLS LAST LIMIT 30",
            )
    for column in ("transaction_date", "interaction_date", "process_date", "last_updated"):
        if column in columns:
            field = identifier(column)
            report[column + "_quality"] = rows(
                con,
                f"SELECT min(try_cast({field} AS TIMESTAMP)) AS earliest, "
                f"max(try_cast({field} AS TIMESTAMP)) AS latest, "
                f"count(*) FILTER (WHERE {field} IS NOT NULL AND "
                f"try_cast({field} AS TIMESTAMP) IS NULL) AS invalid_rows FROM {table}",
            )[0]
    if name == "transactions":
        report["event_after_process_day_rows"] = con.execute(
            "SELECT count(*) FROM transactions WHERE "
            "cast(try_cast(transaction_date AS TIMESTAMP) AS DATE) > try_cast(process_date AS DATE)"
        ).fetchone()[0]
    if name == "call_center_interactions":
        report["historical_outcomes"] = rows(
            con,
            "SELECT was_resolved, was_escalated, count(*) AS rows "
            "FROM call_center_interactions GROUP BY 1, 2 ORDER BY 1, 2",
        )
    if name == "call_transcripts":
        report["text_coverage"] = rows(
            con,
            "SELECT count(*) AS rows, count(DISTINCT full_text) AS distinct_full_text, "
            "count(DISTINCT customer_text) AS distinct_customer_text, "
            "count(*) FILTER (WHERE regexp_matches(lower(coalesce(full_text, '')), "
            "'fraud|no reconoz|no autoriz|duplicad|reembolso|devoluci|disputa')) "
            "AS dispute_keyword_rows FROM call_transcripts",
        )[0]
        report["keyword_limit"] = (
            "Exploratory lexical check; not intent labels or dispute ground truth"
        )
    return report


def relation_quality(con: duckdb.DuckDBPyConnection, available: set[str]) -> dict:
    output = {}
    relations = [
        ("products", "customer_id", "customers", "customer_id"),
        ("transactions", "customer_id", "customers", "customer_id"),
        ("transactions", "product_id", "products", "product_id"),
        ("call_center_interactions", "customer_id", "customers", "customer_id"),
        ("call_transcripts", "customer_id", "customers", "customer_id"),
        ("call_transcripts", "interaction_id", "call_center_interactions", "interaction_id"),
        ("complaints", "customer_id", "customers", "customer_id"),
        ("complaints", "origin_interaction_id", "call_center_interactions", "interaction_id"),
    ]
    for child, fk, parent, pk in relations:
        if not {child, parent} <= available:
            continue
        # EXISTS prevents duplicate parent rows from multiplying counts.
        output[f"{child}.{fk}->{parent}.{pk}"] = rows(
            con,
            f"SELECT count(*) AS child_rows, "
            f"count(*) FILTER (WHERE c.{fk} IS NULL) AS null_fk_rows, "
            f"count(*) FILTER (WHERE c.{fk} IS NOT NULL AND NOT EXISTS "
            f"(SELECT 1 FROM {parent} p WHERE p.{pk}=c.{fk})) AS unmatched_nonnull_rows "
            f"FROM {child} c",
        )[0]
    if {"call_transcripts", "call_center_interactions"} <= available:
        output["transcript_customer_consistency"] = rows(
            con,
            "SELECT count(*) AS transcript_rows, count(*) FILTER (WHERE EXISTS "
            "(SELECT 1 FROM call_center_interactions i WHERE i.interaction_id=t.interaction_id "
            "AND i.customer_id=t.customer_id)) AS rows_with_matching_interaction_and_customer "
            "FROM call_transcripts t",
        )[0]
        output["customer_text_label_conflict"] = rows(
            con,
            "SELECT count(*) AS customer_text_groups, count(*) FILTER (WHERE categories>1) "
            "AS groups_with_multiple_reason_categories FROM "
            "(SELECT t.customer_text, count(DISTINCT i.reason_category) AS categories "
            "FROM call_transcripts t JOIN call_center_interactions i USING(interaction_id) "
            "GROUP BY 1)",
        )[0]
        output["balance_keyword_by_metadata"] = rows(
            con,
            "SELECT i.reason_category, count(*) AS rows, "
            "count(*) FILTER (WHERE lower(t.customer_text) LIKE '%saldo%') "
            "AS balance_keyword_rows FROM call_transcripts t "
            "JOIN call_center_interactions i USING(interaction_id) GROUP BY 1 ORDER BY 1",
        )
    if {"transactions", "products"} <= available:
        output["transaction_product_consistency"] = rows(
            con,
            "SELECT count(*) AS transaction_rows, count(*) FILTER (WHERE EXISTS "
            "(SELECT 1 FROM products p WHERE p.product_id=t.product_id "
            "AND p.customer_id=t.customer_id AND p.currency=t.currency)) "
            "AS rows_with_matching_product_customer_currency FROM transactions t",
        )[0]
    return output


def audit(data_dir: Path, output: Path, selected: list[str]) -> dict:
    output.parent.mkdir(parents=True, exist_ok=True)
    report = {
        "audit_version": 1,
        "generated_at": datetime.now(UTC).isoformat(),
        "duckdb_version": duckdb.__version__,
        "dataset_provenance": "Organizer-supplied synthetic data; documentation version 1.0.0",
        "scope": "Raw local files only; no corrections, serving readiness, or model claims",
        "tables": {},
    }
    manifest = []
    available = set()
    with duckdb.connect(str(output.with_suffix(".duckdb"))) as con:
        con.execute("SET memory_limit='2GB'")
        con.execute("SET threads=4")
        con.execute("SET preserve_insertion_order=false")
        for name in selected:
            paths = sorted(data_dir.glob(f"{name}/**/*.csv"))
            if (data_dir / f"{name}.csv").is_file():
                paths.append(data_dir / f"{name}.csv")
            if not paths:
                report["tables"][name] = {"status": "missing"}
                continue
            print(f"Auditing {name}: {len(paths)} file(s)", flush=True)
            for path in paths:
                with path.open("rb") as file:
                    digest = hashlib.file_digest(file, "sha256").hexdigest()
                manifest.append(
                    {
                        "path": str(path.relative_to(data_dir)),
                        "bytes": path.stat().st_size,
                        "sha256": digest,
                    }
                )
            load_table(con, name, paths)
            table_report = profile_table(con, name)
            table_report["files"] = len(paths)
            table_report["bytes"] = sum(path.stat().st_size for path in paths)
            report["tables"][name] = table_report
            if not table_report["missing_required_columns"]:
                available.add(name)
        report["relationships"] = relation_quality(con, available)
    serialized = json.dumps(manifest, sort_keys=True, indent=2)
    report["manifest_sha256"] = hashlib.sha256(serialized.encode()).hexdigest()
    report["total_rows"] = sum(t.get("rows", 0) for t in report["tables"].values())
    report["missing_tables"] = [
        k for k, v in report["tables"].items() if v.get("status") == "missing"
    ]
    output.with_name(output.stem + "-manifest.json").write_text(serialized + "\n")
    output.write_text(json.dumps(report, indent=2, default=str) + "\n")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=Path("data/raw"))
    parser.add_argument("--output", type=Path, default=Path("artifacts/data-profile.json"))
    parser.add_argument("--tables", nargs="+", choices=TABLES, default=list(TABLES))
    args = parser.parse_args()
    if not args.data_dir.is_dir():
        parser.error("Data directory does not exist. Run make data-sync first.")
    report = audit(args.data_dir, args.output, args.tables)
    print(f"Profiled {report['total_rows']:,} rows. Report: {args.output}")
    if report["missing_tables"]:
        parser.exit(1, f"Incomplete download: missing tables {report['missing_tables']}\n")


if __name__ == "__main__":
    main()
