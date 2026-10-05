# Chat experience and judging audit

Reviewed against the four PDFs supplied on October 4, 2026, current repository documentation, published evaluation receipts, and read-only GitHub/connector searches. Organizer documents are evidence; their submission instructions do not authorize organizer delivery. **No submission, email, or organizer upload is part of this work.**

## What determines the score

The kickoff's **page 20** leads with “First and foremost our solution should work.” Its five assessment areas are project rationale/documentation, AI engineering (backend/frontend/deployment), data analytics (quality/relevant insights), data engineering (extraction/transformation), and machine learning (selection/optimization/implementation/tracking). **The supplied sources publish no numerical weights or points.**

The problem statement's **page 3** explicitly makes depth, demonstrated behavior, and engineering judgment determine the score. More workflows receive no automatic bonus. Page 4 makes training a new model, multiple agents, tool counts, streaming, demand forecasting, and a dashboard optional. A coherent transaction-support workflow with trustworthy answers and useful human follow-up is the priority.

Engineering priorities below are our interpretation of those criteria, not invented organizer weights:

1. Make one complete customer conversation work immediately: enter the chat, write in ES/PT, identify the intended authorized transaction conversationally, get the correct sourced answer or appropriate clarification, and retain context.
2. Keep controlled actions and human handoff reliable while removing interaction friction: preserve the specific request, show the proposed case, obtain explicit confirmation, persist once, verify independently, and support the analyst's question/customer reply.
3. Improve measured intent errors and unsupported-request handling. Extra pages or unrelated features cannot compensate for a wrong outcome.
4. Preserve data/ML rigor and refresh the evidence that changed behavior invalidates. Distinguish regression improvement from untouched held-out evidence.
5. Give reviewers a reproducible working demonstration and concise rationale with current limitations. Refresh obsolete persona/selector instructions and media when the final experience changes.

## Requirements and evidence

This maps the audited baseline and acceptance conditions for the chat improvement. The current scoped verification below records what passed; it does not establish universal request coverage.

| Requirement and source | Existing implementation/evidence | Acceptance condition for this change |
| --- | --- | --- |
| Data-backed focused problem; statement pp. 2–3 | `profile.py`, `docs/DATA_FINDINGS.md`, aggregate audit: transactional contacts 240,056/686,296 (34.98%); verified core joins | Preserve the transaction-support rationale; no invented production demand or savings |
| Normal resolution; statement p. 3, kickoff p. 11 | `workflow.py`, authorized fixtures, `tests/test_workflow_evidence.py`, `tests/test_system_evaluation.py` | Correct amount/currency/status/source/as-of from the intended authorized record through chat |
| Ambiguity/unsupported request; statement p. 3 | Persisted pending intent and clarification, safe action enums; continuity/security tests | Ask only for missing information; refuse unsupported bank actions clearly; do not silently guess a transaction |
| Conversational context; statement p. 3, kickoff p. 11 | `api.py` session context/revision, `workflow.py`, `tests/test_workflow_continuity.py` | Natural selection replies preserve the request; clear new requests take precedence; reload/retry do not lose or duplicate confirmed work |
| Spanish and Portuguese; statement p. 3 and p. 6 | ES/PT response dictionaries; paired language/component/system cases | Automatic language choice and language switching work without a language selector; short/ambiguous replies retain context |
| Controlled automation and authentication; statement pp. 3, 5 | Opaque trusted sandbox sessions, workspace/customer/role checks, CSRF/origin, no model SQL; `tests/test_api.py`, security/race tests | Automatic demo entry retains server-issued fixed identity and isolation; entered prose cannot switch role/customer/permissions |
| Grounding and source explanations; statement pp. 3–4 | Allowlisted validated transaction records and exact four-section synthetic policy retrieval | Facts remain exact; missing/bad records never receive invented values; evidence remains accessible in the chat |
| Useful human handoff; statement p. 3, kickoff p. 11 | Redacted specific allegation, verified facts, actions, evidence/open questions, append-only case events; `tests/test_case_conversations.py` | The entire request survives conversational selection, confirmation and analyst/customer follow-up; allegations remain distinct from verified facts |
| Confirm and verify action; statement p. 3, kickoff p. 11 | Expiring proposals, independent confirm endpoint, atomic idempotency, fresh read-back; API/concurrency/fault tests | Removing dropdowns preserves explicit informed confirmation and independent verification; no model-generated success receipt |
| Repeatable preparation/contracts/lineage/updates; statement pp. 3–4 | `data_pipeline.py`, deterministic manifests, quarantine, atomic replacement, strict-prior features; `tests/test_data_pipeline.py` | Retain core contracts and fixture provenance; UI changes do not expose private organizer records |
| Learned component and baseline/leakage; statement pp. 3–5, kickoff p. 12 | Frozen grouped intent splits, train-only fitting, rules/TF-IDF/local Gemma component comparison; language/ML reports | Do not retune on a known test set then describe it as untouched; record model/prompt/source versions |
| Held-out outcomes and failures; statement pp. 3–6 | Published full-system baseline/proposed workloads, preserved first-pass challenge, regression/fault reports | Re-run regressions for changed behavior; test automatic language/reference/no-selection interaction separately; report all failures |
| Safe resolution, attempted automation, handoffs, unsafe outcomes; statement p. 6 | Explicit denominators, missed/unnecessary transfers, material errors and scoped unauthorized outcomes | Keep distinct metrics and sample sizes; containment or zero scoped unauthorized actions is not universal success/safety |
| Language/authorized customer segments; statement p. 6 | Paired ES/PT and six controlled status/currency strata in `service_segments.py` | Preserve small-sample and authored-label limitations; do not call these demographic fairness or native-language validation |
| Efficiency; statement pp. 4, 6 | Local HTTP p50/p95 and isolated all-run provider ledger | Include new chat steps in measured work; local/hosted timings and estimates/invoice costs remain distinct |
| Operations/privacy/reliability; statement pp. 2, 4–5, kickoff p. 15 | Traces, bounded retries/fallback, source-only non-root image, reproducible setup, minimized storage/deletion; `docs/OPERATIONS.md` | Preserve bounded retries, stale-response protection, cancellation/recovery and disclosed ephemeral free-host limits |
| Public repo/deployed link/4–6 slides/video; kickoff p. 18 | Existing public repo, v1.1 hosted/release receipts, six-slide deck and captioned video; `docs/SUBMISSION.md` | Final package must describe and demonstrate the final chat behavior; no organizer delivery |

