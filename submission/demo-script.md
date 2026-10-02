# Claro narrated demo

Actual screenshots of the running local sandbox; narrated with the macOS Samantha system voice.
No footage is represented as a continuous recording. Architecture and evaluation slides are labeled separately. UI content is from team-authored fixtures.

## 1. Banking help. With evidence.

Meet Claro, banking support in Spanish and Portuguese.
These screenshots come from actual local test runs with team authored fixtures.
The application understands transactions, prepares review cases, and completes a human follow up. It never connects to real bank accounts.

## 2. Understand. Then clarify.

The Portuguese customer asks whether a payment went through.
Claro asks which transaction before answering.
An authorized record tool returns thirty eight dollars and fifty cents as pending, preserving the currency, source reference, and historical date.

## 3. Your report. Your confirmation.

This Spanish report describes an unfamiliar charge after a phone call.
The preview preserves that context and redacts the test email.
A separate confirmation is required to create a case. Typing yes in chat cannot execute it.
No refund or card blocking is promised.

## 4. An action needs a verified receipt.

Every successful case creation needs a committed record and verified read back.
Retries keep the same idempotency key and stop after three attempts.
A verification failure never becomes a success claim.

## 5. Ask a question. Receive an answer.

The analyst asks whether the charge was noticed during or after the call.
The Portuguese customer sees that exact question and can answer inside the case.
A verified reply returns the case to the review queue.

## 6. History that survives refresh.

The analyst now sees the original report, the question, and the customer reply in order.
The review is closed, and all four events remain after refreshing and switching profiles.
The backend stores the history; the browser does not invent it.

## 7. AI explains. The service controls.

One FastAPI service owns sessions, scoped tools, and transactional case storage.
Jev routing and DeepSeek Flash wording are implemented behind bounded adapters.
Live inference still requires explicit authorization for metered use. These captures used local processing.
Provider status and fallback are disclosed. Only entered sandbox messages and minimized fixture context may leave; organizer data never does.

## 8. Measure outcomes. Publish the limits.

Language understanding and complete workflow outcomes are evaluated separately.
The repository preserves offline baselines, failure analysis, language slices, and service segments.
Authored scenarios and mocked provider tests do not prove real customer performance or live provider quality.

## 9. Keep evidence. Keep human oversight.

The fraud candidates did not pass the validation promotion gate. Risk remains unavailable for these out of domain fixtures.
A low score never dismisses the customer report.
Claro delivers a working bilingual follow up with explicit controls and measured limits, ready for review, with real banking production still outside this prototype.
