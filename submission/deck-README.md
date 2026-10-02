# Six-slide presentation

`Claro-Hackathon-2026.pptx` is editable. Titles, body text, architecture boxes/connectors, and numerical charts are native slide objects. Chart workbooks are embedded. The PDF is exported from that finalized PPTX, not assembled from screenshots.

The deck contains exactly six slides: scope and data evidence; verified customer workflow; architecture and security; reproducible data and the rejected fraud candidates; language/component and workflow evidence; deployment and integration trade-offs. Speaker notes name repository evidence and explain limitations. Source screenshots show the actual local app using team-authored synthetic fixtures. No organizer record or private material appears in them.

## Rebuild

```bash
./submission/build-deck.sh
```

This uses the installed Codex runtime's Node.js, `@oai/artifact-tool`, bundled Noto Sans font files, presentation validators, and LibreOffice PDF converter. It does not install dependencies or call a paid service. Set `CLARO_RUNTIME_ROOT` and `CLARO_PRESENTATIONS_SKILL` if their installation locations differ. The builder is reproducible from committed composition, report JSON and screenshot inputs, but timestamps/internal package identifiers mean output files are not promised byte-identical.

`build-deck.mjs` loads measured aggregate results from `docs/evidence/ml-evaluation.json`, `language-evaluation.json`, `system-evaluation-v2.json`, `system-challenge-regression-v2.json` and `service-segment-evaluation.json`. Historical challenge evidence stays separate. The workflow chart is explicitly a regression replay. Six status/currency strata repeat 140 unique authored utterances rather than providing 840 independent labels. These are authorized service groups, not demographic fairness evidence. Labels have no independent human language review and the prospective 70-case provider challenge remains unscored. No state-of-the-art or real-customer accuracy claim is made. If current receipts are absent, the builder visibly labels historical results or pending replay; never publish that fallback as current evidence.

The v2 screenshots show the real local application's specific redacted report and persisted analyst/customer case history, with external providers disabled. Architecture and trade-off slides distinguish optional Jev/DeepSeek adapters tested with mocked transports from unverified live inference. No external-provider performance or invoice-spend result is invented. The release URL still refers to the exact commit in `deployment.json`; local screenshots are not deployment proof.

`deployment.json` controls the last slide. It displays a verified URL only after the release owner provides live verification. While `verified` is false, the slide visibly says verification is pending. Rebuild after changing that receipt. A deployment must not be inferred from a planned hostname.

Generated candidates, per-slide PNG/layout exports, font/package/geometry/chart validation receipts and LibreOffice temporary profiles stay in ignored `.local/deck-build/` and `.local/deck-finalized/`. The finalizer checks six slides, editable native charts on slides4–5, embedded chart workbooks, theme/font policy, package relationships, slide geometry and re-import. Final PDF page renders are visually checked in addition to these structural gates.

The chosen Noto Sans font is available in both rendering paths. The initial system-font choice was rejected during visual QA because the bundled headless LibreOffice substituted a serif font; the delivered PDF contains embedded Noto Sans regular/bold subsets.

The builder regenerates `deck-manifest.json` with structural checks and exact input/output hashes. It resets visual review to pending on every build. After viewing all six final PDF renders, run the same runtime Python with `submission/verify-deck.py --visual-review-complete` to associate the review with the exact output hashes. The receipt includes PDF text counts and embedded fonts; it does not claim a native Microsoft PowerPoint opening.
