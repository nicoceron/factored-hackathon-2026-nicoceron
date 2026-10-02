# Claro submission

**Factored AI & Data Hackathon 2026 · team/repository identifier `nicoceron`.** Materials are prepared locally and published through GitHub. Organizer submission is intentionally outside the requested work. No organizer email has been sent. The supplied deadline is October 5, 2026; an exact cutoff hour/timezone was not supplied.

## Required materials

- [x] [Public repository](https://github.com/nicoceron/factored-hackathon-2026-nicoceron), correctly named `factored-hackathon-2026-nicoceron`.
- [x] [Working deployed application](https://claro-banking-hackathon-2026.onrender.com), on Render's **Free ($0/month)** plan.
- [x] Six-slide [presentation PDF](../submission/Claro-Hackathon-2026.pdf) and [editable PPTX](../submission/Claro-Hackathon-2026.pptx).
- [x] [Demo video](../submission/claro-demo.mp4), **150.57 seconds (2:30.57)**, 1080p with narration and captions. The maximum is three minutes.
- [x] [Media provenance and reproduction](../submission/README.md), plus exact file hashes and validation manifests.
- Organizer delivery is **intentionally not requested** and is not a missing application feature. Materials have **not been emailed**. The event route is `hackathon.admin@factored.ai`; the local draft is preparation, not a submission receipt. Registered member details and the exact cutoff remain for a participant who later chooses to submit.

## Reviewer access — no credentials needed

Open the deployed link and allow about a minute if the free service is waking. Choose **Cliente · Español** or **Cliente · Português**, then enter. Use the transaction-status prompt without selecting a record to see clarification; select an operation and continue. Report an unrecognized charge, review the evidence, and confirm the proposed case. Only the explicit confirmation creates a case; a separate read-back verifies it.

Choose **Cambiar perfil / Trocar perfil**, then the analyst persona in the same browser. The queue contains that browser's cases. Open one, review facts and the specific customer request, then ask a question. Switch back to the customer to answer that saved question. Return to the analyst, verify the chronological history, and close the sandbox review. Closed cases retain read-only history. Operations shows measured workspace activity; Evaluation exposes the published model and workflow evidence. A new browser gets a separate workspace. Reset deletes only the current sandbox's data.

The personas, records and bank policies are explicitly team-authored fixtures. This is a working customer-service prototype, not real banking authentication or a bank integration. Do not enter personal data or credentials. No money movement, refund, card blocking or lending decision is available. Free-host restarts can clear cases and sessions; local Docker volumes can preserve developer state. Cold starts and ephemeral storage are disclosed in the UI, deck and [deployment guide](DEPLOYMENT.md).

## Product and evidence checks

- [x] Focused historical-transaction support and dispute intake justified by organizer-data findings.
- [x] Spanish/Portuguese normal, ambiguous and human-required paths, browser and actual HTTP checks.
- [x] Opaque expiring test sessions; workspace/customer/role isolation; CSRF/origin and confirmation controls.
- [x] Transactional idempotency, concurrent-write protection, fresh read-back and verified receipts; failed verification never claims success.
- [x] Server-backed cancellation, pending-context handling, scoped analyst review and minimized structured handoffs.
- [x] Reproducible contracts, lineage, quarantine, full-snapshot refresh, changed/deleted/late fixtures and failed-export preservation.
- [x] Frozen learned component versus keyword and local Gemma baselines; same held-out component workload.
- [x] Whole-system regression and preserved untouched first-pass evidence; counts, failures, language slices, cost and latency are explicit.
- [x] Missing/malformed transaction evidence, expiry, unauthorized access, injection, model outage, tool verification failures and retries tested.
- [x] Clean-clone setup, CI, non-root Docker, public HTTPS/API workflows, secure cookies and published-asset equality verified.
- [x] Secret scans and source-only image boundary; no organizer PDFs, credentials or private customer records in the public repository/image.

[Rubric mapping](RUBRIC.md) links every evaluation dimension to evidence. [Completion audit](COMPLETION_AUDIT.md) distinguishes prototype completion from production work. [System evaluation](SYSTEM_EVALUATION.md) discloses remaining model errors; authored synthetic tests do not establish production performance. Fraud candidates failed their promotion gates and were not released as useful detection. The v1.0 release measured a local runtime with no remote model calls. The subsequent provider integration is separately gated and must report its own usage, tariff estimates and verification; v1.0’s $0 model-API result must not be generalized to a provider-enabled run.

## Release evidence

[Deployed v1.1 API receipt](evidence/deployed-v1.1-api-checks.json) records actual HTTPS workflows, isolation, cookie/security attributes, and file/report checksums without retaining session values. [Deployment receipt](../submission/deployment.json) identifies the public service and application commit. [UI verification](UI.md) and the hosted-browser release receipt cover customer/analyst behavior. The media manifests verify six slides, all reviewed renders, video duration/streams/captions and source provenance.

The original build plan and September 27 setup receipt are historical. Their incomplete scaffold status does not describe this release. Follow [SETUP.md](SETUP.md) to reproduce the current application and [DEPLOYMENT.md](DEPLOYMENT.md) for free-host operation and rollback.


## Additional completion work after the v1.0 release

Specific redacted customer allegations now survive transaction clarification, and analyst questions/customer replies persist in scoped case history. The [source-matched v2 replay](evidence/system-evaluation-v2.json) verifies 60/60 required handoffs preserving the request and 122/140 learned outcomes. The [earlier challenge regression](evidence/system-challenge-regression-v2.json) verifies 30/30 such handoffs and 63/70 outcomes. A [frozen controlled replay](evidence/service-segment-evaluation.json) compares customers by selected-transaction status/currency, counterbalanced in both languages, with the same outcomes in all six strata. The repeated 840 cases per system contain 140 unique authored utterances, not additional independent labels or demographic fairness proof.

A separate prospective 70-case challenge is frozen and unscored. Jev classification and DeepSeek composition have runtime/spending controls and mocked tests; no successful live inference is claimed. Current offline receipts record zero external attempts including setup/warmup, which must not be generalized to provider-enabled cost. Release v1.1 is deployed at application commit `59ec1d17307bf917e6b598e0ab25e4e8697cfa36`. Its HTTPS API receipt passes 23 checks, matches all eight static assets and all six reports, and exercises complete ES/PT case follow-up. The refreshed six-slide deck and 150.57-second video have separate manifests. The fresh-clone receipt passes all 238 tests; PR #4, the follow-up status-label correction in PR #5, and both merged application CI runs passed. The [hosted browser receipt](evidence/deployed-v1.1-browser-checks.json) identifies the revision used for each check. Organizer delivery is intentionally not requested.