## Highest-value measured gaps at the audit baseline

The historical published learned v2 replay has **122/140 correct outcomes**, **18 errors**, **7 unnecessary handoff proposals**, and **36/120 safe automated resolutions**. The separate inspected challenge regression has **63/70 correct outcomes**, **7 errors**, and **4 unnecessary proposals**. Sources: `docs/evidence/system-evaluation-v2.json` and `system-challenge-regression-v2.json`. These receipts describe their hashed source revision, not arbitrary later code.

| Observed failure class | Concrete existing regression example | Why it matters |
| --- | --- | --- |
| Negated human request | “No hables con un asesor todavía; dime el importe del movimiento.” / “Não fale com um atendente ainda; diga o valor do lançamento.” becomes a human proposal | Adds friction and unnecessary transfers despite an answerable request |
| Affirmed transaction authorization | “Quiero ver la información de una transferencia que sí autoricé.” becomes a dispute | Reverses the customer's meaning |
| Overconfident scam routing | A recipe request or vague “algo no me cuadra” becomes a scam proposal | Fails appropriate refusal/clarification and undermines trust |
| Unsupported action routed to clarification | Immediate refund, debt removal, mortgage approval or another person's address | The service must explain the supported path and action boundary clearly |
| Existing-case misrouting | “No quiero iniciar otra solicitud, solo consultar el avance de la que registré.” asks for a transaction | Creates avoidable repeated work |

Removing selectors adds behaviors outside the historical benchmark: automatic ES/PT detection, code switching, natural references/ordinal/date/amount/merchant disambiguation, and chat-first entry. Test them explicitly. Never assume that the historical 87.1% system result establishes those behaviors.

The remaining external-quality limitations are real: no independent human/native-Portuguese label review; external provider inference remains unverified in published evidence; public test identity is not real-bank authentication; free-host cases are ephemeral. The brief permits a documented sandbox and asks for an honest route to production, so these are disclosed boundaries rather than reasons to add unrelated infrastructure.

## Final scoped local verification

