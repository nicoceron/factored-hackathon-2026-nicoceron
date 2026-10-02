# Optional Jev routing and DeepSeek conversational wording

The default application is local and free. External inference is disabled unless
the server explicitly enables it, has server-side credentials, and sets a positive
request budget. Implementation and mocked tests do **not** establish live provider
quality, account free credits, paid-use authorization, or deployed availability.

## Model and API choices

The adapter uses the official HTTP contracts through `httpx`, with Pydantic schemas
at each model boundary. Endpoints are fixed in code; no environment-controlled
base URL, proxy discovery, or redirect is permitted.

| Role | Request model | Endpoint | Role in the application |
| --- | --- | --- | --- |
| Semantic routing | `jev-1.13.0` | `https://api.typesafe.ai/v1/systemone` | One Choice and three independent Nouls in one normal request |
| Contextual wording | `deepseek-flash` | `https://api.deepseek.com/chat/completions` | Short ES/PT acknowledgement and optional follow-up around immutable deterministic facts |

As checked on 2026-10-02, TypeSafe identifies `jev-1.13.0` as its current version;
pinning avoids silent changes from its moving alias. TypeSafe says English is its
strongest language, so Spanish and Portuguese require workload-specific evidence.
See [TypeSafe models](https://docs.typesafe.ai/models).

DeepSeek currently maps `deepseek-flash` to **DeepSeek-V4.1-Flash**. We use the
documented current alias and record the model identifier returned by the API;
the provider may move that alias. See [DeepSeek models and pricing](https://api-docs.deepseek.com/quick_start/pricing/?tab=case-studies).

## One-request semantic classification

`classify(message, language="es", context=None)` returns the existing workflow
assessment (`intent`, `confidence`, `model_version`, `signals`) plus Choice
`probabilities`, independent `noul_probabilities`, and `provider_meta` when Jev
succeeds. Its finite intent set is `transaction_status`, `dispute`, `scam`, `human`,
`case_status`, `ambiguous`, and `unsupported`.

The request contains one Choice for primary intent and three Nouls for an actual
scam report, disputed transaction, and explicit human request. They share one
request/state; there is no serial model chain or model-controlled tool call. A
single explicitly marked team-authored development example illustrates a status
request. It is not a held-out example, organizer record, or human-reviewed label.
See the [TypeSafe API](https://docs.typesafe.ai/api), [Choice](https://docs.typesafe.ai/primitives/choice),
and [Noul](https://docs.typesafe.ai/primitives/noul) contracts.

The adapter validates the exact answer keys/types, all seven probabilities, their
sum, the winning label, and TypeSafe's reported Choice confidence calculation.
Non-finite numbers, booleans in probability fields, unexpected model versions,
extra fields, and malformed JSON fail closed. Choice confidence below `0.55`, or
any Noul strictly between `0.2` and `0.8`, abstains to human review. A Noul at or
above `0.8` adds its corresponding safety signal. These are **initial policy
thresholds, not demonstrated ES/PT calibration**. TypeSafe's distribution-derived
confidence is not a measured application accuracy percentage; see
[confidence semantics](https://docs.typesafe.ai/confidence).

A healthy Jev answer uses its validated semantic Nouls, not inherited lexical
safety flags that could override negation. The deterministic workflow still owns
authorization, scope, record selection, confirmation, policy, and receipt
verification. Unavailable, malformed, uncertain, or budget-blocked routing selects
human review; it never silently switches to an automatically acting lexical
route. With external AI disabled, the existing local model remains the explicit
local mode.

## Grounded response composition

`compose(message, language, workflow_result, history=None)` returns
`{message, used_provider, provider_meta}`. The composer receives a bounded redacted
current message/history and approved team-authored sandbox evidence. It receives
no credentials, identity claims, database handles, tool definitions, action
authority, or organizer data. Only the pending intent is included in Jev context.

DeepSeek runs with thinking disabled, temperature zero, output capped at 384
tokens, `stream: false`, and `response_format: {"type": "json_object"}`. Its JSON
must exactly match `language`, `acknowledgement`, `question`, and `evidence_ids`.
Application validation requires the requested language label, known evidence IDs,
bounded strings, completed output, and no tool calls. JSON mode alone does not
enforce our schema; empty/truncated output is rejected. See
[DeepSeek JSON output](https://api-docs.deepseek.com/guides/json_mode/) and
[chat completion API](https://api-docs.deepseek.com/api/create-chat-completion/).

The deterministic message is appended **verbatim** between the acknowledgement
and optional question. Generated text cannot mutate workflow state, evidence,
transactions, proposals, or receipts. A conservative output guard rejects digits,
links, currencies, financial statuses, completion/refund/approval language, and
requests for secrets or common personal data. Blocked/cancelled workflows and
unapproved or malformed evidence use deterministic text without a call.

This lexical output guard is defense in depth, **not a proof of arbitrary prose
semantics or factuality**. A JSON language label is also not an independent
language detector. Adversarial paraphrases may escape the wording guard; the
model has no banking action authority even then. Native-language review and a
prospective grounded-response evaluation remain necessary before claiming
production conversational quality. Rejected generation preserves the exact
deterministic answer and reports the fallback reason.

## Server configuration and lifecycle

`ProviderRuntime.from_env(enabled=None, budget_path=None)` reads process
environment only; it does not load a secrets file. `enabled=False` unconditionally
disables external calls even if the environment enables them, which is required
for offline baselines. The application uses the configured ledger path or a
database-adjacent default and closes the HTTP client during lifespan shutdown.

| Environment variable | Default | Purpose |
| --- | --- | --- |
| `CLARO_EXTERNAL_AI_ENABLED` | `0` | Only `1` opts into external mode |
| `TYPESAFE_API_KEY` | absent | Server-only Jev credential |
| `DEEPSEEK_API_KEY` | absent | Server-only DeepSeek credential |
| `CLARO_PROVIDER_BUDGET_USD` | `0` | Conservative cumulative reservation ceiling; zero blocks inference |
| `CLARO_PROVIDER_BUDGET_DB` | Application database path plus `.ai.sqlite` | Explicit ledger override; standalone runtime default is `.local/provider-budget.sqlite` |
| `CLARO_PROVIDER_BUDGET_ID` | `claro-provider-v1` | Namespace within the ledger; changing it starts a separate allowance |
| `CLARO_PROVIDER_MAX_REQUESTS` | `100` | Cumulative HTTP-attempt ceiling, including retries and failures |
| `CLARO_PROVIDER_MAX_ATTEMPTS` | `2` | Attempts per provider invocation, constrained to 1–3 |
| `CLARO_PROVIDER_TIMEOUT_SECONDS` | `6` | HTTP phase timeout and checked response elapsed limit, constrained to 0.1–15 |

Keys belong in deployment secret settings or an owner-only ignored local file,
never browser storage, public JavaScript, committed environment files, logs, or
evaluation artifacts. `status()` is configuration-only and performs no network
probe. `/readyz` therefore can stay free and side-effect-free; a
`configured_not_probed` status is not evidence that inference works.

The classifier and composer each bound requests to 32,000 serialized UTF-8 bytes
and responses to 64,000 bytes. Default connect timeout is at most two seconds;
other HTTP phases use the configured timeout. While streaming the response into
bounded memory, elapsed time is checked after each chunk. These are phase/read
limits rather than a hard end-to-end SLA across DNS, operating-system scheduling,
retries, both providers, and application work.

Only transient transport failures and selected overload/server statuses retry.
Authentication, redirects, schema failures, unsafe wording, and budget failures
do not retry. Backoff starts at 0.25 seconds; a numeric `Retry-After` up to one
second is respected, while a longer one returns `retry_deferred` without retrying
earlier than instructed. Every attempt reserves budget first. Provider error
bodies are discarded; only fixed, non-sensitive failure codes leave the adapter.

## Budget enforcement and honest accounting

SQLite `BEGIN IMMEDIATE` reserves money estimates and request slots atomically
across processes sharing the ledger. Reservations are not released, even when a
timeout or error prevents usage attribution: the provider may have billed that
attempt. Connections explicitly commit/roll back and close. A broken ledger
prevents outbound work and returns a safe unknown-cost fallback.

The input reservation uses serialized UTF-8 byte count plus 4,096 tokens of
protocol allowance; output uses its configured bound. This is deliberately
conservative for these short text requests, not a provider tokenization or billing
guarantee. Reported usage over a reservation invalidates the output and the larger
observed estimate counts against future reservations. Tariffs can change. An
account-level provider cap is needed for a hard financial guarantee.

The cumulative application cap survives process restart **only while the same
ledger and budget namespace survive**. The free Render service uses ephemeral
storage, so a deploy/restart that loses this file also loses prior reservations.
Do not describe this as a durable lifetime spending cap on that deployment.
Public metered deployment requires an approved durable budget store or an
independent provider/account spending ceiling; it is not enabled merely by
installing the adapter.

The 2026-10-02 estimate uses USD per million tokens:

| Provider | Input | Output | Estimate assumption |
| --- | ---: | ---: | --- |
| Jev | 0.042 | 0 | Published input tariff |
| DeepSeek Flash | 0.30 | 1.20 | Peak-hour, cache-miss input tariff |

These tariffs come from the official model/pricing pages linked above. DeepSeek
cache hits and off-peak discounts can reduce charges; estimated totals are not
invoice charges or proof of free credits. TypeSafe's
[MCA §8.2](https://typesafe.ai/legal/mca) makes promotional credits discretionary
and says they are consumed before purchased credits. Its public API documentation
does not establish that this specific account has promotional credit. Never
infer free usage from a working API key.

`snapshot()` returns a ledger cursor; `usage_since(cursor)` returns aggregate
attempts, observed input/output tokens, model IDs, tariff-estimated USD, retained
reservations, unknown-cost attempts, cost completeness, and provider breakdowns.
It never stores prompts, generated content, provider error bodies, credentials,
customer IDs, or provider request IDs. It stores a nullable scope ID containing
only the server-generated random sandbox workspace identifier. Scope accepts the
existing 32-character lowercase hexadecimal ID format, not a customer ID or a
free-text label. This opaque accounting association persists with the ledger; no
conversation text is retained there.

The application wraps classification and composition in
`with runtime.scope(workspace_id):`. A `ContextVar` isolates threads/requests,
supports nesting, and restores the previous value even if the turn raises or is
cancelled. Every reservation captures that scope **before** outbound work.
`usage_for_scope(workspace_id)` therefore accounts for failed inference and turns
discarded by a later conversation-revision check as well as committed responses.
Its totals are independent of the conversation event log. SQLite failure raises
an availability error rather than reporting zero spend. Schema migration leaves
legacy unscoped rows unattributed but still counted against the global budget.

Per-response metadata uses the invocation's exact attempt IDs so simultaneous
workspaces cannot inherit each other's costs. Global `usage_since` intentionally
includes all scopes and remains suitable for an isolated benchmark. Cursor deltas
require an isolated runtime/ledger if unrelated traffic could otherwise occur
concurrently. All scopes share the same budget namespace and request cap; entering
a new scope cannot create additional spending allowance.

Known token usage is retained even when output validation fails. Missing usage
does not become a claim of zero cost: `unknown_cost_attempts` increases,
`cost_complete` becomes false, and the reservation remains consumed. Public
pricing estimates cannot be labeled actual provider charges. Customer success
denominators must include all clarification/composition/retry attempts for that
scenario, with setup/warmup separated by the evaluator.

## Evidence and remaining validation

Run `uv run pytest -q tests/test_providers.py` for the provider contracts. The
current 64 mocked cases cover single-request typed routing, negation isolation,
uncertainty/threshold boundaries, redaction, malformed responses, schema and
grounding checks, retries, redirects, outages, budget exhaustion, concurrent
reservation safety, process restart, per-invocation and concurrent workspace usage
isolation, nested scope restoration after exceptions, legacy ledger migration,
ledger failure, immutable facts, and ES/PT composition boundaries. Mocked success
is not live model accuracy or latency evidence.

No provider inference was performed to implement these adapters. Before live
comparison, establish paid-use authorization or verify sufficient free credits,
freeze prompt/config/source hashes, choose thresholds on development data only,
then evaluate the independent prospective corpus once. Preserve that first pass,
including failures, abstention, latency, and all attributable usage. Existing
synthetic regression/holdout reports describe the local model and must not be
relabelled as Jev or DeepSeek results. Do not tune prompts on prospective test
texts or predictions and then report the rerun as an untouched holdout.
