# Claro submission package

Team/repository identifier: `nicoceron`. The public application uses team-authored fixtures, synthetic policy and isolated test identities. It performs no real banking action.

- `Claro-Hackathon-2026.pdf`: six-slide presentation for reviewers.
- `Claro-Hackathon-2026.pptx`: editable presentation source.
- `claro-demo.mp4`: narrated demonstration, under three minutes, H.264/AAC with an English subtitle track.
- `claro-demo.en.srt`: separately accessible captions; `demo-script.md` contains the complete narration.
- `demo-manifest.json`: exact duration, output/source hashes, capture provenance and narration disclosure. The video uses actual local-app screenshots plus clearly labeled architecture/evaluation slides. It is not presented as a continuous screen recording, hosted proof, or evidence of live external-provider inference. The captured flows used local processing.
- `deployment.json`: separately records the verified public URL and commit when release checks finish.

Open the public demo link in [the submission checklist](../docs/SUBMISSION.md). Select either customer persona, ask about a transaction, report a charge, and explicitly confirm a case. Switch to the analyst persona in the same browser to review that case and ask a specific question. Return to the customer persona to answer it, then verify the persisted history and close the review as the analyst. No password or organizer-data access is required. Each browser receives an isolated workspace. The free host can take about a minute to wake and may clear sessions/cases on restart.

## Rebuilding the media

The shipped PDF, PPTX and MP4 can be opened with ordinary viewers; rebuilding is optional and separate from `make setup` for the app.

`build-deck.sh` uses the documented bundled Codex presentation runtime and skill renderer; override `CLARO_RUNTIME_ROOT` and `CLARO_PRESENTATIONS_SKILL` for another installation. `build-deck.mjs` contains the editable slide composition, charts and source notes.

`build-demo.py` requires Python with Pillow, FFmpeg/FFprobe, and the macOS `say` command with the Samantha system voice. `DEMO_FONT` can override the local font path. It renders the committed team-authored app captures and labeled diagram images; it uses no paid or remote service. `demo-scenes.json` controls narration and layout. Generated intermediates stay in ignored `artifacts/demo-build/`.

The materials are packaged for review only. The user explicitly instructed us never to submit. No organizer email, competition form, or upload is authorized by this package.
