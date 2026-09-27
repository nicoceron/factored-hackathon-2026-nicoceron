# Factored AI & Data Hackathon 2026

Repository for the provisional team **nicoceron**. Deadline: **October 5, 2026**; exact cutoff time/timezone is not confirmed in the supplied materials.

Build one banking customer-service workflow that understands a request, uses authorized records and tools, verifies the result, and escalates when appropriate. Demonstrate it in Spanish and Portuguese and compare it with a baseline on the same held-out cases.

## Start here

1. [What the organizers want](docs/BRIEF.md): requirements, deliverables, and interpretation of the Slack excerpts.
2. [Setup](docs/SETUP.md): environment, private dataset access, commands, and local service.
3. [Build and evaluation plan](docs/PLAN.md): recommended scope, architecture, acceptance criteria, and schedule.
4. [Data findings](docs/DATA_FINDINGS.md): measured coverage and limitations after downloading the organizer data.
5. [Submission checklist](docs/SUBMISSION.md): public repo, deployed demo, slides, and video.

## Current state

This is the development and data-analysis foundation. It includes a locked Python environment, dataset download commands, a reproducible raw-data audit, a minimal FastAPI service, a Dockerfile, and CI. The banking assistant, authenticated tool layer, learned component, held-out benchmark, and deployed demo still need to be built. `/readyz` intentionally returns 503 until that work exists.

## Run locally

Prerequisites: Python 3.12, [uv](https://docs.astral.sh/uv/getting-started/installation/), and AWS CLI v2 for the dataset.

```bash
make setup
make check
make dev
```

API documentation: <http://127.0.0.1:8000/docs>. Health: <http://127.0.0.1:8000/healthz>.

```bash
make data-list     # Uses a separate participant AWS profile
make data-plan     # Preview the download
make data-sync     # Resume/download the organizer CSV files
make profile       # Raw-data quality report + hashes + local DuckDB database
```

Read [SETUP.md](docs/SETUP.md) before using data commands on a fresh clone. No paid model service is required for these setup steps.

## Working recommendation

Start with **account/payment inquiries**: answer authorized balance and transaction-status questions, clarify an unspecified account/payment, and transfer disputed or unsupported cases with verified context. Confirm this scope against the audited data and valid evaluation labels before building. The supplied workflow examples are not separate competition tracks.

Use a pretrained component for language/intent understanding, deterministic code for permissions and workflow transitions, and verified records for amounts/statuses. Never treat generated prose as proof that an action succeeded.

## Repository boundaries

The repo is private during setup; the kickoff asks for a public repo at submission. Organizer PDFs, raw/derived customer records, local audit databases, and credentials are excluded from Git and the Docker build. The data dictionary itself contains access credentials and must not be committed. Public reports should contain reviewed aggregate evidence only. Review the organizer's data-use terms before redistributing any examples.

## Sources

The participant problem statement is the technical brief; the kickoff is the submission/logistics source. The dictionary and summary describe the dataset. Specific PDF pages and official implementation references are listed in [BRIEF.md](docs/BRIEF.md) and [SETUP.md](docs/SETUP.md). The [official event FAQ](https://www.factored.ai/careers/ai-data-hackathon) also gives October 5, 2026 as the closing date.
