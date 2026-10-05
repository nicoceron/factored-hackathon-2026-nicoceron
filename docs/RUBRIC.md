# Requirement-to-evidence map

**Post-Opus local verification complete.** Stronger ordinal guards, visible attached-record confirmation, independent role sessions, augmented reports and fresh captures pass 413 local tests and 27 scoped Chrome checks. Refreshed v3 regressions and media bind the final local source. Hosted release verification is separate.

This map follows the participant problem statement and kickoff, without inventing scoring weights. It distinguishes implementation, offline evidence, and hosted behavior. No metric is a production claim.

The exact judging instruction is that the solution should work first (kickoff p. 20); depth, demonstrated behavior and engineering judgment determine the score, and more workflows earn no automatic bonus (problem statement p. 3). [The chat audit](CHAT_RUBRIC_AUDIT.md) records the complete requirement/comment inventory and the focused priorities. The current chat redesign passes 413 local tests and 27 scoped Chrome checks and is not deployed. Current v3 regression receipts are source-matched; public v1.1 browser/media and historical receipts verify their recorded revisions. The stricter v3 case-grounding scorer prevents direct old/new percentage comparisons.

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
| Ambiguity and unsupported requests | Persisted pending intent; current conversational references over validated authorized candidates; clarification and safe refusal. Historical regression/challenge outcome reports preserve mistakes |
| Human intervention | Specific redacted customer allegation retained through clarification, kept separate from verified facts; policy/risk evidence, open questions, read-back receipt and scoped analyst review. The evaluator rejects a generic filled report when the reference request is lost |
| Spanish and Portuguese | Current automatic ES/PT routing with short-reply language continuity; paired corpus groups, per-language historical evaluation, UI dictionaries and localized replies. Automatic routing has its own scoped API/Chrome checks in [UI.md](UI.md) |
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
