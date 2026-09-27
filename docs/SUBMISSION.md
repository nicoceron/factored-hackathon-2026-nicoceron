# Submission checklist

Source: kickoff p. 18. Closing date October 5, 2026; cutoff hour/timezone still needs organizer confirmation. These are preparation notes, not a sent submission.

## Required materials

- [ ] Public repository named `factored-hackathon-2026-[team-name]` (currently private during setup).
- [ ] Working deployed-demo URL with reviewer access instructions and clearly marked sandbox behavior.
- [ ] Presentation of 4–6 slides.
- [ ] Short mandatory video demonstrating the working solution and core architectural decisions.
- [ ] Submit the materials to `hackathon.admin@factored.ai` before the confirmed deadline.

## Product and evidence checks

- [ ] One workflow justified by organizer-data findings.
- [ ] Spanish and Portuguese normal, ambiguous, and human-required cases.
- [ ] Trusted session, expiry, cross-customer denial, policy/confirmation enforcement.
- [ ] Read-back proof for every claimed write/action; idempotent retries.
- [ ] Useful structured handoff without an unfiltered transcript dump.
- [ ] Repeatable preparation, versioned contracts, manifests, freshness/update policy.
- [ ] Learned component compared with baseline on identical held-out cases.
- [ ] Report case counts, label quality, leakage prevention, failures, cost, latency, and language slices.
- [ ] Record limitations: synthetic inputs, missing content/joins, language gaps, sandbox tools, capacity, and remaining deployment work.
- [ ] Clean-clone setup works; CI passes; deployed UI/API and state changes verified live.
- [ ] No credentials, organizer PDFs, restricted records, or raw customer/transcript dumps in Git history or image.

## Suggested six-slide story

1. **Problem and users:** data-supported service need, chosen scope, intended outcome.
2. **Data:** actual coverage, important quality defects, valid labels, preparation and joins.
3. **System:** language component, tool/permission boundaries, source grounding, verification.
4. **Demonstration:** normal, ambiguity, escalation; Spanish and Portuguese.
5. **Results:** baseline versus proposed system, denominators, unsafe outcomes, latency/cost, limitations.
6. **Operation:** hosted architecture, observability, failures, retention, remaining production work.

## Local submission-message outline

Subject: Factored AI & Data Hackathon 2026 — [confirmed team name]

- Team members / registered identities: pending
- Public GitHub repository: pending final visibility/review
- Deployed demo and reviewer access: pending
- Slides: pending
- Video: pending
- Short workflow summary and known limitations: pending

Do not put AWS credentials or unrestricted customer access in the submission message. This outline is stored locally in the repo; no email or Slack message has been composed in an external app or sent.

## Questions to resolve from official announcements or mentors

1. Exact October 5 cutoff time/timezone and whether the email route is still current.
2. Any exception to the deployed-link/public-repo requirements, and the meaning of the public-repository asterisk on kickoff p. 18.
3. Video duration/file/link constraints and team/member registration linkage.
4. Whether there are updated policy sources, repaired record mappings, or more representative transcripts; rules for publishing/downstream processing synthetic data and for team-generated evaluation conversations.

No answer to these questions has been inferred from unanswered participant messages.
