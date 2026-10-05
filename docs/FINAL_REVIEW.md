# Final hackathon review

**GO for the frozen hackathon demo.** Actual final review #8 completed on October 5, 2026 with initialized model `claude-opus-5-5` and configured effort `xhigh`: 35 turns, 34 read-only Read/Grep/Glob calls, successful exit and no material blockers. This record was written after that review; it does not claim the reviewer inspected this later record. No organizer submission, email, upload, tag or release was performed.

The requested experience is immediate customer chat, automatic Spanish/Portuguese, no language/persona/transaction selectors or dropdowns, grounded transaction answers, explicit informed confirmation and useful human follow-up. The supplied rubric prioritizes a working solution, depth, demonstrated behavior and engineering judgment. It publishes no numerical weights. [The requirement and available-comment audit](CHAT_RUBRIC_AUDIT.md) maps all supplied requirements and excerpts; it distinguishes accessible repository comments from unseen organizer Slack.

## Reviewed source and corrections

Application source: `6a4cf24fcb105d1587475d71c35c0de6ca4043ea`. [Source PR #15](https://github.com/nicoceron/factored-hackathon-2026-nicoceron/pull/15) merged after exact-head CI passed at `dd88d09f1b258af8d3aebab63238285358944127`; all three recorded push/PR checks succeeded. The sanitized review snapshot contained 241 files, including exact slide renders and the frozen supplemental probe. Its canonical input-manifest SHA-256 is `ace44656804743c9031ad5ca4463403ce3f7e6d23eb7bc0c85f88c400315a92a`. Organizer records/PDFs, credentials, cookies, accounts, private transcripts and raw reviewer thinking were excluded. The exact snapshot secret scan passed after independently verifying checksum-only detections against Git source and original receipt bytes.

Review #7 had returned GO with 42 turns and 41 read-only calls. Root independently reproduced both of its notes and made them required corrections. That older verdict does not approve the later application.

| Finding | Final correction | Evidence inspected by review #8 |
| --- | --- | --- |
| Q1: explicit `R$38,50` or `38,50€` could resolve or propose a USD record | Amount-adjacent unambiguous symbols constrain BRL/EUR through the existing scoped currency/amount/reference intersections. Merchant and ID exclusions remain. Bare `$` supplies no currency; no conversion, serving-contract expansion or invented record | Entire `references.py`; 23 added reference checks, genuine-denial and exact-merchant controls; four added public-probe symbol scenarios |
| Q2: a pure rejected amount during a factual lookup could change the task to dispute | Preserve supported pending intent before an early reference clarification, guarded by a real continuation and fresh review signals. Rejected or retained records never attach by elimination. Explicit new requests and genuine denial/scam/human signals retain priority | Actual API rejection/retry/reload/follow-up/confirmation tests, four injected-model-dispute controls, and ten added public-probe continuity scenarios |

If the customer rejects an amount and later deliberately selects it for review, the bounded redacted report preserves substantive contradictory statements in order. Exact-record confirmation displays that report before creation. The accepted behavior preserves the customer's allegation rather than rewriting it.

## Independent verification scopes

Render reports deployment `dep-db1v74cs728c73afmro0` as Live at the application commit above. Owner-reported deployment identity and independently checked public content/behavior are separate evidence. Later documentation/media packaging does not change or redeploy application source.

| Gate | Final observed result |
| --- | --- |
| Local source | 680 tests; Ruff lint and format on 74 Python files; JavaScript syntax and diff checks pass |
| Frozen main regression | Learned 130/140 versus rules 85/140; safe automated resolutions 38/120 versus 31/120; required handoffs 60/60 versus 30/60. Ten learned errors and one unnecessary proposal remain |
| Exposed challenge regression | Learned 64/70 versus rules 49/70; safe resolutions 18/60 versus 16/60; required handoffs 30/30 versus 20/30. Six learned errors and two unnecessary proposals remain |
| Faults and segments | 22/22 faults per system/workload; six status/currency strata each retain the same main outcomes and zero paired changes. There are 140 unique authored utterances, not 840 independent labels |
| Regression provenance | All 43 source bindings and three byte-identical packaged reports match; corpus, model, fixtures and scorer remain frozen |
| Docker | Source-only non-root image and actual ES/PT lifecycle smoke pass; image SHA-256 `391c7f71c0ad0892b5602e36ad0082853a2faa0ab1e202fc34bb5c01a8a17305` |
| [Public HTTPS](evidence/chat-deployed-api-checks.json) | 26 checks: exact eight assets, three SHA resource URLs, six reports, authorization/isolation and complete bilingual case/question/reply/history/closure/retry/deletion workflows |
| [Returning Chrome](evidence/chat-deployed-browser-checks.json) | 22 observed checks: single composer/zero selectors, genuine ambiguity, retained reports, exact native confirmation, independent roles/reload, verified reply and locale, four events, closure, 320×780 controls and zero console errors |
| [Supplemental public conversations](evidence/chat-deployed-conversation-checks.json) | 70/70 authored scenarios; 28 verified cases, 68 chat retries, 28 confirmation retries, all 70 owned workspace deletions and zero provider attempts; reports equal before/after |
| [Media](evidence/chat-media-checks.json) | 21 checks; six visually reviewed editable slides, three native charts/workbooks, nine reviewed composed scenes, 170.920736-second video, clean full decode/audio and 29 equal embedded/external English captions |
| Available comments | Paginated GitHub audit through source PR #15: zero standalone issues, conversation comments, submitted reviews or inline comments. Supplied organizer excerpts are individually mapped; no unseen Slack audit is claimed |

The learned regressions record zero scoped material, unauthorized and missed-handoff outcomes. Those observations coexist with the retained errors; they establish neither universal safety nor real production performance. The stronger v3 case-grounding scorer prevents direct comparison with older percentages.

The original seven local media captures retain their actual source revision. Four current hosted captures are separate evidence; the restored-reply capture explicitly uses a fresh repeated case after the page animation settled, while confirmation/history retain the main closed-case walkthrough. Historical receipts and captures remain immutable. Root and an independent quality agent recomputed the final bindings, inspected all six exact PDF pages and verified video/caption/audio outputs.

## What Claude inspected

Review #8 read the complete compact evidence index, rubric audit and reference resolver; inspected `workflow.py` lines 185–680, language normalization/negation/signals, the cited API-sequence and injected-model tests, the supplemental probe and current receipt headers. It directly traced Q1/Q2, P1–P3, F1/L1/N1/N2 grammar, F7 continuation restoration and M1 denial handling. It viewed all six exact slide renders and all four current hosted PNGs.

It relied on existing receipts for F3 cookies/CSRF, F6 caching, F8 reply transactions, P4/F4 redaction, data/ETL/ML/fraud, frozen metrics, CI/comments, manifests and historical provenance. It ran no tests, network checks, hash recomputation or video decode, edited nothing, and did not watch the MP4. Root and quality verification above are separate from that read-only review. This is a scoped hackathon review, not production or security certification.

## Accepted minor observations and limits

Claude inferred, without reproducing it, that unit-before-amount prose such as `cobrança de USD 38,50` or `US$ 38,50` can enter conservative merchant clarification. It identified no wrong attachment or action. This remains a disclosed grammar limitation, alongside safely clarified spaced/ambiguous decimals. Rejection wording could be more natural; one compact `de38.50` test also has spaced-form coverage; slide 3's Jev acronym is explained in [the provider documentation](AI_PROVIDERS.md). These were expressly non-blocking review observations, not new required features.

The exposed authored regressions have no independent human/native-Portuguese label review. Identities and policies are synthetic, with no bank-managed authentication or bank integration. External inference is disabled and unverified. Free hosting has cold starts and ephemeral state. Safari, native mobile keyboards and formal accessibility certification remain unverified. The video is an edited narrated screenshot walkthrough built from disclosed earlier local captures. No universal request coverage, production uptime, causal business benefit or organizer acceptance is claimed.
