# Claro interface

## Current chat redesign — local verification

The current source replaces the v1.1 persona entry screen, language controls, transaction-selection panel and customer dashboard with an immediate customer conversation. It creates a trusted sandbox session automatically. Browser preferences set the opening interface language; the server detects ES/PT per message and preserves the session language when a reply is too short to establish another language. The browser follows the returned language. Automatic language choice does not change customer identity or permission.

Transaction references are resolved against validated, authorized records. Explicit merchant details, amount/currency, ISO date or record reference can identify a unique record; ambiguity remains a conversational question. Ordinal replies refer to the candidates previously displayed in that conversation. The service does not guess an identity from a merchant or let a model choose record permissions. Answers retain exact financial evidence and historical dates.

Sources expand inside the chat. Proposed cases retain explicit confirmation and verified read-back receipts. Case details, pending analyst questions and persisted history open alongside the conversation. **Responder por chat / Responder na conversa** enters reply mode for the displayed pending question; the customer sends the answer through the same main composer. No second reply textarea is needed. The reply retains the exact saved question ID and uses the existing verified, idempotent mutation contract. The separate reviewer workspace at `/?review=1` contains the scoped analyst queue, operations and published evaluation; `/?review=1&view=evaluation` opens the evidence view. Asking a question and closing a review use direct actions. No language, persona or review-resolution dropdown is needed.

The implementation preserves native form/dialog semantics, a named chat log, keyboard send, draft/focus recovery, bounded retries and server cancellation. A bounded redacted conversation window supports session recovery; persisted case history remains the authority for confirmed work. The [current local Chrome receipt](evidence/chat-browser-checks.json) records 20 passing checks: immediate entry, natural references, same-customer ES/PT switching, redaction, explicit confirmation, verified case follow-up in one composer, four persisted events after reload, proposal recovery/cancellation, zero customer selectors, responsive viewport geometry (including a 390×300 short viewport) and an empty final warning/error log. Fresh unknown-payment predicates and unanchored case references also clarify without guessing a record. Screenshot and static-asset hashes identify the checked UI. The [Docker receipt](evidence/chat-docker-checks.json) records a local source-only non-root image, bilingual chat-only HTTP lifecycle, workspace cleanup and identical static/report bytes. These are local receipts. The final source passed `make check` with 352 tests, Ruff lint and formatting, plus JavaScript parsing and diff checks. Final v3 regression source hashes and identical packaged copies have been checked after the final backend guards; the final Docker image serves those exact reports and static assets and passes the bilingual HTTP lifecycle after readiness. The linked hosted demo remains v1.1. The current evidence view discloses the stronger v3 case-grounding scorer and prevents direct comparison with old v1.1 correctness percentages. Desktop viewport overrides approximate responsive layouts; real mobile keyboard behavior, Safari, formal screen-reader audit and native-Portuguese review remain unverified. No current deployment or live external inference is inferred from these local or historical receipts.

## Historical v1.1 interface and verification

The following sections describe the prior released interface and its October 2 checks. Selector, persona and dashboard descriptions apply to that source revision. They are retained as historical evidence and are superseded by the current source description above.

The interface is a responsive ES/PT customer and analyst workspace served by FastAPI from `src/factored_banking/static`. It uses native ES modules, Fetch, semantic HTML, CSS Grid, native dialogs, and local OFL-licensed DM Sans/Manrope font subsets. No browser package install, frontend build service, third-party runtime request, or paid API is required.

## Working flows

