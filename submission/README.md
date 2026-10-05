# Claro submission package

Team/repository identifier: `nicoceron`. The public application uses team-authored fixtures, synthetic policy and isolated test identities. It performs no real banking action.

The separate [conversational HTTPS receipt](../docs/evidence/chat-deployed-conversation-checks.json) passes 70/70 authored scenarios with verified cases and retries. It is distinct from the 26 HTTPS release checks and 22 observed browser checks; frozen evaluation workloads and independent native-language limitations remain unchanged.

- `Claro-Hackathon-2026.pdf`: six-slide presentation for reviewers.
- `Claro-Hackathon-2026.pptx`: editable presentation source.
- `claro-demo.mp4`: narrated demonstration, under three minutes, H.264/AAC with an English subtitle track.
- `claro-demo.en.srt`: separately accessible captions; `demo-script.md` contains the complete narration.
- `demo-manifest.json`: exact duration, output/source hashes, capture provenance and narration disclosure. The video uses actual local-app screenshots plus clearly labeled architecture/evaluation slides. It is not presented as a continuous screen recording, hosted proof, or evidence of live external-provider inference. The captured flows used local processing.
- `deployment.json`: separately records the verified public URL and commit when release checks finish.

The current package contains six editable, reviewed slides and a 170.92-second narrated, captioned nine-scene video. The chat is separately verified Live on Render Free at application commit `6a4cf24fcb105d1587475d71c35c0de6ca4043ea`, with 680 local tests, 26 public HTTPS checks and 22 observed returning-Chrome checks. The published v1.1 release assets remain historical. Open the app and start chatting in Spanish or Portuguese without selecting a persona, language or transaction. Clarify a transaction conversationally, report a charge and explicitly confirm the case. Open `/?review=1` in the same browser to ask a specific question or close the review; return to `/` for the customer's inline case follow-up. [The submission checklist](../docs/SUBMISSION.md) separates current hosted proof, original local captures and historical release assets. No password or organizer-data access is required. Each browser receives an isolated workspace. The free host can take about a minute to wake and may clear sessions/cases on restart.

## Capture scope and final hosted proof

The deck/video retain seven genuine local screenshots from port 8096 on October 5 UTC. [The original local browser receipt](../docs/evidence/chat-browser-checks.json) records their actual backend/static hashes. They precede SHA asset revalidation, F7 repeated-clarification report continuity, F8 reply/ack session-history recovery plus the validated client reply locale, M1 denial polarity, L1 ordinal choice, N1/N2 conversational choices, P1 decimal amount references, P2 rejected amounts, P3 currency constraints and P4 numeric case-reference history, Q1 currency symbols and Q2 rejected-choice task continuity. Their pixels, case references and source hashes remain unchanged. The final hosted application and packaged reports are verified separately, rather than relabeling those screenshots as later source.

[The final HTTPS receipt](../docs/evidence/chat-deployed-api-checks.json) verifies eight assets, three SHA-versioned resources, six reports and ES/PT reply/retry history. [The final browser receipt](../docs/evidence/chat-deployed-browser-checks.json) binds the exact Live commit and four supplemental public screenshots below. They show ordinary returning-Chrome entry, the full three-turn report with the exact native transaction, a redacted Spanish reply/ack restored for a saved Portuguese case, and all four persisted events. They belong to a different isolated hosted workspace from the local video captures. The restored-reply image repeats the same reply/reload contract using a fresh case after the animation settled; it is distinct from the main confirmation and complete four-event history case, as recorded in its capture row.

| Final hosted capture | Proof |
| --- | --- |
| [Immediate chat](demo-assets/chat-hosted-welcome.png) | Single composer and zero customer selectors |
| [Full confirmation](demo-assets/chat-hosted-confirm.png) | Exact attached record and preserved original allegation plus later details |
| [Restored reply](demo-assets/chat-hosted-reply-restored.png) | Redacted reply and verified acknowledgement after reload |
| [Persisted history](demo-assets/chat-hosted-history.png) | Four chronological case events |

The source-only non-root Docker receipt and exact-head CI are separate gates. Later packaging changes correct one verification-probe field in `scripts/smoke.py` and refresh evidence/media; the packaged application remains equivalent to the hosted commit. Free-host persistence, real mobile keyboards, Safari, formal accessibility, live providers and independent native-language quality remain outside the verified scope.

## Rebuilding the media

The shipped PDF, PPTX and MP4 can be opened with ordinary viewers; rebuilding is optional and separate from `make setup` for the app.

`build-deck.sh` uses the documented bundled Codex presentation runtime and skill renderer; override `CLARO_RUNTIME_ROOT` and `CLARO_PRESENTATIONS_SKILL` for another installation. `build-deck.mjs` contains the editable slide composition, charts and source notes.

`build-demo.py` requires Python with Pillow, FFmpeg/FFprobe, and the macOS `say` command with the Samantha system voice. `DEMO_FONT` can override the local font path. It renders the committed team-authored app captures and labeled diagram images; it uses no paid or remote service. `demo-scenes.json` controls narration and layout. Generated intermediates stay in ignored `artifacts/demo-build/`.

The materials are packaged for review only. The user explicitly instructed us never to submit. No organizer email, competition form, or upload is authorized by this package.
