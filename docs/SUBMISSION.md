# Claro submission

**Factored AI & Data Hackathon 2026 · team/repository identifier `nicoceron`.** Materials are prepared locally and published through GitHub. No organizer email has been sent by this work. The supplied deadline is October 5, 2026; an exact cutoff hour/timezone was not supplied.

## Required materials

- [x] [Public repository](https://github.com/nicoceron/factored-hackathon-2026-nicoceron), correctly named `factored-hackathon-2026-nicoceron`.
- [x] [Working deployed application](https://claro-banking-hackathon-2026.onrender.com), on Render's **Free ($0/month)** plan.
- [x] Six-slide [presentation PDF](../submission/Claro-Hackathon-2026.pdf) and [editable PPTX](../submission/Claro-Hackathon-2026.pptx).
- [x] [Demo video](../submission/claro-demo.mp4), **164.55 seconds (2:44.55)**, 1080p with narration and captions. The maximum is three minutes.
- [x] [Media provenance and reproduction](../submission/README.md), plus exact file hashes and validation manifests.
- [ ] Organizer delivery: materials have **not been emailed**. The route supplied by the event is `hackathon.admin@factored.ai`; the local draft is preparation, not a submission receipt. Registered member details and the exact cutoff remain for the submitting participant to verify.

## Reviewer access — no credentials needed

Open the deployed link and allow about a minute if the free service is waking. Choose **Cliente · Español** or **Cliente · Português**, then enter. Use the transaction-status prompt without selecting a record to see clarification; select an operation and continue. Report an unrecognized charge, review the evidence, and confirm the proposed case. Only the explicit confirmation creates a case; a separate read-back verifies it.

Choose **Cambiar perfil / Trocar perfil**, then the analyst persona in the same browser. The queue contains that browser's cases. Open one, review facts and open questions, and either close the sandbox review or request more information. Operations shows measured workspace activity; Evaluation exposes the published model and workflow evidence. A new browser gets a separate workspace. Reset deletes only the current sandbox's data.

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

[Rubric mapping](RUBRIC.md) links every evaluation dimension to evidence. [Completion audit](COMPLETION_AUDIT.md) distinguishes prototype completion from production work. [System evaluation](SYSTEM_EVALUATION.md) discloses remaining model errors; authored synthetic tests do not establish production performance. Fraud candidates failed their promotion gates and were not released as useful detection. Runtime performs no paid or remote model calls.

## Release evidence

[Deployed API receipt](evidence/deployed-api-checks.json) records actual HTTPS workflows, isolation, cookie/security attributes, and file/report checksums without retaining session values. [Deployment receipt](../submission/deployment.json) identifies the public service and application commit. [UI verification](UI.md) and the hosted-browser release receipt cover customer/analyst behavior. The media manifests verify six slides, all reviewed renders, video duration/streams/captions and source provenance.

The original build plan and September 27 setup receipt are historical. Their incomplete scaffold status does not describe this release. Follow [SETUP.md](SETUP.md) to reproduce the current application and [DEPLOYMENT.md](DEPLOYMENT.md) for free-host operation and rollback.
