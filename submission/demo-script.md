# Claro narrated demo

Actual screenshots of the running local sandbox; narrated with the macOS Samantha system voice.
No footage is represented as a continuous recording. UI content is from team-authored fixtures.

## 1. Banking help. With evidence.

Meet Claro, banking support in Spanish and Portuguese.
This is a working historical sandbox with team authored fixtures, not a connection to real bank accounts.
We complete one workflow: understand a transaction, report an unrecognized charge, and hand off with evidence.

## 2. Understand. Then clarify.

Here, the Portuguese customer asks whether a payment went through.
Claro asks which transaction, instead of guessing.
After a selection, it reports thirty eight dollars and fifty cents as pending, preserving the currency and historical date.
The answer comes from an authorized record tool, with source references.

## 3. The model can't act alone.

The customer says they do not recognize this charge.
Claro prepares a human review case, but nothing has been created yet.
Intent classification helps understand the request.
Deterministic service rules control permissions, required context, and which actions are allowed.

## 4. A real pause for confirmation.

A separate confirmation dialog names the sandbox action and its limits.
The service requires the valid session, the correct role, and a CSRF token.
Typing yes in the conversation cannot execute the case creation.

## 5. An action needs a verified receipt.

The confirmed case is now saved and read back from storage.
Only then does Claro show this verified reference.
Retries reuse an idempotency key, so a dropped response does not create another case.
A verification failure produces an error, never a success claim.

## 6. A useful handoff. A bounded decision.

In the same isolated workspace, an analyst receives the allegation, transaction facts, evidence, and open questions.
Risk is unavailable for these out of domain fixtures, rather than shown as a misleading zero.
The analyst can close the review or request more information.
Neither outcome grants a refund or proves fraud.

## 7. Small architecture. Explicit boundaries.

The application uses one FastAPI service, a local language classifier, and a transactional sandbox case store.
Offline data preparation and model evaluation stay outside requests.
The browser shows actual workspace activity and latency.
Zero model API spend does not mean zero infrastructure cost.

## 8. Measure the result. Publish the limits.

We compare rules, a trained TF-IDF classifier, and local Gemma on the same one hundred forty authored bilingual scenarios.
The selected classifier reaches an intent macro F one of eighty two point three percent.
The complete workflow has a separate evaluation with failures disclosed.
These tests have no independent human review and cannot establish production accuracy.

## 9. Ship the evidence. Keep human oversight.

The fraud experiment is equally explicit: its candidates did not pass the validation promotion gate.
We retain the baseline and never let a low score dismiss a customer's report.
Claro delivers a working bilingual workflow, traceable evidence, and a human handoff, with honest boundaries for what remains before real banking production.
