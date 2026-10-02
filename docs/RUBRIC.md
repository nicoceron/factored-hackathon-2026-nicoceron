# Requirement-to-evidence map

This map follows the participant problem statement and kickoff, without inventing scoring weights. It distinguishes implementation, offline evidence, and hosted behavior. No metric is a production claim.

| Evaluation dimension | Implemented decision and evidence | Limits |
| --- | --- | --- |
| Technical judgment | Deterministic permission/action policy; exact evidence; explicit confirmations; transactional idempotency reservation; fresh read-back; scoped sessions; [OPERATIONS.md](OPERATIONS.md) and API/security tests | Trusted test identity, synthetic policy, single replica; real bank identity and durable infrastructure remain production work |
| AI engineering | FastAPI customer/analyst API; ES/PT UI; local learned NLU; optional schema-validated Jev/DeepSeek adapters; specific reports, proposals, receipts, persisted question/reply history; Docker and CI | No real bank tools; sandbox fixture service. External inference remains unverified pending authorized metered use |
| Data engineering | All-table raw audit; contracts, quarantine, lineage, atomic private serving snapshot; strict-prior features and update fixtures; [DATA_PIPELINE.md](DATA_PIPELINE.md) | Conservative availability assumption because timezone/label adjudication clocks are absent |
| Machine learning | Rules, trained TF-IDF/logistic, local Gemma challenger; temporal weighted logistic/CatBoost fraud experiments; calibration/capacity; [LANGUAGE_EVALUATION.md](LANGUAGE_EVALUATION.md), [ML_REPORT.md](ML_REPORT.md) | Authored dialogue labels; synthetic organizer data; fraud candidates rejected rather than overstated |
| Data analytics | Data-backed workflow choice; measured corpus limitations; language/failure slices; workspace analytics; [DATA_FINDINGS.md](DATA_FINDINGS.md), [SYSTEM_EVALUATION.md](SYSTEM_EVALUATION.md) | Offline/service-demo counts, no causal business savings or measured production CSAT |

## Required behavior

| Requirement | Authoritative implementation/evidence |
| --- | --- |
| Normal resolution with sources | `workflow.py` status templates; exact amount/currency/status/source/as-of; ES/PT API and browser scenarios |
| Ambiguity and unsupported requests | Persisted pending intent; explicit transaction selection; safe refusal; regression/challenge outcome reports include mistakes |
| Human intervention | Specific redacted customer allegation retained through clarification, kept separate from verified facts; policy/risk evidence, open questions, read-back receipt and scoped analyst review. The evaluator rejects a generic filled report when the reference request is lost |
| Spanish and Portuguese | Paired corpus groups; per-language evaluation, UI dictionaries and localized replies |
| Authorized service-segment comparison | Frozen team-authored status × currency fixtures, identical utterances counterbalanced in ES/PT; paired outcomes and disparity investigation in [SYSTEM_EVALUATION.md](SYSTEM_EVALUATION.md). These are customers by selected-transaction status/currency, not inferred demographic groups |
| Permissions outside prompts | Session/customer/workspace filters and allowed action enums; no model SQL; role/CSRF/origin checks |
| Action confirmation and verification | Expiring proposal; separate confirmation endpoint; atomic key reservation; duplicate/concurrent/write-verification-failure tests |
| Data quality, lineage, refresh | Deterministic DuckDB contracts and manifests; private atomic snapshot; duplicate/conflict/late/update fixtures |
| Learned component versus baseline | Frozen component corpus and development-only selection; same workloads for rules and learned model; local Gemma comparator |
| Leakage prevention | Source hashes; semantic-pair split isolation; train-only fitting; temporal availability; labels and supplied fraud_score excluded from features |
| Failure handling | Expired session, cross-customer/browser/role access, injection, malformed input, model outage, missing data, write/read-back failure, retry conflict, concurrent writes |
| Safe resolution versus containment | Separate denominators and outcome definitions in full-system reports; missed and unnecessary handoffs explicit |
| Efficiency | Measured local component and HTTP workflow p50/p95; offline receipts record zero external attempts. Optional provider accounting separates tokens, attempts, tariff estimates, unknown cost and all-run overhead; electricity/host costs excluded explicitly |
| Reliability/operations | Source-only non-root Docker image, health/readiness, bounded SQLite locks, local fallback, optional provider timeout/budget controls, minimized traces, retention/deletion and rollback policy |

## Deliverable audit

Final URLs, release checks, presentation/video paths, runtime limitations and submission preparation status are maintained in [SUBMISSION.md](SUBMISSION.md). A local test or report is not proof of public deployment. Organizer delivery is intentionally outside the requested work; preparing a complete review package does not imply that an email was sent.