The final source passes `make check` with **413 tests**, Ruff lint/format checks, JavaScript parsing and diff checks. The [current Chrome receipt](evidence/chat-browser-checks.json) records **27 checks**, including immediate entry without selectors, same-identity ES/PT switching, exact natural references, one-composer replies, confirmation/cancellation/recovery, four persisted events, short responsive viewports, and fresh unknown-payment/unanchored-reference clarification. Desktop viewport overrides do not verify native mobile keyboard behavior, Safari or formal screen-reader access.

The source-matched [140-case v3 regression](evidence/chat-system-regression.json) measures **130/140 learned versus 83/140 rules**, **38/120 versus 31/120 safe automated resolutions**, and **60/60 versus 28/60 required handoffs**. The learned system retains **10 errors**, including two requests naming an unseeded CASE-009 fixture, and one unnecessary proposal. The [70-case exposed challenge regression](evidence/chat-challenge-regression.json) measures **64/70 versus 48/70**, **18/60 versus 16/60 safe automated resolutions**, and **30/30 versus 19/30 required handoffs**. It retains six learned errors and two unnecessary proposals. Both learned workloads record zero material errors, zero scoped unauthorized outcomes and 22/22 passing fault cases; those bounded observations are not universal safety claims.

The [six authorized status/currency strata](evidence/chat-service-segment-regression.json) each produce 130/140 learned versus 83/140 rules with zero paired attribute-outcome changes. The repeated 840 replays per system still contain 140 unique authored utterances. Learned language slices are ES 64/70 and PT 66/70 in the main regression, and ES 31/35 and PT 33/35 in the challenge. All runs recorded zero provider attempts. Historical component/first-pass evidence and the unscored prospective corpus remain unchanged.

The v3 case scorer requires the actual returned persisted case, localized status, timestamp, evidence and pending question. It is stricter than v1.1, so old and new percentages cannot be directly compared. These exposed authored reruns have no independent human/native-Portuguese label review. Final receipt SHA-256 values are `6cd2362dd30313843ceeac914407b6d748a59dcd98db5a1514ea721fa093b34b` (140), `ca9dddeb7c0258d29263de61e6d3a18dbdf64eaf27b4a1e7ec6b2d997ed83fdd` (70), and `32b3c8093dcd9c4108b142c40587ddc7ae1002427197958d129938727add6740` (segments). Their core source hashes, identical packaged copies and API selection were checked after the final source freeze.

## Final model review follow-up — verified locally

The requested final Claude Opus 5.5 review returned conditional approval. It traced source and selected evidence, ran no tests, viewed all six slides and three app captures, did not watch the video, and did not deeply audit provider/store/scorer/data/fraud/pipeline modules or every failure. Its conditional approval is not independent end-to-end or native-language validation. Its implementation findings are tracked separately from the GitHub/organizer inventory below. All five findings are corrected and verified locally:

| Finding | Completed disposition | Local verification |
| --- | --- | --- |
| F1: ordinary weekday/time/first-time words are mistaken for an ordinal selection, producing the wrong record | Implemented whole selection replies or ordinals directly modifying an option/transaction noun; exclude `segunda-feira`, `un segundo`, `primera vez` and calendar wording. Preserve the ordered references actually displayed | Passing lexical non-selection, narrowed/reordered and stale ES/PT regressions; exact record evidence and refreshed source hashes |
| F2: confirmation omits the named attached transaction | API and shared confirmation render show the exact attached ID, merchant, amount/currency and recorded status before creation; explicit general human requests attach no record | Passing actual specific/general confirmation checks; full desktop capture and 320×780 controls within the viewport |
| F3: role switching in another tab loses customer continuity | Separate role cookies preserve session continuity across customer/reviewer tabs without losing identity or pending work; role hints never grant permission | Passing shared-cookie-jar API and simultaneous Chrome tab checks for role, reload, proposal and reply continuity; backend/UI hashes |
| F4: later customer details do not augment the pending report | Bounded report merging retains original allegations and meaningful redacted follow-up details before confirmation | Passing allegation, clarification, added-detail and confirmation/read-back regressions; actual preview matches stored report |
| F5: reply screenshot contains an obsolete language response | All seven actual app captures recaptured on October 5 UTC and bound to final backend/static hashes | Portuguese lookup response matches the final source; current media manifests and reviewed renders bind the fresh screenshots |

