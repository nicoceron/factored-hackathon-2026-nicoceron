# Claro submission

**Factored AI & Data Hackathon 2026 · team/repository identifier `nicoceron`.** The prior v1.1 release is published through GitHub; current chat materials are prepared locally for review. Organizer submission is intentionally outside the requested work. No organizer email has been sent. The supplied deadline is October 5, 2026; an exact cutoff hour/timezone was not supplied.

## Current revision and published materials

The current source introduces immediate chat, automatic ES/PT and conversational transaction references. It is **not deployed yet**. Local verification passes 352 tests, 20 scoped Chrome checks and the source-only Docker bilingual HTTP lifecycle with identical static assets/reports. The current v3 authored regressions measure 130/140 and 64/70 learned correct outcomes; all remaining failures are published. Its stronger case-grounding scorer prevents direct comparison with v1.1 percentages.

The local six-slide deck/PDF and 157.17-second captioned video now demonstrate the chat redesign and source-matched regressions. The public hosted app and [v1.1 release](https://github.com/nicoceron/factored-hackathon-2026-nicoceron/releases/tag/v1.1.0) remain the prior verified revision. Local screenshots do not establish deployment.

## Current local review materials

- [x] Six-slide [presentation PDF](../submission/Claro-Hackathon-2026.pdf) and [editable PPTX](../submission/Claro-Hackathon-2026.pptx), with three native editable charts and embedded workbooks. All six final PDF pages were reviewed.
- [x] [Demo video](../submission/claro-demo.mp4), **157.17 seconds (2:37.17)**, 1080p/24 fps with H.264, AAC mono narration, English embedded captions and 29 external SRT cues. All nine composed scenes were reviewed and the encoded file decodes without errors.
- [x] [Media provenance and reproduction](../submission/README.md), exact input/output hashes and validation manifests. Captures contain team-authored fixtures and disabled providers.
- [x] Existing [public repository](https://github.com/nicoceron/factored-hackathon-2026-nicoceron), correctly named `factored-hackathon-2026-nicoceron`, with the historical v1.1 release. Current local source/media are not a new publication receipt.
- [x] Prior [hosted v1.1 application](https://claro-banking-hackathon-2026.onrender.com), previously verified on Render Free. Its exact source and checks are in the deployment receipt; the current chat revision has not been deployed.
- Organizer delivery is **intentionally not requested** and is not a missing application feature. Materials have **not been emailed or uploaded to organizers**. The existing local email draft is preparation, not a submission receipt. Registered member details and the exact cutoff remain for a participant who later chooses to submit.

## Current local reviewer access — no credentials needed

Run `make dev` and open `http://127.0.0.1:8000`. Start the conversation immediately in Spanish or Portuguese. Ask about a transaction using the merchant or other exact details; an ambiguous reference produces a question in chat. Report an unrecognized charge, review the evidence and explicitly confirm the proposed case. Only confirmation creates a case; a separate read-back verifies it.

Open **Revisión humana / Análise humana** (`/?review=1`) in the same browser. Its queue contains that browser's cases. Open one, review the specific request and facts, then send a question using the direct action. Return to `/`, open the case and choose **Responder por chat / Responder na conversa** for the saved question; send the reply through the same composer. Return to the reviewer workspace, verify the chronological history and close the sandbox review. Closed cases retain read-only history. Operations and Evaluation stay in the reviewer workspace; `/?review=1&view=evaluation` opens the published evidence. A new browser gets a separate workspace. Reset deletes only the current sandbox's data. These current local instructions are covered by the scoped Chrome and HTTP receipts in [UI.md](UI.md).

The hosted v1.1 interface retains its historical persona entry and transaction-selection controls. Its source-specific browser checks are recorded in [UI.md](UI.md) and `evidence/deployed-v1.1-browser-checks.json`; they do not verify the current chat redesign.

The personas, records and bank policies are explicitly team-authored fixtures. This is a working customer-service prototype, not real banking authentication or a bank integration. Do not enter personal data or credentials. No money movement, refund, card blocking or lending decision is available. Free-host restarts can clear cases and sessions; local Docker volumes can preserve developer state. Cold starts and ephemeral storage are disclosed in the UI, deck and [deployment guide](DEPLOYMENT.md).

## Historical v1.1 product and evidence checks

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

## Historical v1.1 release evidence

[Deployed v1.1 API receipt](evidence/deployed-v1.1-api-checks.json) records actual HTTPS workflows, isolation, cookie/security attributes, and file/report checksums without retaining session values. [Deployment receipt](../submission/deployment.json) identifies the public service and application commit. [UI verification](UI.md) and the hosted-browser release receipt cover customer/analyst behavior. Historical v1.1 media remain in the published release. The local manifests now verify the current six-slide deck and 157.17-second video; their source hashes and local screenshot provenance are separate from deployed v1.1 evidence.

The original build plan and September 27 setup receipt are historical. Their incomplete scaffold status does not describe this release. Follow [SETUP.md](SETUP.md) to reproduce the current application and [DEPLOYMENT.md](DEPLOYMENT.md) for free-host operation and rollback.


## Verified v1.1 completion work after the v1.0 release

Specific redacted customer allegations now survive transaction clarification, and analyst questions/customer replies persist in scoped case history. The [source-matched v2 replay](evidence/system-evaluation-v2.json) verifies 60/60 required handoffs preserving the request and 122/140 learned outcomes. The [earlier challenge regression](evidence/system-challenge-regression-v2.json) verifies 30/30 such handoffs and 63/70 outcomes. A [frozen controlled replay](evidence/service-segment-evaluation.json) compares customers by selected-transaction status/currency, counterbalanced in both languages, with the same outcomes in all six strata. The repeated 840 cases per system contain 140 unique authored utterances, not additional independent labels or demographic fairness proof.

A separate prospective 70-case challenge is frozen and unscored. Jev classification and DeepSeek composition have runtime/spending controls and mocked tests; no successful live inference is claimed. Current offline receipts record zero external attempts including setup/warmup, which must not be generalized to provider-enabled cost. Release v1.1 is deployed at application commit `59ec1d17307bf917e6b598e0ab25e4e8697cfa36`. Its HTTPS API receipt passes 23 checks, matches all eight static assets and all six reports, and exercises complete ES/PT case follow-up. The refreshed six-slide deck and 150.57-second video have separate manifests. The fresh-clone receipt passes all 238 tests; PR #4, the follow-up status-label correction in PR #5, and both merged application CI runs passed. The [hosted browser receipt](evidence/deployed-v1.1-browser-checks.json) identifies the revision used for each check. Organizer delivery is intentionally not requested.
