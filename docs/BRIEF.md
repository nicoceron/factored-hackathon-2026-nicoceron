# What they want

PDFs reviewed September 27 and October 2, 2026; user-supplied event-page requirements incorporated October 2. The task is to demonstrate a useful, safe, measured banking customer-service system. Choose a focused problem and complete it end to end. Depth matters more than adding workflows.

## Required behavior

| Requirement | What we should show | Source |
| --- | --- | --- |
| Data-backed problem selection | Reproducible demand and quality analysis supporting the workflow | Problem statement pp. 2–3 |
| Normal resolution | Authorized account/payment answer or permitted sandbox action with evidence | Problem statement p. 3 |
| Ambiguity or unsupported request | Clarification, abstention, or safe fallback | Problem statement p. 3 |
| Human-required case | Structured handoff with request, verified facts, actions, evidence, and open questions | Problem statement p. 3 |
| Spanish and Portuguese | Multi-turn examples and measured results in each language | Problem statement p. 3; kickoff p. 10 |
| Grounded responses | Amounts, statuses, and policy claims trace to permitted records/sources | Problem statement p. 3 |
| Permissions outside prompts | Authentication, record isolation, action rules, and confirmation enforced in code | Problem statement pp. 3, 5 |
| Data engineering | Repeatable preparation, contracts, quality checks, lineage, update/freshness policy | Problem statement pp. 3–4 |
| AI/ML rigor | At least one learned component evaluated against a suitable baseline | Problem statement pp. 3–4 |
| Held-out evaluation | Same workload for baseline and proposed system, valid labels, leakage controls | Problem statement pp. 3–6 |
| Failure handling | Bad/missing data, expired sessions, unauthorized access, injection, tool failures, multilingual ambiguity | Problem statement pp. 3–4 |
| Operational thinking | Traces, bounded retries, fallback, monitoring, capacity, retention, reproducible setup | Problem statement p. 4 |

The organizing sequence is **understand → decide → act → verify → escalate**. The important distinction is between a model saying something happened and the service verifying it happened.

## What is optional

The technical brief does not require training a new model, multiple agents, a particular tool count, streaming, forecasting, or a dashboard. A pretrained model or retrieval component can satisfy the learned-component requirement if it is evaluated properly. Batch processing is acceptable when it fits the data and freshness needs. Sandbox/mock bank tools are explicitly acceptable with documented contracts and limitations. A trusted test session is acceptable; a typed customer ID alone is not authentication.

No live lending decisions or money movement are required or authorized by the challenge. For any eligibility work, the policy must come from approved rules or an explicitly synthetic policy service, never from invented conversational-model rules.

## Submission and timing

- Closing date: **October 5, 2026**. Kickoff p. 6 and the [official FAQ](https://www.factored.ai/careers/ai-data-hackathon) agree. Neither inspected source specifies the cutoff hour/timezone.
- Kickoff p. 18 asks for a **public GitHub repo** named `factored-hackathon-2026-[team-name]`, a **deployed-tool link**, **4–6 slides**, and a **mandatory short video pitch** showing the working solution and architecture decisions.
- The slide says to submit those materials to `hackathon.admin@factored.ai`. This documents the submission route; nothing has been sent.
- The user-supplied current event page specifies a video pitch of **no longer than three minutes**. The final artifact must also satisfy that limit.
- Kickoff p. 6 lists finalists October 15 and the award ceremony October 16.
- No numerical scoring weights were provided in the inspected brief. Do not invent a percentage rubric.

The technical brief says this is a prototype with honest remaining deployment work; that does not erase the kickoff's requirement for a deployed demo link. Plan a hosted sandbox demonstration. No particular cloud provider is mandated. Obtain an explicit organizer exception if planning a local-only submission.

The September 27 website snapshot contained mixed wording, including a “Submissions Closed” button label and generic fraud-related marketing. Its FAQ still says October 5. Use the detailed participant brief for scope and confirm the cutoff in organizer announcements.

## What the pasted Slack conversation establishes

These are user-supplied excerpts, not a fresh authenticated reading of Slack. “Today” cannot be assigned an independent timestamp.

| Topic | Evidence level | Consequence |
| --- | --- | --- |
| Costs/free tier | Organizer André R says participants may incur costs and are not restricted to free tiers | Paid hosting is allowed; this is not a requirement to spend or permission to use any particular account |
| Cloud deployment optional? | A participant asks; no organizer answer shown | Keep the deployed-link deliverable from kickoff p. 18 |
| Transcript/metadata mismatch | A participant reports it; Antonio suggests reading docs and justifying the impact | Audit the data; this is not approval to relabel transcripts or proof of another transcript dataset |
| Controlled synthetic dispute conversations | A participant asks; no explicit approval shown | Clearly separate team fixtures from supplied evidence and clarify evaluation/data-use rules |
| `transaction_date > process_date` | Participant observation; no explanation provided | Measure calendar-date anomalies; do not assume timezone or silently shift dates |
| Campaign monetary units | Participant question; dictionary does not specify currency for `send_cost`/`conversion_value` | Do not assume USD; exclude unsupported currency arithmetic |
| Production call volume | Participant asks what the sample represents | No demonstrated production-scale multiplier or ROI estimate |
| Customer IDs across tables | Participant reports trouble joining | Measure exact FK coverage and customer consistency before linking records |
| Kaggle, machine GitHub account, registration email | Questions without shown answers | Treat as unresolved; do not infer policy |

The pasted AWS example uses PowerShell. On macOS, AWS CLI works directly from zsh/bash; installing PowerShell is unnecessary. The starter uses the official AWS CLI and an isolated participant profile.

## Dataset context from the supplied documentation

Version 1.0.0 describes 13 tables and approximately 19 million records across Mexico, Colombia, and Argentina, June 2023–June 2026. It explicitly calls the data synthetic. Text is Spanish with regional variations. Currency fields include MXN, COP, ARS, and USD. About 2% duplicates and 5% nullable-field missingness, late arrivals, schema changes, and some orphan references are described as intentional challenges. These are documentation claims; measured findings belong in DATA_FINDINGS.md.

Portuguese must be separately tested; the country/accent fields do not demonstrate Portuguese coverage. The summary's broad fraud/marketing/churn use-case suggestions do not replace the customer-service scope in the problem statement.

## Source register

The original PDFs remain on the participant's machine, outside version control.

| Document | Relevant pages |
| --- | --- |
| `Datathon_2026_Kickoff.pdf` | 6 timeline; 10–15 system, evaluation, and operations; 18 submission; 19 tool freedom; 20 evaluation areas |
| `Factored AI & Data Hackathon 2026 (1).pdf` | 2–3 scope; 3–4 technical behavior; 5 data/execution boundaries; 5–6 evaluation definitions |
| `LATAM_Bank_Complete_Data_Dictionary (2).pdf` | 2 participant access (contains credentials; never publish); 4–14 table definitions; 15–16 joins; 18 caveats |
| `LATAM_Bank_Dataset_Summary (1).pdf` | 2 provenance and quality; 3 table sizes; 5 language/currency caveats |
