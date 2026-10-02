# Workflow evaluation and its limits

This benchmark sends real HTTP requests through FastAPI `TestClient`, persisted sessions, the workflow, SQLite proposals/cases, explicit confirmation, and committed read-back verification. It compares the **same workflow with keyword rules versus the released learned classifier**. Both receive the same deterministic safeguards. The default offline replay explicitly disables external providers and uses no organizer customer record. Provider-enabled experiments have separate configuration, usage and evidence.

The 140-case workload replays the frozen language test corpus described in [LANGUAGE_EVALUATION.md](LANGUAGE_EVALUATION.md). Its model-level results remain a held-out classification experiment because model weights and thresholds were frozen before that evaluation. **The system results below are a developer regression replay:** the first workflow run exposed two legitimate scam reports blocked by privacy filters and two overlapping scam/dispute reports delayed by transaction clarification. Deterministic safety behavior was corrected and the workflow replayed. These final numbers must not be described as an untouched or independently reviewed end-to-end test.

## Request-preservation contract and provider accounting (v2)

The evaluator now requires the stored `customer_report` to retain the redacted reference request through transaction selection and confirmation. It also requires `report_provenance=customer_allegation_redacted_not_verified`, separating what the customer reported from verified transaction facts. A generic category sentence can contain every expected field and still fails this check. Tests distinguish a duplicate second charge from denial of the entire purchase, and verify that the initial specific request survives clarification. This is a deliberately strict retained-text contract, not a model judge or a claim that every possible paraphrase is equivalent. Known-sensitive examples may provide an independently specified `reference_report`; otherwise the expected text is the shared redactor's output, whose security tests are separate.

`system-request-preservation-v2` receipts add `handoffs_preserving_reference_request` and require preservation for a correct human-required outcome. Original frozen first-pass reports keep their historical v1 criterion and source hashes. Replaying an exposed corpus with v2 is regression evidence; it does not create a new blind test.

`run_workload` accepts a named classifier through its `classifier` argument and optional `configure_app`/`usage_meter` hooks for an explicitly authorized provider experiment. It creates the app with external inference disabled before any optional injection. Provider ledger snapshots surround the measured case requests, including clarification and confirmation/read-back. A separate all-run ledger includes warmup, seed-case setup and fault checks so those requests cannot vanish from the accounting. Run each experiment with an isolated ledger.

Provider input/output tokens and attempts come from recorded responses and attempts. Costs computed using public tariffs are estimates, not invoice spend. Unknown-charge attempts and budget reservations remain visible; an incomplete cost becomes undefined rather than $0. Estimated cost per attempted case and per successful automated resolution have separate fields, and the success-denominator metric is undefined with zero successes. The older `$0` figures below apply only to the identified local runs. A prepared provider adapter is not a measured provider outcome.

## Authorized service-segment protocol

The frozen [fixture specification](../src/factored_banking/resources/service_segment_fixtures.json) and [manifest](../src/factored_banking/resources/service_segment_manifest.json) define **customers by selected-transaction status/currency**: completed, pending and declined crossed with COP/USD. Every stratum replays the identical 140 exposed utterances, including 70 Spanish and 70 Portuguese cases, for **840 replays per system**. There remain only 140 unique utterances and 70 translated semantic pairs, not 840 independent labels. Forty reference cases per stratum directly require selected transaction evidence (status/dispute); all other intents are also scored to check that record attributes do not change policy routing.

The API fixture seam preserves each authenticated customer's record IDs and replaces only the first permitted transaction's status, amount/currency, source and common country. Both languages receive every status/currency combination, preventing the original ES/COP and PT/USD fixture pairing from confounding the comparison. Monetary values are authored examples, not exchange conversions. These operational service groups contain no inferred age, gender, disability, income or customer tier. They address the chosen workflow's supported record attributes, not demographic fairness.

The [source-matched aggregate report](evidence/service-segment-evaluation.json) compares correctness, safe automated resolution, missed/unnecessary handoffs and materially wrong outcomes for every stratum/language. Paired differences use the same case ID against the completed/COP reference. **Zero paired outcome changes were observed** for either system across the controlled attributes. Grounded status answers were checked against each changed permitted record, rather than a constant expected response.