- Public demo personas create a server session for team-authored fixtures. The interface explicitly distinguishes the historical sandbox from real bank authentication. The entry screen and verified receipts warn that sessions and cases may be erased on a service restart. Persona changes preserve the browser's isolated workspace, allowing an analyst to review the customer's test case.
- The customer selects an authorized transaction, asks questions in Spanish or Portuguese, and sees currency-preserving amounts, snapshot dates, and expandable evidence. No organizer customer data is embedded in frontend assets.
- Multi-turn clarification uses the server context. Restored sessions show the current transaction context. Dismissing a proposal, removing a selection, or starting a new conversation calls the server reset endpoint, which invalidates pending proposals while preserving cases. Reset requests block new messages and transaction changes until completion; session-generation checks ignore stale results.
- A case proposal requires an explicit native confirmation dialog. The browser retains the same idempotency key when a confirmation request fails and is retried, up to three attempts. A proposal is shown as canceled only after server cancellation succeeds; failure leaves it available for a retry. A green receipt requires the server's explicit verified flag; an unverified receipt is labeled accordingly.
- Customer cases and the analyst queue fetch persisted records. Analyst results are restricted to `reviewed_closed` or `needs_information`; the latter requires a specific question. Customers see the pending question and can submit a reply that returns the case to review. Each reply carries the displayed question’s ID, so a stale tab cannot silently answer a replacement question. Both mutations require a verified receipt before the UI announces success. Closed cases show a read-only history without an enabled review form. Neither grants a refund nor determines fraud.
- Case history renders only the backend’s persisted chronological events, with actor, UTC timestamp, text and status. It does not synthesize a creation or latest-review entry. Specific redacted customer reports and open questions are shown before confirmation and in the analyst packet.
- New chat attempts, confirmation writes, analyst questions/reviews and customer replies are capped at three explicit attempts per operation. Retries preserve their original body/idempotency key. Uncertain case mutations lock the action form; a read-back can reconcile a matching `client_request_id` in the persisted timeline. Rejected validation requests can be corrected. No reload, matching text, or status alone is treated as proof of a write.
- A concise sandbox data-sharing notice precedes the chat. Session configuration and per-response `ai` metadata distinguish configured/used providers, local processing and fallback. Provider names/models come from the backend; a configured Jev or DeepSeek provider is never presented as used without response metadata. Only entered sandbox messages and minimized fixture context may go to enabled providers; organizer data is excluded.
- Operations uses workspace-scoped request, state, case and latency aggregates. Provider costs are tariff estimates, explicitly distinguished from invoices; unknown usage renders unavailable, and provider/unknown-cost attempt counts are visible. Small nonzero estimates retain up to six decimal places instead of rounding to a false zero. The verified counter is labeled as cases created and verified, excluding analyst status updates. Evaluation renders actual published language, end-to-end workflow, and fraud-model reports, including limitations, language slices, baseline comparisons, and rejected-model promotion.
- Demo reset is a separately labeled destructive control with an explicit warning dialog. It calls `DELETE /api/workspace`; it never clears another visitor's workspace.

## Safety and accessibility

All dynamic response fields are escaped before HTML rendering. Requests use same-origin credentials; mutations carry the server-issued CSRF token. There is no client-side secret, local-storage transcript, arbitrary URL rendering, or permission claim based on the model response. Backend authorization remains the authority.

The UI provides a skip link, named controls, visible focus outlines, native select/dialog semantics, a chat log, loading and error states, explicit retry controls, reduced-motion support, and keyboard send (`Enter`; `Shift+Enter` inserts a line). It includes responsive navigation and preserves readable currency codes. No full WCAG audit or screen-reader certification is claimed.

## Browser verification, October 2, 2026

Verified against the local FastAPI app at `127.0.0.1:8096` with CUA-controlled Chrome:

1. Spanish customer login, scoped transaction selection, sourced status explanation, dispute proposal, explicit confirmation, and verified case receipt.
2. Case persistence after view/session switching; analyst closed the Spanish case and observed the persisted result.
3. Portuguese customer login, `Já saiu?` clarification, explicit pending transaction selection, correct USD status response, dispute confirmation and verified receipt.
4. Portuguese analyst handoff with localized allegations/open questions and `needs_information` persisted/read back.
5. Workspace analytics reflected the executed flows. Evaluation displayed backend report values, rather than fabricated UI metrics.
6. Customer layout at 390×844 and analyst layout at 320×780: document/body width matched viewport width. Viewport overrides were reset after inspection.
7. Final Chrome error/warning log was empty. Static JavaScript parses with `node --check src/factored_banking/static/app.js`.

