# Claro interface

The interface is a responsive ES/PT customer and analyst workspace served by FastAPI from `src/factored_banking/static`. It uses native ES modules, Fetch, semantic HTML, CSS Grid, native dialogs, and local OFL-licensed DM Sans/Manrope font subsets. No browser package install, frontend build service, third-party runtime request, or paid API is required.

## Working flows

- Public demo personas create a server session for team-authored fixtures. The interface explicitly distinguishes the historical sandbox from real bank authentication. Persona changes preserve the browser's isolated workspace, allowing an analyst to review the customer's test case.
- The customer selects an authorized transaction, asks questions in Spanish or Portuguese, and sees currency-preserving amounts, snapshot dates, and expandable evidence. No organizer customer data is embedded in frontend assets.
- Multi-turn clarification uses the server context. Restored sessions show the current transaction context. Dismissing a proposal, removing a selection, or starting a new conversation calls the server reset endpoint, which invalidates pending proposals while preserving cases.
- A case proposal requires an explicit native confirmation dialog. The browser retains the same idempotency key when a confirmation request fails and is retried. A proposal is shown as canceled only after server cancellation succeeds; failure leaves it available for a retry. A green receipt requires the server's explicit verified flag; an unverified receipt is labeled accordingly.
- Customer cases and the analyst queue fetch persisted records. Analyst results are restricted to `reviewed_closed` or `needs_information`; neither grants a refund nor determines fraud.
- Operations uses workspace-scoped request, state, case and latency aggregates. Evaluation renders actual published language, end-to-end workflow, and fraud-model reports, including limitations, language slices, baseline comparisons, and rejected-model promotion.
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
