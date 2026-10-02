# Reproducible serving data

The pipeline has executed over the downloaded organizer snapshot: **150,000 customers, 400,000 products, and 4,425,008 transactions**. All transaction rows passed the implemented serving contracts. **1,106,307** timestamp discrepancies remain visible flags. This is a historical synthetic dataset, not live banking data. The public product uses independently generated fixtures; organizer records stay local.

The measured aggregate receipt is [serving-contracts.json](evidence/serving-contracts.json). The existing [raw-data audit](DATA_FINDINGS.md) accounts for all 13 source tables. This serving pipeline deliberately admits only the customer/product ownership relationships and transaction evidence needed by the chosen support workflow. It does not claim that the other ten tables have full serving contracts.

## Reproduce

```bash
make profile
uv run --locked python -m factored_banking.data_pipeline --export-sqlite
uv run --locked --group ml python -m factored_banking.train_fraud
uv run --locked --group ml pytest tests/test_data_pipeline.py tests/test_fraud.py tests/test_train_fraud.py
```

Run the profile after downloading all organizer files with the documented participant profile. No cloud compute or paid API is used. The pipeline opens the audit database read-only and builds temporary DuckDB relations. It writes under ignored `artifacts/curated/`:

| Artifact | Purpose |
| --- | --- |
| `serving.sqlite` | Local historical records with a customer index and unique transaction key; optional `--export-sqlite` |
| `fraud-features.parquet` | Offline feature table, temporal partitions and evaluation labels; never serve to the UI |
| `quarantine.parquet` | Private invalid transaction rows and their primary reason |
| `pipeline-report.json` | Aggregate counts, source database/file-manifest/feature/source-code hashes |

## Contracts and failure behavior

Schema columns are required before any output is admitted. Missing schema aborts the run. Customer and product keys must be present and unique. Products need an unambiguous accepted customer and a three-letter currency. Transactions require a present unique key, finite nonnegative numeric amount, parsed event and process dates, and an accepted product matching **product ID, customer ID and currency**. Every member of a duplicate-key group is quarantined, including apparently identical copies; choosing an arbitrary winner would hide conflicts. Invalid parents quarantine their descendants. Reason assignment follows a stable declared order, and aggregate counts are by the primary reason, not the sum of overlapping defects.

The original decimal amount string is retained in SQLite to avoid changing monetary evidence through a binary floating-point conversion. History sums use fixed-point `DECIMAL(38,8)` before division, avoiding parallel floating-point summation drift; this feature precision is ample for the observed source monetary values. Floating-point transforms are used only in the offline modeling experiment. Nullable merchant/category data remain nullable evidence. Missing descriptions are never invented. No exchange conversion is needed or assumed.

All serving rows exclude `is_fraud`, the organizer's `fraud_score`, customer contact/identity fields, gender, and product numbers. The offline feature table holds labels separately from its explicit feature allowlist. The SQLite customer index helps bounded retrieval; it **does not implement authentication or authorization**. An integrating service must scope every lookup using a trusted authenticated subject, never an arbitrary supplied customer ID.

## Time, replay and freshness

Source dates have no established timezone or label-adjudication time. We retain both event and process time without silently shifting them. An event calendar date after the process date is accepted with a visible flag; it is not treated as proven corruption or corrected to an invented timezone.

The conservative replay availability clock is:

```text
available_at = max(transaction_date, process_date + 1 day)
```

A process date has only daily resolution, so the replay assumes availability no earlier than the end of that day. This is an explicit experiment assumption, not observed ingestion metadata. Customer/currency history spans the preceding 30 days and ends **one microsecond before** the current availability timestamp. A DuckDB `RANGE` window excludes the current row, every simultaneous peer, future events and other currencies. Future product balances and customer snapshots are not predictors. Labels are assumed available at offline fitting; the missing adjudication times prevent proof of label maturity.

The partition clock differs from the earlier event-time feasibility query. Train is before January 2026; January calibrates probabilities; February selects the candidate; March onward is the held-out test. Every record carries event/process/availability time, organizer synthetic provenance and a historical source reference. A historical June 2026 snapshot must never be described as a current October balance.

## Lineage and public boundary

### Snapshot refresh and update correctness

The source is a dated batch snapshot with no validated change feed. Refresh means re-download the authorized source snapshot, rerun the full audit, and rebuild all serving rows and strict-prior features. Changed rows replace their prior values, rows absent from the new source disappear, and newly arrived historical events enter using the new snapshot's preserved event/process dates. A late row never gains an invented earlier availability time. Every update requires a fresh source manifest and pipeline receipt. This policy does not claim streaming freshness or change-data-capture support.

Two explicitly team-generated update tests exercise the missing source update feed: one changes an amount, deletes a prior transaction and inserts a late historical event in a replacement snapshot; the other interrupts the source after one staging batch and proves that the prior committed SQLite file remains byte-identical. Export commits and closes staging, checks the row count through a new SQLite connection, then atomically replaces the complete serving database. Until replacement succeeds, readers keep the prior snapshot. Run one publisher per output path. The public service continues to use labeled fixtures and never describes this private historical snapshot as live bank data.

The raw audit hashes all 7,671 CSV files. The pipeline receipt links that source-manifest digest, the actual input database digest, the source-code digest and the sorted feature-Parquet digest. Feature output is ordered by transaction ID. Every run has an isolated DuckDB spill directory. Two independent full-data runs produced the same feature-file SHA-256; the [reproduction receipt](evidence/pipeline-reproducibility.json) records the comparison. The SQLite export builds a temporary file, creates indexes, commits, and atomically replaces the prior export only after success. Failed exports therefore preserve the previous completed database.

Raw CSVs, SQLite/DuckDB databases, Parquet, quarantine records and local model-candidate artifacts remain excluded from Git and deployment. Only reviewed aggregate receipts and the selected small model manifest are public. Reproduction requires authorized organizer-data access; a public clone can run the team-generated contract/security tests without it.

Tests cover ambiguous parents, duplicate transactions, invalid time/amount/ownership, strict-prior windows, simultaneous peers, currency separation, source timestamp preservation, missing schema, exact monetary strings, and exclusion of targets from serving evidence.

Implementation references: [DuckDB window functions](https://duckdb.org/docs/stable/sql/functions/window_functions.html), [DuckDB Parquet export](https://duckdb.org/docs/stable/guides/file_formats/parquet_export.html), and [Python SQLite transactions](https://docs.python.org/3.12/library/sqlite3.html#transaction-control).
