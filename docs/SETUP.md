# Local setup

## Environment

Use Python 3.12 and uv. `uv.lock` pins dependencies. The initial setup uses uv 0.5.24; CI and the Dockerfile use that version too.

```bash
uv python install 3.12
make setup
make check
make dev
```

`make dev` binds to localhost. Use `make dev PORT=8010` if 8000 is in use. `/docs` is the generated API documentation, `/healthz` reports process health, and `/readyz` verifies the released language model. The root page is the complete Spanish/Portuguese sandbox. No participant credentials or organizer records are needed to run the demo or tests.

## Participant dataset access

AWS CLI v2 is required. Use only the read-only credentials issued in the participant data dictionary. They are already configured locally on the original setup machine; they are not included in a clone.

For a fresh clone, configure them interactively:

```bash
mkdir -p .local
chmod 700 .local
./scripts/aws.sh configure --profile factored-2026
chmod 600 .local/aws-credentials .local/aws-config
```

At the prompts, enter the organizer's access key and secret, region `us-east-2`, output `json`. Do not paste credentials into source code, chat logs, shell command arguments, or the README. This wrapper directs the official CLI to `.local/aws-credentials` and `.local/aws-config` and clears inherited credential environment variables. Existing global AWS profiles are not changed.

```bash
make data-list
make data-plan
make data-sync
make profile
```

The bucket is `factored-datathon-2026-s3-157725502942-us-east-2-an`, prefix `data/`. The initial inventory contained 7,671 CSV objects totaling 5,349,322,481 bytes (about 5.35 GB decimal / 4.98 GiB). Allow additional disk space for the audit database. Downloads stay in `data/raw/`. `sync` resumes and does not delete local files. Run it again to pick up organizer updates, then rerun the audit and compare manifests.

For an official inventory snapshot:

```bash
mkdir -p artifacts
./scripts/aws.sh s3api list-objects-v2 \
  --bucket factored-datathon-2026-s3-157725502942-us-east-2-an \
  --prefix data/ --output json > artifacts/s3-inventory.json
```

AWS CLI automatically paginates this command. Do not pass `--no-paginate` when taking a complete inventory.

## Audit outputs

`make profile` writes:

- `artifacts/data-profile.json`: aggregate row counts, required-column/key checks, nulls, categories, timestamp parsing, and selected exact-match joins.
- `artifacts/data-profile-manifest.json`: relative paths, byte sizes, and SHA-256 hashes of all scanned files.
- `artifacts/data-profile.duckdb`: raw tables for repeatable local SQL exploration.

This audit reads the files as strings to preserve invalid source values and casts explicitly in checks. CSV parse errors fail the command; rows are not silently discarded. It preserves duplicates and flags quality issues. A completed audit can contain failed contracts: this is diagnostic output, not a production data gate. The CLI exits nonzero when requested tables are absent. It does not itself prove that every expected partition downloaded; compare against the S3 inventory.

Audit only selected tables while iterating:

```bash
uv run --locked python -m factored_banking.profile \
  --tables customers products transactions call_center_interactions call_transcripts complaints \
  --output artifacts/focused-profile.json
```

The audit database stores organizer data and must remain local. Review aggregate results before copying them to `docs/`. The audit is diagnostic; the separate `make pipeline` step applies typed serving contracts, duplicate/conflict quarantine, lineage and atomic snapshot replacement. See [DATA_PIPELINE.md](DATA_PIPELINE.md) for availability clocks, strict-prior features and update fixtures. `make train-fraud` reproduces temporal experiments; `make evaluate` compares the complete HTTP workflows without external model calls.

## Container and deployment path

```bash
docker build -t factored-banking:dev .
docker run --rm -p 127.0.0.1:8000:8000 factored-banking:dev
```

The Docker context is an allowlist: code and dependency definitions only. No organizer records or credentials enter the image. The container runs as a non-root user. The image includes only public fixtures, frozen model artifacts and application assets. It runs one worker and writes sandbox state to `/state`; mount a local volume there for persistence. Use `CLARO_SECURE=1` and an exact `CLARO_ORIGIN` on HTTPS hosts. [DEPLOYMENT.md](DEPLOYMENT.md) records the free hosted configuration and release verification. Free-host state is ephemeral and can disappear after idle/restart.

## Reviewer smoke check

```bash
python3 scripts/smoke.py http://127.0.0.1:8000
```

This uses actual HTTP sessions for ES/PT, creates and reads verified cases, repeats an idempotent confirmation, records an analyst review, then erases its own isolated test workspace.

## Official references read before implementation

- [uv locking and syncing](https://docs.astral.sh/uv/concepts/projects/sync/)
- [uv with Docker](https://docs.astral.sh/uv/guides/integration/docker/)
- [AWS CLI sync](https://docs.aws.amazon.com/cli/latest/reference/s3/sync.html)
- [AWS CLI list-objects-v2](https://docs.aws.amazon.com/cli/latest/reference/s3api/list-objects-v2.html)
- [DuckDB Python API](https://duckdb.org/docs/current/clients/python/overview)
- [DuckDB CSV import](https://duckdb.org/docs/current/data/csv/overview)
- [DuckDB CSV error handling](https://duckdb.org/docs/current/data/csv/reading_faulty_csv_files)
- [FastAPI first steps](https://fastapi.tiangolo.com/tutorial/first-steps/)
- [FastAPI testing](https://fastapi.tiangolo.com/tutorial/testing/)