| Selected transaction stratum | Rules correct | Learned correct | Learned handoffs preserving request | Learned safe automated / all in-scope |
| --- | ---: | ---: | ---: | ---: |
| Completed / COP | 77/140 | 122/140 | 60/60 | 36/120 |
| Completed / USD | 77/140 | 122/140 | 60/60 | 36/120 |
| Pending / COP | 77/140 | 122/140 | 60/60 | 36/120 |
| Pending / USD | 77/140 | 122/140 | 60/60 | 36/120 |
| Declined / COP | 77/140 | 122/140 | 60/60 | 36/120 |
| Declined / USD | 77/140 | 122/140 | 60/60 | 36/120 |

Within every stratum, learned correctness was 60/70 Spanish and 62/70 Portuguese; rules scored 40/70 and 37/70. Learned verified handoffs preserved the request in 30/30 cases in each language, while rules reached 15/30 ES and 13/30 PT. Thus the remaining disparity in these fixtures is tied to the authored language cases, not the status/currency intervention: the same failed IDs recur in every stratum. No protected or demographic attribute is collected or inferred. These small translated slices do not estimate population fairness or explain language differences causally. Shared linguistic errors and authoring bias persist even when the controlled attribute gaps are zero. All 1,680 replays, including setup, recorded zero external provider attempts.

```bash
uv run --locked python -m factored_banking.service_segments \
  --output artifacts/service-segment-evaluation.json
```

## Prospective provider challenge

A new **70-case** corpus, `system_prospective_test.json`, was frozen at SHA-256 `4622618e9d06cba5584081a438e84ab896eaf9a5ff0ef6b1cf497545258a7a67` before any scoring or inspection of the new provider prompts. It contains 35 ES/PT pairs, five per intent. The separate author knew previous workflow code and failures, so it is independent of provider prompt corrections, not externally blinded. There is no independent human or native-Portuguese label review. The [manifest](../src/factored_banking/resources/system_prospective_manifest.json) requires preserving the first-pass evidence; later fixes/reruns must be named regression. No result is claimed merely because the corpus exists.

## Reference behavior and replay protocol

Every case gets a fresh isolated browser workspace and a trusted demo session in its reference language. The corpus is synthetic and uniformly balanced, rather than sampled from production demand. Existing-case scenarios get a permitted support case created through the same API before measurement. The replay then submits the exact corpus utterance:

- Transaction status and dispute cases answer a transaction-clarification prompt with an explicit selection of the first authorized fixture transaction. Selection comes from the simulated user, not an inferred merchant match.
- Ambiguous cases remain ambiguous; the harness never invents a transaction selection for them.
- A case proposal is confirmed only when the reference scenario requires a human. Wrong proposals on other intents are recorded and remain unconfirmed.
- A transfer succeeds only when the action response has a verified receipt and a subsequent authenticated case read returns that same stored case.
- A normal answer must return the selected authorized record, its evidence/source, amount, currency, localized status, ID, and historical as-of date.
- Case lookup must read the previously created case and its stored status. This tests the list/read workflow, not semantic extraction of an arbitrary case ID mentioned in a sentence.

Entity recognition, matching fictional merchants in an utterance to real transaction candidates, multi-party adjudication, natural confirmation behavior, and analyst judgment of summary usefulness are outside this benchmark. The historical v1 packet score checked required fields, reference intent, scam priority and dispute transaction evidence, but did not test whether a generic report preserved the actual request. The stronger v2 contract below adds that missing check. Neither criterion is independent human approval of a summary.

### Hosted continuity regression

The first hosted browser review of release `39a8e2c` exposed a Portuguese multi-turn defect outside the frozen workloads: after asking for transaction status and being asked to select an operation, selecting `TX-PT-102` and replying “Essa transação” incorrectly started a dispute. The workflow now recognizes complete short ES/PT demonstrative replies only when a transaction-status or dispute task is pending. It preserves that task and requires the same authorized-record validation; no selected record still produces clarification. Cancellation and explicit scam/dispute/human-review or model-outage signals keep priority. A longer utterance beginning with a demonstrative remains a new request.

The 36 cases in `tests/test_workflow_continuity.py` are explicitly developer regression tests, including the actual learned-model HTTP sequence in both languages, pending dispute preservation, missing/foreign selections and new-request/safety priority. They are not added to the frozen 140- or 70-case denominators and do not alter classifier weights, thresholds, labels or first-pass evidence. The implementation uses Python's documented [whole-string regular-expression matching](https://docs.python.org/3.12/library/re.html#re.fullmatch) with a bounded selection grammar; it does not infer transaction identity from prose.

## Independent challenge: first untouched run

