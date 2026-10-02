# Claro · Banking support with verified outcomes

**Factored AI & Data Hackathon 2026 · team nicoceron**

A bilingual customer-service prototype that explains historical transactions, clarifies ambiguous requests, and creates confirmed, verified cases for human review. Spanish and Portuguese share the same permissions and workflow. The public demo uses explicitly team-authored fixtures; private organizer records never leave the local data pipeline.

**[Open the live demo](https://claro-banking-hackathon-2026.onrender.com)** · [Presentation and video](https://github.com/nicoceron/factored-hackathon-2026-nicoceron/releases/tag/v1.0.0) · [Rubric evidence](docs/RUBRIC.md)

The free service can take about a minute to wake. Cases and sessions are temporary and may reset when the host restarts.

## Try it locally

```bash
make setup          # Python 3.12 + locked uv environment, including CPU ML tools
make check          # lint, formatting, integration/security/data/ML tests
make dev            # http://127.0.0.1:8000
```

Choose a demo customer, ask about a transaction, or report an unrecognized charge. Review the evidence and confirm the proposed case. Switch to the analyst persona in the same browser to inspect the handoff and record a review outcome. Each browser receives an isolated workspace. These are trusted **test identities**, not real-bank authentication.

Three paths to demonstrate in either language:

| Path | Spanish | Portuguese | Expected result |
| --- | --- | --- | --- |
| Explain | ¿Cuál es el estado de esta transacción? | Qual é o estado desta transação? | Exact recorded amount, currency, status and source |
| Clarify | ¿Y esa operación? | E essa operação? | Ask which operation; preserve the pending request |
| Human review | No reconozco este cargo | Não reconheço essa cobrança | Propose a case; confirm; read back a verified receipt |

No real money movement, card blocking, credit approval, or refund promises are available. An unsuccessful write/read-back never yields a success receipt.

## What is implemented

- Customer and analyst web UI, ES/PT, responsive layouts and accessible controls.
- Opaque expiring sessions, CSRF/origin controls, workspace/customer isolation, explicit action confirmation, idempotent retries, persistent local cases, and read-back verification.
- Local learned intent classification, a keyword baseline and a local Gemma 3 4B challenger benchmark. Runtime has no paid/external model calls.
- Versioned synthetic policy evidence, exact transaction tools, minimized structured handoffs and workspace-scoped operational analytics.
- Full organizer-data audit, deterministic typed preparation/lineage, strict-prior features, temporal fraud experiments, calibration and analyst-capacity metrics.
- Reproducible component and complete-system evaluation with failure cases, language slices and limitations.

### Evidence and deliberate choices

The original audit measured **23,495,188 rows across 13 tables**, including **4,425,008 transactions**. Dialogue records collapse to 42 distinct customer utterances and do not supply trustworthy dispute labels or Portuguese coverage. We therefore keep organizer analytics, independent language scenarios, and public demo fixtures separate.

On 140 frozen team-authored intent cases, the local TF-IDF/logistic component achieved macro-F1 **0.8230**, versus **0.4207** for keyword rules and **0.8045** for local Gemma 3 4B. This is a developer-authored synthetic benchmark with no independent human/native-language review; it is not a production accuracy claim or a claim of universal model superiority. See [the methodology and failures](docs/LANGUAGE_EVALUATION.md).

The transaction-risk models **failed the validation promotion gates**. Their ranking offered little useful improvement at a 1% analyst review budget. The released baseline is explicitly a historical population prior, not a personalized fraud verdict. Demo fixtures are out of domain and receive no probability. Customer reports still trigger review. See [the ML report](docs/ML_REPORT.md).

Four policy sections use exact retrieval. Identity, record access, confirmation, workflow transitions and action verification stay in deterministic code. SQLite provides transactional local persistence for this single-worker prototype; the public free host may lose sandbox state on restart. The route to durable, bank-managed operation is described in [OPERATIONS.md](docs/OPERATIONS.md).

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

[SUBMISSION.md](docs/SUBMISSION.md) tracks the actual public repository, deployed link, 4–6 slide deck and video of at most three minutes. Closing date: **October 5, 2026**; the supplied materials do not establish an exact hour/timezone. [BRIEF.md](docs/BRIEF.md) maps source requirements, and [RUBRIC.md](docs/RUBRIC.md) maps implementation to evidence.

The original [architecture proposal](docs/ARCHITECTURE.md) and [build plan](docs/PLAN.md) remain historical decision context. The implemented architecture and deviations are in [OPERATIONS.md](docs/OPERATIONS.md). Component evidence must not be confused with full-system outcomes or deployment proof.

## Repository boundaries

Never commit organizer PDFs, credentials, source/derived customer records, databases, raw transcripts or private reports. The dictionary PDF contains access credentials. Public JSON artifacts contain reviewed aggregate metrics, numeric model weights, or explicitly team-authored test fixtures. The Docker build allowlist excludes raw data, local reports and credentials. Deployment/release uses only reviewed source and safe artifacts. No external model receives organizer records.