Real fixture-only screenshots are local QA artifacts under `artifacts/ui-qa/` (ignored by Git). The Spanish case created before localization retained its original stored English summary; the subsequent Portuguese case demonstrated the localized payload. Backend contract/security tests cover failure and permission cases; browser QA is not a substitute for those tests. Safari, formal assistive-technology testing, and hosted network QA are not established by this local check.

## Documentation used

- [MDN Fetch](https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API/Using_Fetch): explicit status checking, credential and error handling.
- [MDN dialog](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/dialog): modal focus and native dismissal.
- [MDN log role](https://developer.mozilla.org/en-US/docs/Web/Accessibility/ARIA/Reference/Roles/log_role): incremental conversational content.
- Google Fonts source distributions: [DM Sans](https://github.com/google/fonts/tree/main/ofl/dmsans), [Manrope](https://github.com/google/fonts/tree/main/ofl/manrope). License texts accompany the font binaries in `static/fonts`.

## Hosted release verification — prior release

The release owner exercised the public HTTPS customer and analyst interfaces in both languages, including server cancellation, explicit confirmation, verified receipts, and saved analyst outcomes. A Portuguese short-follow-up misroute was fixed in PR #2 and rechecked in the browser on application commit `4692ded`. [Browser receipt](evidence/deployed-browser-checks.json) distinguishes the original complete walkthrough from the final correction check and records screenshot hashes. The public API was independently checked against the latest release; static files match local assets byte-for-byte.

## Handoff/provider extension verification

Verified on October 2 against `http://localhost:8096`, using an isolated Chrome workspace and authored fixture messages:

- Spanish and Portuguese: specific report preview → explicit confirmation → analyst asks a specific question → customer replies with the keyboard → analyst closes review. Green success notices followed verified mutation receipts. A test email was redacted in the Spanish report before confirmation.
- Refresh and persona switching retained exactly four real chronological events (creation, analyst question, customer reply, closure), with their actual actor, message and timestamp. Server read-back confirmed `history_complete: true`, `reviewed_closed` and no pending question. The static intake questions are explicitly labeled as questions present when the case was created.
- Required question validation blocked an empty analyst request. At 390×844 customer and 320×780 analyst widths, document and body width matched the viewport. The Portuguese reply was sent by Tab then Enter; in-flight fields were disabled.
- A temporary browser offline override forced an analyst mutation to fail. Three explicit attempts exhausted the retry allowance, removed the retry button and left the action form locked without a success claim. Restoring connectivity and reading the case back showed the original four events and no question; absent event evidence was not treated as a successful write. Network and viewport overrides were reset afterward.
- `node --check` passes. Isolated Node VM checks in both languages covered configured-not-probed vs. actually-used metadata, missing-key/deferred fallback, escaping hostile provider/model strings, and binding a reply operation to the displayed question ID even if case context subsequently changes. The ordinary browser flow showed actual local/deterministic metadata with external inference disabled. No paid or live external-provider inference was performed, so this is not provider availability or language-quality proof.

Fixture screenshots, case read-back JSON and hashes are saved locally under the ignored `artifacts/ui-completion/` directory, with `browser-checks.json` as the receipt. Normal-flow browser warning/error logs were empty before intentionally inducing network errors. Hosted extension QA, Safari and formal screen-reader testing remain separate gates.

Native form validation follows [MDN reportValidity](https://developer.mozilla.org/en-US/docs/Web/API/HTMLFormElement/reportValidity). Requests retain abort-controller timeouts with explicit cleanup, consistent with [MDN AbortSignal guidance](https://developer.mozilla.org/en-US/docs/Web/API/AbortSignal/timeout_static).


## Hosted v1.1 verification

The [public browser receipt](evidence/deployed-v1.1-browser-checks.json) records actual ES/PT case creation, analyst questions, customer replies, closure and reload at the stated workflow commit. Both closed cases retain four events with no further review form; no browser warnings/errors were observed. The later configuration-label correction and its public check are identified separately. No external model inference or organizer data was used.