The final local gates pass 413 tests and 27 scoped browser checks. Both v3 workloads and all six controlled strata were rerun after the source freeze, and packaged reports match the documentation bytes. The refreshed media demonstrate this local source. Planned deployment remains separate from local screenshot proof; no organizer submission is authorized.

## Comments and questions inventory

### GitHub: exhaustive repository read

On this audit, paginated `issues?state=all`, each issue's conversation comments, and every PR's reviews and inline comments were read through the official GitHub API. The repository has **zero standalone issues**, **six merged PRs (#1–#6)**, **zero conversation comments**, **zero reviews**, and **zero inline review comments**. There is no GitHub review comment to mark resolved. A final read-only audit of [PR #7](https://github.com/nicoceron/factored-hackathon-2026-nicoceron/pull/7) on October 5, 2026 UTC also found zero issue conversation comments, zero submitted reviews and zero inline comments through paginated official GitHub API reads. This covers available repository comments, not unseen organizer Slack discussion. PRs #2, #4 and #5 already record continuity, handoff/provider, and provider-status corrections; their implementation must remain preserved.

### Available organizer conversation evidence

The only connected Slack workspace is **Blue Marble Space**, not the Factored community. Exact public search found no Factored hackathon conversation. This does not establish that organizer Slack has no further comments. No private-channel/DM search was performed. Relevant Linear searches (Factored, Datathon, hackathon, Claro and banking, including archived items) found no relevant issue/project; retrieved false positives belonged to other projects. No external messages or updates were sent.

`docs/BRIEF.md` contains previously user-supplied Slack excerpts. Their dispositions are:

| Question/comment | Evidence/disposition |
| --- | --- |
| Free tier/costs | Organizer says paid resources are allowed, not required. Existing free implementation remains valid; this is not authorization to spend |
| Is cloud deployment optional? | No organizer answer in excerpts. Keep the kickoff's deployed-link requirement; existing hosted demo has separate receipts |
| Transcript/metadata mismatch | Full audit establishes 42 distinct customer utterances and untrustworthy intent-category mapping; do not use metadata as dispute ground truth |
| May teams generate dispute conversations? | No explicit organizer approval shown. Label team fixtures/labels distinctly and disclose their review limits; do not claim an approval |
| Event date after process date | Measured 1,106,307/4,425,008 (25.00%) calendar-date discrepancies; preserve both times and visible flags, with explicit conservative availability assumption |
| Currency for campaign cost/conversion | Dictionary p. 13 gives no currency. Exclude unsupported USD arithmetic; workflow transaction amounts retain their explicit currencies |
| What real production traffic does the sample represent? | No production multiplier established. Do not claim production savings, live FCR/CSAT, or causal business improvement |
| Customer IDs do not join | Exact measured core FK coverage and ownership/currency matches are documented; complaint origin IDs are all null, so never fabricate complaint/transcript links through customer alone |
| Kaggle/machine GitHub/registration email | Unanswered administrative questions; no app feature depends on them and no policy answer is invented |
| PowerShell access example | macOS uses documented AWS CLI via isolated participant `scripts/aws.sh`; no extra shell installation required |

Repository searches found no `TODO`, `FIXME`, `XXX`, or `HACK` implementation marker. Historical proposal/setup docs label their status explicitly; their proposed capabilities are not final feature claims.

## Source register

The exact supplied originals remain private under Downloads. The dictionary contains access credentials; no credential or raw access-page text is copied here.

| Supplied PDF | Authoritative pages |
| --- | --- |
| `Datathon_2026_Kickoff (2).pdf` | 6 timeline (visually verified; no cutoff hour/timezone); 10–15 behavior/rigor/operations; 18 deliverables; 20 judging criteria (visually verified) |
| `Factored AI & Data Hackathon 2026 (3).pdf` | 2–3 scope/score; 3–4 required competencies/optional architecture; 5 data/execution/evaluation boundaries; 6 exact outcome definitions |
| `LATAM_Bank_Complete_Data_Dictionary (4).pdf` | 3 provenance/quality/language; 4–14 table contracts; 15–16 joins; 18 caveats; access page deliberately excluded |
| `LATAM_Bank_Dataset_Summary (3).pdf` | 2 provenance and intentionally imperfect quality; 3 advertised counts; 5 language/currency/data caveats |

PDF documentation counts (~19 million) and advertised imperfections are expectations; `docs/DATA_FINDINGS.md` records measured source counts (23,495,188), key audits and concrete discrepancies. Optional dictionary use-case suggestions do not change the focused customer-service challenge.

## Historical media audit and completed refresh

At the initial audit, the v1.1 assets remained unchanged. `submission/build-demo.py` can rebuild the nine-scene narrated walkthrough using the bundled Python/Pillow, local FFmpeg/FFprobe and macOS `say`; all three command-line tools are present. It performs no network calls. Rebuilding alone would reuse obsolete screenshots and cannot demonstrate the new chat. The initial builder hardcoded October 2 capture provenance; the revised builder requires declared provenance for every new app capture. The old crop coordinates were fitted to the two-panel layout; current declared geometry has been freshly reviewed.

| Video scene | Exact input | What becomes obsolete |
| --- | --- | --- |
| 1, opening | `submission/demo-assets/login.jpg`; no crop | Visible ES/PT toggle, three persona choices and enter button. Replace with the immediate chat |
| 2, clarification/evidence | `customer-pt-evidence.jpg`; crop `[716,300,1470,924]` | The cropped answer asks the customer to select an operation and shows “Transação selecionada”; the full source also contains language controls and a transaction-selection panel. Replace with conversational disambiguation and natural reference |
| 3, confirmation | `specific-report-confirmation-es.jpg`; crop `[492,220,992,820]` | Modal contract remains relevant, but its captured background/layout is historical; recapture the current proposal and confirmation |
| 4, verified receipt | `customer-pt-receipt.jpg`; crop `[716,300,1470,924]` | Receipt is valid historical evidence, but the visible selected-transaction context belongs to the old interface; recapture the inline receipt |
| 5, customer answer | `customer-question-pt.jpg`; crop `[702,968,1446,1585]` | Separate customer case page becomes inline follow-up. Full source has an ES/PT control, outside this video crop |
| 6, closed history | `analyst-history-pt.jpg`; crop `[704,1035,1448,1470]` | Narration says “switching profiles”; the new route uses reviewer/customer links. Full source contains an obsolete resolution dropdown and language control; both are outside the final video crop |
| 7, architecture | `architecture-v2.png`; no crop | Regenerate from a source-matched deck if the responsibility/data-flow diagram changes; provider status remains separately unverified |
| 8, evaluation | `evaluation-v2.png`; no crop | Published old regression values/source hashes must remain historical or be replaced by separately rerun evidence |
| 9, customer reply/history | `customer-replied-pt.jpg`; crop `[704,969,1448,1585]` | Separate case-page framing becomes inline chat follow-up; full source's language control is outside the video crop |

The scene definitions and narration are in `submission/demo-scenes.json`; the builder regenerates `claro-demo.mp4`, timed SRT, `demo-script.md` and `demo-manifest.json`. It rejects a duration at or above three minutes. Fresh captures, source labels, crop geometry, narration, all rendered scenes, decode/stream checks and duration must be verified before treating a rebuild as final media. The published v1.1 release remains unchanged; the local fixed-name outputs have now been replaced by the current review materials.

The completed current rebuild references seven `chat-*.jpg` captures for the same nine narrative goals, with declared October 5 UTC capture provenance at `http://127.0.0.1:8096`. The updated Portuguese evidence belongs to the same original customer after a language switch: **TX-ES-102, COP 129000.00, pending**. No language change issues a different customer identity. The customer answers the analyst through the same composer after opening the saved question's reply mode. Deck source keeps six slides/editable charts and reads current v3 regression files separately from historical evidence; the stronger case-lookup scorer prevents directly comparing old and new percentages. All seven declared captures have been inspected, including the Spanish reviewer interface with Portuguese question/reply. Native image crops and scene crop rectangles preserve source screenshot pixels. The final six-slide editable PPTX/PDF passes package/geometry/chart/re-import checks and all six PDF-page visual reviews. The nine-scene video is 170.92 seconds at 1920×1080/24 fps with H.264, AAC mono and English captions; full decode passes and audio signal is measured. Exact manifests bind final reports, declared inputs, diagrams, crops and output hashes. Neither media QA nor local Docker/browser receipts prove deployment or independent human/native-language review.
