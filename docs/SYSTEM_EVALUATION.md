# Workflow evaluation and its limits

This benchmark sends real HTTP requests through FastAPI `TestClient`, persisted sessions, the workflow, SQLite proposals/cases, explicit confirmation, and committed read-back verification. It compares the **same workflow with keyword rules versus the released learned classifier**. Both receive the same deterministic safeguards. No cloud model or organizer customer record is used.

The 140-case workload replays the frozen language test corpus described in [LANGUAGE_EVALUATION.md](LANGUAGE_EVALUATION.md). Its model-level results remain a held-out classification experiment because model weights and thresholds were frozen before that evaluation. **The system results below are a developer regression replay:** the first workflow run exposed two legitimate scam reports blocked by privacy filters and two overlapping scam/dispute reports delayed by transaction clarification. Deterministic safety behavior was corrected and the workflow replayed. These final numbers must not be described as an untouched or independently reviewed end-to-end test.

## Reference behavior and replay protocol

Every case gets a fresh isolated browser workspace and a trusted demo session in its reference language. The corpus is synthetic and uniformly balanced, rather than sampled from production demand. Existing-case scenarios get a permitted support case created through the same API before measurement. The replay then submits the exact corpus utterance:

- Transaction status and dispute cases answer a transaction-clarification prompt with an explicit selection of the first authorized fixture transaction. Selection comes from the simulated user, not an inferred merchant match.
- Ambiguous cases remain ambiguous; the harness never invents a transaction selection for them.
- A case proposal is confirmed only when the reference scenario requires a human. Wrong proposals on other intents are recorded and remain unconfirmed.
- A transfer succeeds only when the action response has a verified receipt and a subsequent authenticated case read returns that same stored case.
- A normal answer must return the selected authorized record, its evidence/source, amount, currency, localized status, ID, and historical as-of date.
- Case lookup must read the previously created case and its stored status. This tests the list/read workflow, not semantic extraction of an arbitrary case ID mentioned in a sentence.

Entity recognition, matching fictional merchants in an utterance to real transaction candidates, multi-party adjudication, natural confirmation behavior, and analyst judgment of summary usefulness are outside this benchmark. Packets are checked for required fields, correct reference intent, scam priority, and dispute transaction evidence; that is a structural usefulness proxy, not human approval of a summary.

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

Cancellation was then restricted to an explicit command rather than any sentence containing the verb. The [separately labeled regression rerun](evidence/system-challenge-regression.json) on the corrected release achieved **63/70 learned outcomes and 30/30 required handoffs**, versus 43/70 and 19/30 for rules. **Seven learned outcomes remain incorrect, including four unnecessary handoff proposals.** Zero materially wrong outcomes under the narrower definition below must not be described as zero errors. All 22 current fault cases passed for each system. The rerun's learned local p50/p95 was 8.57/15.24 ms; rules were 5.25/12.13 ms. This unisolated development host's timing varied substantially between runs, so these are observations rather than a latency guarantee. The model and thresholds were unchanged. The first-pass report retains the historical source hashes and results; the current source reproduces the corrected regression, not the old defect.

## Measured 140-case regression results

Each recorded benchmark uses a sequential replay in one process on the development Mac. The final regression refreshes ran concurrently on the shared development host, so CPU contention is included and timings are not isolated measurements. Reported latency includes in-process HTTP chat, any clarification and confirmation, and read-back requests. It excludes session/fixture setup, hosted network delivery, user thinking time, and queue time. This is not a production capacity or hosted latency measurement.

| Metric | Rules + safeguards | Learned + safeguards |
| --- | ---: | ---: |
| Correct reference outcomes / all cases | 77/140 (55.0%) | **122/140 (87.1%)** |
| Correct automated resolutions / all in-scope cases | 31/120 (25.8%) | **36/120 (30.0%)** |
| Attempted automation / all cases | 47/140 | 37/140 |
| Required handoffs verified | 28/60 | **60/60** |
| Required handoffs missed | 32/60 | **0/60** |
| Handoffs with correct intent, priority and required packet fields | 28/28 | 60/60 |
| Unnecessary handoff proposals | 4/140 | 7/140 |
| No verified transfer (“containment”) | 80.0% | 57.1% |
| Incorrect outcomes of any kind | 63/140 | 18/140 |
| Materially wrong outcomes under the definition below | 34/140 | 1/140 |
| Observed scoped unauthorized record/action outcomes | 0/140 | 0/140 |
| Measured local p50 / p95 | 4.69 / 11.22 ms | 7.85 / 15.51 ms |

