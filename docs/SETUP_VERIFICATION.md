# Setup verification — September 27, 2026

These checks verify the project foundation. They do not establish that the banking assistant or hackathon submission is complete.

| Check | Result |
| --- | --- |
| Python environment | Python 3.12; uv sync completed; dependency versions recorded in uv.lock |
| Code checks | Ruff lint and formatting passed |
| Automated tests | 5 passed: scaffold readiness, malformed/minimum contracts, duplicate/null keys, duplicate-parent join counting, transaction ownership/currency consistency |
| Test warning | The installed Starlette version warns that its httpx-based TestClient is deprecated; tests still pass. Revisit the documented test client before expanding tests. |
| Local API | `/healthz` returned HTTP 200; `/readyz` returned HTTP 503 as intended; OpenAPI document retrieved successfully |
| Dataset access | Organizer's participant credentials authenticated successfully against the documented S3 bucket |
| Download | 7,671 of 7,671 listed files present; all byte sizes match the captured S3 inventory |
| Data audit | All 13 tables profiled; 23,495,188 rows; file SHA-256 manifest and aggregate report generated |
| Container build | Docker image built successfully from the lockfile |
| Container execution | Service returned HTTP 200; process UID 10001; no `/app/data`, `/app/.local`, or `/app/artifacts` present |
| Git boundary | Staged contents checked against the actual participant credentials; no credentials, source PDFs, raw data, or local audit database included |
| Cloud deployment | Not performed; the current service is a scaffold |
| Learned-component evaluation | Not implemented or run |

Local detailed receipts are under ignored `artifacts/`; the reviewed aggregate data receipt is under `docs/evidence/`. GitHub CI results are available in the repository's Actions tab. The initial setup does not require paid inference or provision cloud infrastructure.
