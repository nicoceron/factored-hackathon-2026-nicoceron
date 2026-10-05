# Claro · Banking support with verified outcomes

**Factored AI & Data Hackathon 2026 · team nicoceron**

A bilingual customer-service prototype that explains historical transactions, clarifies ambiguous requests, and creates confirmed, verified cases for human review. Analysts can ask a specific question, customers can reply, and both can read the persisted case history. Spanish and Portuguese share the same permissions and workflow. The public demo uses explicitly team-authored fixtures; private organizer records never leave the local data pipeline.

**[Open the live chat demo](https://claro-banking-hackathon-2026.onrender.com)** · [Current presentation and video](submission/README.md) · [Rubric evidence](docs/RUBRIC.md)

[Final review](docs/FINAL_REVIEW.md): Claude Opus 5.5 at configured xhigh returned **GO** for the frozen hackathon demo, with no material blockers. The record distinguishes its read-only inspection from executed checks and retains the remaining limits. Nothing has been submitted to organizers.

The chat redesign is verified on Render Free at application commit `6a4cf24fcb105d1587475d71c35c0de6ca4043ea`: **680 local tests**, [26 public HTTPS checks](docs/evidence/chat-deployed-api-checks.json) and [22 observed Chrome checks](docs/evidence/chat-deployed-browser-checks.json). Supplemental [conversational HTTPS checks](docs/evidence/chat-deployed-conversation-checks.json) cover authored reference and denial cases separately. The current six-slide presentation and 170.92-second video are in [submission/README.md](submission/README.md); the published [v1.1 release assets](https://github.com/nicoceron/factored-hackathon-2026-nicoceron/releases/tag/v1.1.0) remain historical. Original local screenshots retain their capture revision; supplemental hosted screenshots verify the final source. The free service can take about a minute to wake and may reset cases/sessions on restart. External providers remain disabled; Jev/DeepSeek adapters are implemented and mocked, with live inference unverified.

## Try it locally

```bash
make setup          # Python 3.12 + locked uv environment, including CPU ML tools
make check          # lint, formatting, integration/security/data/ML tests
make dev            # http://127.0.0.1:8000
```

Open the page and start chatting. The application creates an isolated demo session automatically; there is no persona or language selector. Write in Spanish or Portuguese and refer to a transaction by its merchant, amount, currency, date or displayed reference. If several records fit, Claro asks for clarification in the conversation. Language follows the message while short replies retain the conversation's language.

Report an unrecognized charge, review the evidence and explicitly confirm the proposed case. Open **Revisión humana / Análise humana** (`/?review=1`) in the same browser to inspect the handoff, ask a question or close the sandbox review. Return to `/` for the customer conversation and case follow-up. Analyst actions use direct buttons rather than dropdowns. Each browser receives an isolated workspace. These are trusted **test identities**, not real-bank authentication. Current verification status is in [UI.md](docs/UI.md).

Three paths to demonstrate in either language:

| Path | Spanish | Portuguese | Expected result |
| --- | --- | --- | --- |
| Explain | ¿Cuál es el estado del cargo de Tienda Demo? | Qual é o estado da cobrança da Tienda Demo? | Exact recorded amount, currency, status and source |
| Clarify | ¿Y esa operación? | E essa operação? | Ask which operation; preserve the pending request |
| Human review | No reconozco este cargo | Não reconheço essa cobrança | Propose a case; confirm; read back a verified receipt |

No real money movement, card blocking, credit approval, or refund promises are available. An unsuccessful write/read-back never yields a success receipt.

## What is implemented

- Chat-first customer UI with automatic ES/PT, conversational transaction clarification, sourced answers, confirmation and inline case follow-up; a separate analyst/reviewer workspace.
- Opaque expiring sessions, CSRF/origin controls, workspace/customer isolation, explicit action confirmation, idempotent retries, persistent local cases, and read-back verification.
- Jev one-shot typed intent classification and DeepSeek Flash conversational wording behind explicit server-side configuration and a usage budget. The local learned classifier and deterministic responses remain available without external calls. See [provider contracts and verification status](docs/AI_PROVIDERS.md).
- Versioned synthetic policy evidence, exact transaction tools, redacted customer-specific handoffs, two-way case follow-up, append-only case history and workspace-scoped operational analytics.
- Full organizer-data audit, deterministic typed preparation/lineage, strict-prior features, temporal fraud experiments, calibration and analyst-capacity metrics.
- Reproducible component and complete-system evaluation with failure cases, language slices and limitations.

### Evidence and deliberate choices

The original audit measured **23,495,188 rows across 13 tables**, including **4,425,008 transactions**. Dialogue records collapse to 42 distinct customer utterances and do not supply trustworthy dispute labels or Portuguese coverage. We therefore keep organizer analytics, independent language scenarios, and public demo fixtures separate.

On 140 frozen team-authored intent cases, the local TF-IDF/logistic component achieved macro-F1 **0.8230**, versus **0.4207** for keyword rules and **0.8045** for local Gemma 3 4B. This is a developer-authored synthetic benchmark with no independent human/native-language review; it is not a production accuracy claim or a claim of universal model superiority. See [the methodology and failures](docs/LANGUAGE_EVALUATION.md).

The transaction-risk models **failed the validation promotion gates**. Their ranking offered little useful improvement at a 1% analyst review budget. The released baseline is explicitly a historical population prior, not a personalized fraud verdict. Demo fixtures are out of domain and receive no probability. Customer reports still trigger review. See [the ML report](docs/ML_REPORT.md).

Four policy sections use exact retrieval. Jev supplies typed judgments; DeepSeek can add contextual acknowledgement and clarification while the service preserves its authoritative response and evidence verbatim. Neither provider can execute a banking action. Identity, record access, confirmation, workflow transitions and action verification stay in deterministic code. SQLite provides transactional local persistence for this single-worker prototype; the public free host may lose sandbox state on restart. The route to durable, bank-managed operation is described in [OPERATIONS.md](docs/OPERATIONS.md).

## Reproduce the data and evaluations

```bash
make data-plan      # separate participant AWS profile, preview only
make data-sync      # organizer source files; private local data/
make profile        # raw audit, hashes and DuckDB database
make pipeline       # contracts, lineage, quarantine, private serving snapshot + features
make train-fraud    # local CPU experiment, temporal holdout and release decision
make evaluate       # HTTP workflow replay and fault cases; no model API spend
make docker         # allowlisted source-only Docker context
```

Read [SETUP.md](docs/SETUP.md) for participant access. Data and modeling evidence: [DATA_FINDINGS.md](docs/DATA_FINDINGS.md), [DATA_PIPELINE.md](docs/DATA_PIPELINE.md), [ML_REPORT.md](docs/ML_REPORT.md), [LANGUAGE_EVALUATION.md](docs/LANGUAGE_EVALUATION.md), [SYSTEM_EVALUATION.md](docs/SYSTEM_EVALUATION.md).

## Submission and review

[SUBMISSION.md](docs/SUBMISSION.md) tracks the public repository, deployed link, 4–6 slide deck and video of at most three minutes. **Do not submit or email these materials: the owner explicitly excluded organizer delivery.** Closing date: **October 5, 2026**; the supplied materials do not establish an exact hour/timezone. [BRIEF.md](docs/BRIEF.md) maps source requirements, and [RUBRIC.md](docs/RUBRIC.md) maps implementation to evidence.

The original [architecture proposal](docs/ARCHITECTURE.md) and [build plan](docs/PLAN.md) remain historical decision context. The implemented architecture and deviations are in [OPERATIONS.md](docs/OPERATIONS.md). [CHAT_RUBRIC_AUDIT.md](docs/CHAT_RUBRIC_AUDIT.md) maps the supplied judging criteria, requirements and available comments to the focused chat work. Component evidence must not be confused with full-system outcomes or deployment proof.

## Repository boundaries

Never commit organizer PDFs, credentials, source/derived customer records, databases, raw transcripts or private reports. The dictionary PDF contains access credentials. Public JSON artifacts contain reviewed aggregate metrics, numeric model weights, or explicitly team-authored test fixtures. The Docker build allowlist excludes raw data, local reports and credentials. Deployment/release uses only reviewed source and safe artifacts. No external model receives organizer records.