“Safe automated resolution” requires a correct transaction answer or verified case lookup without a human transfer, divided by **all 120 in-scope cases**, including those expected to need clarification or a human. Unsupported requests are the 20 out-of-scope cases. The maximum possible automated rate on this deliberately balanced workload is 40/120; correct clarification, refusal, and human transfer count as correct outcomes but are not automated resolutions.

“Attempted automation” means a returned resolved or case-lookup state. “Containment” only means no verified transfer; false proposals, clarification loops, and missed transfers can inflate it. Higher containment in the rules system therefore does not mean better service.

“Materially wrong” is the explicitly defined subset of incorrect outcomes where the system returned a resolved/case-lookup state despite a different required result, or failed the required human-outcome contract. Other routing errors, refusals that should have clarified, unnecessary proposals, and failure to refuse unsupported requests remain visible in **all incorrect outcomes**. This metric is separate from the scoped unsafe-outcome check, which checks returned transaction ownership and unverified action receipts. A zero in that limited check does not establish universal safety.

Language slices have 70 cases each. Learned outcomes were **60/70 Spanish and 62/70 Portuguese**, with 18 automated resolutions and 30 verified required handoffs in each. Rules achieved 40/70 and 37/70. These small authored slices do not establish demographic fairness or native-language quality. No independent human language review has occurred.

The 18 remaining learned-system failures include negated human requests and affirmative transaction-recognition causing false proposals, unsupported requests causing clarification instead of a clear refusal, unrelated requests causing unnecessary scam proposals, and one ambiguous request sent to case lookup. The public evidence preserves every failed case ID, expected/predicted intent, state sequence, and the verification result. The system does not yet resolve every language variation correctly.

## Failure injection

A separate, explicitly oversampled fault suite runs eleven checks in each language for each system: unauthenticated record access, foreign-customer reference, missing CSRF token, expired session, model timeout, failed committed read-back, retry with the same idempotency key, prompt injection, missing transaction amount, unknown currency, and invalid transaction status. **22/22 passed per system**. The current tool boundary validates an allowlisted Pydantic record before financial text, risk inference or case evidence. Malformed or conflicting selected records produce a human-review proposal without claimed transaction facts; 33 targeted tests additionally cover missing provenance/source/as-of, non-finite/negative/numeric amounts, invalid dates, unexpected fields, and duplicate references. For a failed read-back, the API returns 503 without a receipt; retry verifies one stored case rather than creating another. The model timeout check supplies a deterministic injected timeout, not an observed provider outage.

The broader API tests also exercise cross-browser workspace isolation, analyst permissions, concurrent confirmation, request-key conflicts, cancellation/expiry, deletion, and retention boundaries. Unit-test success and the fault suite are supporting engineering evidence; neither replaces hosted-browser QA or proves absence of other attack paths.

## Cost and reproducibility

Measured model API spend was **$0** for both systems. Model API cost per attempted case and per successful automated resolution is $0; the latter is reported as undefined if a run has zero successful automated resolutions. Hardware, electricity, and hosting costs are unmeasured and excluded. No production savings, revenue, avoided fraud, or representative per-customer operating cost is claimed.

```bash
uv run --locked python -m factored_banking.system_evaluation \
  --output artifacts/system-evaluation.json
# Challenge replay is regression once its first run has been inspected:
uv run --locked python -m factored_banking.system_evaluation \
  --challenge-corpus src/factored_banking/resources/system_challenge_test.json \
  --challenge-regression \
  --output artifacts/system-challenge-regression.json
uv run --locked pytest -q tests/test_system_evaluation.py tests/test_api.py tests/test_workflow_evidence.py
```

The [aggregate evidence](evidence/system-evaluation.json) records corpus SHA-256 and exact API, workflow, language, and evaluation-source hashes. A packaged identical copy is served to the demo dashboard. Latencies may vary on rerun. The benchmark does not write to the deployed environment; its databases use temporary directories and are removed after the run.

Three benchmark-contract tests verify that a false handoff is never automatically accepted or counted as success, a real dispute needs persisted case read-back, grounded transaction resolution is recognized, and zero-success cost denominators remain undefined. The framework integration follows [FastAPI's documented TestClient pattern](https://fastapi.tiangolo.com/tutorial/testing/).