A separate data/ML assistant authored **70 new cases** after receiving only the seven intent definitions and schema, without reading prior corpus messages or classifier predictions. It had previously seen workflow code and discussed known defects, so this is not an externally blinded study. Labels and Portuguese translations remain unreviewed by humans. The [freeze manifest](evidence/system-challenge-manifest.json) records **35 ES/PT pairs**, five groups per intent, frozen SHA-256 `7c25f29b05769c76597c967cc9db24cc37c05401040eb76a66f756b0618faaa9`, and the authoring protocol. The evaluator checks that hash and rejects duplicate text against earlier splits before scoring.

The workflow and models were held fixed for the first run. Its [unaltered first-pass evidence](evidence/system-challenge-evaluation.json) is kept separately from the 140-case regression replay:

| Fresh challenge result | Rules + safeguards | Learned + safeguards |
| --- | ---: | ---: |
| Correct outcomes | 43/70 (61.4%) | 61/70 (87.1%) |
| Safe automated resolutions / all in-scope | 15/60 | 18/60 |
| Required human handoffs verified | 19/30 | **28/30** |
| Required human handoffs missed | 11/30 | **2/30** |
| Unnecessary handoff proposals | 0/70 | 4/70 |
| All incorrect outcomes | 27/70 | 9/70 |
| Materially wrong outcomes | 15/70 | 2/70 |
| Observed scoped unauthorized record/action outcomes | 0/70 | 0/70 |
| Local p50 / p95 | 4.46 / 9.82 ms | 6.27 / 11.94 ms |

Learned outcome counts were **31/35 ES and 30/35 PT**. Eight fault checks per language again passed for both systems. The two missed escalations shared a new defect: a customer's report of a coercive instruction contained the cancellation verb, and a broad command regex cancelled the conversation instead of recognizing the scam report. This shows why the earlier regression suite's 60/60 handoffs cannot be generalized to all language. Other failures included false dispute/scam proposals, existing-case misrouting, and unsupported requests sent to clarification.

Cancellation was then restricted to an explicit command rather than any sentence containing the verb. The historical [v1 regression](evidence/system-challenge-regression.json) remains preserved. The current [v2 regression rerun](evidence/system-challenge-regression-v2.json), with the stronger retained-request criterion, achieved **63/70 learned outcomes and 30/30 required handoffs preserving the request**, versus 43/70 and 19/30 for rules. **Seven learned outcomes remain incorrect, including four unnecessary handoff proposals.** Zero materially wrong outcomes under the narrower definition below must not be described as zero errors. All 22 current fault cases passed for each system. This v2 rerun's learned local p50/p95 was 7.91/14.15 ms; rules were 5.71/11.13 ms. This unisolated development host's timing varied substantially between runs, so these are observations rather than a latency guarantee. The model and thresholds were unchanged. The first-pass report retains the historical source hashes and results; current source reproduces the corrected regression, not the old defect.

## Measured v2 140-case regression results

Each recorded benchmark uses a sequential replay in one process on the development Mac. The final regression refreshes ran sequentially on the shared development host; other development activity was not isolated. Reported latency includes in-process HTTP chat, any clarification and confirmation, and read-back requests. It excludes session/fixture setup, hosted network delivery, user thinking time, and queue time. This is not a production capacity or hosted latency measurement.

| Metric | Rules + safeguards | Learned + safeguards |
| --- | ---: | ---: |
| Correct reference outcomes / all cases | 77/140 (55.0%) | **122/140 (87.1%)** |
| Correct automated resolutions / all in-scope cases | 31/120 (25.8%) | **36/120 (30.0%)** |
| Attempted automation / all cases | 47/140 | 37/140 |
| Required handoffs verified | 28/60 | **60/60** |
| Required handoffs missed | 32/60 | **0/60** |
| Handoffs with correct intent, priority, packet fields and preserved request | 28/28 | 60/60 |
| Unnecessary handoff proposals | 4/140 | 7/140 |
| No verified transfer (“containment”) | 80.0% | 57.1% |
| Incorrect outcomes of any kind | 63/140 | 18/140 |
| Materially wrong outcomes under the definition below | 34/140 | 1/140 |
| Observed scoped unauthorized record/action outcomes | 0/140 | 0/140 |
| Measured local p50 / p95 | 4.76 / 10.12 ms | 7.49 / 14.82 ms |

“Safe automated resolution” requires a correct transaction answer or verified case lookup without a human transfer, divided by **all 120 in-scope cases**, including those expected to need clarification or a human. Unsupported requests are the 20 out-of-scope cases. The maximum possible automated rate on this deliberately balanced workload is 40/120; correct clarification, refusal, and human transfer count as correct outcomes but are not automated resolutions.

“Attempted automation” means a returned resolved or case-lookup state. “Containment” only means no verified transfer; false proposals, clarification loops, and missed transfers can inflate it. Higher containment in the rules system therefore does not mean better service.

“Materially wrong” is the explicitly defined subset of incorrect outcomes where the system returned a resolved/case-lookup state despite a different required result, or failed the required human-outcome contract. Other routing errors, refusals that should have clarified, unnecessary proposals, and failure to refuse unsupported requests remain visible in **all incorrect outcomes**. This metric is separate from the scoped unsafe-outcome check, which checks returned transaction ownership and unverified action receipts. A zero in that limited check does not establish universal safety.

Language slices have 70 cases each. Learned outcomes were **60/70 Spanish and 62/70 Portuguese**, with 18 automated resolutions and 30 verified required handoffs in each. Rules achieved 40/70 and 37/70. These small authored slices do not establish demographic fairness or native-language quality. No independent human language review has occurred.

The 18 remaining learned-system failures include negated human requests and affirmative transaction-recognition causing false proposals, unsupported requests causing clarification instead of a clear refusal, unrelated requests causing unnecessary scam proposals, and one ambiguous request sent to case lookup. The public evidence preserves every failed case ID, expected/predicted intent, state sequence, and the verification result. The system does not yet resolve every language variation correctly.

## Failure injection

A separate, explicitly oversampled fault suite runs eleven checks in each language for each system: unauthenticated record access, foreign-customer reference, missing CSRF token, expired session, model timeout, failed committed read-back, retry with the same idempotency key, prompt injection, missing transaction amount, unknown currency, and invalid transaction status. **22/22 passed per system**. The current tool boundary validates an allowlisted Pydantic record before financial text, risk inference or case evidence. Malformed or conflicting selected records produce a human-review proposal without claimed transaction facts; 33 targeted tests additionally cover missing provenance/source/as-of, non-finite/negative/numeric amounts, invalid dates, unexpected fields, and duplicate references. For a failed read-back, the API returns 503 without a receipt; retry verifies one stored case rather than creating another. The model timeout check supplies a deterministic injected timeout, not an observed provider outage.

The broader API tests also exercise cross-browser workspace isolation, analyst permissions, concurrent confirmation, request-key conflicts, cancellation/expiry, deletion, and retention boundaries. Unit-test success and the fault suite are supporting engineering evidence; neither replaces hosted-browser QA or proves absence of other attack paths.

## Cost and reproducibility

Recorded external provider attempts were **zero** for both systems, for measured requests and the all-run ledger including setup/warmup/fault checks. These offline runs therefore incurred **$0 model API spend**. Model API cost per attempted case and per successful automated resolution is $0; the latter is undefined with zero successful automated resolutions. Each workload explicitly disables external inference and creates a temporary provider ledger so other processes cannot contaminate its accounting. Hardware, electricity, and hosting costs are unmeasured and excluded. Optional provider-enabled runs require separate authorized execution and evidence. No production savings, revenue, avoided fraud, or representative per-customer operating cost is claimed.

```bash
uv run --locked python -m factored_banking.system_evaluation \
  --output artifacts/system-evaluation-v2.json
# Challenge replay is regression once its first run has been inspected:
uv run --locked python -m factored_banking.system_evaluation \
  --challenge-corpus src/factored_banking/resources/system_challenge_test.json \
  --challenge-regression \
  --output artifacts/system-challenge-regression-v2.json
uv run --locked pytest -q tests/test_system_evaluation.py tests/test_api.py tests/test_workflow_evidence.py
```

The [v2 aggregate evidence](evidence/system-evaluation-v2.json) records corpus SHA-256 and exact API, workflow, language, privacy, provider, store, fixture, policy, fraud and evaluation-source hashes, including the released language/fraud JSON model artifacts. The old [v1 report](evidence/system-evaluation.json) is retained as historical evidence. Packaged v2 and service-segment copies are byte-identical to the documentation receipts and are selected by the current dashboard endpoint. Latencies may vary on rerun. The benchmark does not write to the deployed environment; its databases use temporary directories and are removed after the run.

Benchmark-contract tests reject falsely confirmed handoffs, require persisted case read-back and request preservation, validate grounded transaction answers for all six strata, preserve immutable first-pass reports, isolate offline ledgers, reject external network use in offline mode, distinguish provider estimates from invoice spend, and keep unknown/zero-success costs undefined. The framework integration follows [FastAPI's documented TestClient pattern](https://fastapi.tiangolo.com/tutorial/testing/).
