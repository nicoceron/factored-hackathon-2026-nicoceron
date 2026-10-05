"""Record structural checks and hashes for the six-slide submission deck."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from zipfile import ZipFile

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument(
    "--visual-review-complete",
    action="store_true",
    help="Use only after viewing all six renders of this exact PDF.",
)
args = parser.parse_args()
summary = json.loads((ROOT / ".local/deck-build/build-summary.json").read_text())
receipt = summary["receipt"]
inputs = [
    "submission/build-deck.mjs",
    "submission/build-deck.sh",
    "submission/demo-scenes.json",
    "submission/deployment.json",
    "submission/demo-assets/chat-confirm-es.jpg",
    "submission/demo-assets/chat-history-pt.jpg",
    "docs/evidence/ml-evaluation.json",
    "docs/evidence/language-evaluation.json",
    "docs/evidence/system-challenge-evaluation.json",
    "docs/evidence/system-challenge-regression.json",
    "docs/AI_PROVIDERS.md",
]
for current, historical in (
    ("docs/evidence/system-evaluation-v2.json", "docs/evidence/system-evaluation.json"),
    ("docs/evidence/system-challenge-regression-v2.json", None),
    ("docs/evidence/service-segment-evaluation.json", None),
    ("docs/evidence/chat-system-regression.json", None),
    ("docs/evidence/chat-challenge-regression.json", None),
    ("docs/evidence/chat-service-segment-regression.json", None),
):
    if (ROOT / current).exists():
        inputs.append(current)
    elif historical:
        inputs.append(historical)
outputs = ["submission/Claro-Hackathon-2026.pptx", "submission/Claro-Hackathon-2026.pdf"]
hashes = {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in inputs + outputs}
assert hashes[outputs[0]] == receipt["finalSha256"], "PPTX differs from finalized receipt"
assert receipt["packageIntegrity"]["findingCount"] == 0
assert receipt["presentationLayout"]["findingCount"] == 0
assert receipt["firstPartyImport"]["passed"]
assert receipt["nativeChartValidation"]["passed"]
reader = PdfReader(ROOT / outputs[1])
assert len(reader.pages) == 6
word_counts = [len(page.extract_text().split()) for page in reader.pages]
assert all(count > 20 for count in word_counts), "Unexpected empty/textless slide"
fonts = sorted(
    {
        str(font.get_object()["/BaseFont"]).split("+")[-1]
        for page in reader.pages
        for font in page["/Resources"]["/Font"].values()
    }
)
assert all("NotoSans" in font for font in fonts), f"Unexpected PDF font fallback: {fonts}"
with ZipFile(ROOT / outputs[0]) as archive:
    embedded_workbooks = [p for p in archive.namelist() if p.endswith(".xlsx")]
    assert len(embedded_workbooks) == 3
manifest = {
    "version": "claro-deck-chat-v3",
    "slide_count": 6,
    "native_chart_count": 3,
    "embedded_chart_workbook_count": len(embedded_workbooks),
    "editable_architecture_slide": 3,
    "pdf_word_counts_by_slide": word_counts,
    "pdf_embedded_fonts": fonts,
    "package_integrity_passed": True,
    "geometry_checks_passed": True,
    "artifact_tool_reimport_passed": True,
    "native_chart_checks_passed": True,
    "visual_review_completed_for_these_output_hashes": args.visual_review_complete,
    "visual_review_scope": (
        "Assistant inspected every final PDF page at 1280x720 for font fallback, clipping, "
        "overlaps, diagram direction, chart labels and caveats."
    )
    if args.visual_review_complete
    else "Pending. Render and inspect all six current PDF pages before marking complete.",
    "native_powerpoint_application_verified": False,
    "input_output_sha256": hashes,
    "asset_provenance": (
        "Actual CUA Chrome local Claro captures at http://127.0.0.1:8096 on "
        "2026-10-04 America/Bogota, team-authored fixtures and disabled providers. "
        "Declared image crops improve readability without editing screenshot pixels. "
        "The reviewer timeline retains a Spanish interface, Spanish report and "
        "Portuguese question/reply."
    ),
    "limitations": [
        "Screenshots illustrate the app; they do not prove deployed behavior.",
        "Deployment readiness evidence is separate from full browser workflow verification.",
        "Charts represent authored synthetic evaluation and retrospective synthetic fraud labels.",
    ],
}
(ROOT / "submission/deck-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
print(
    json.dumps(
        {
            "slides": 6,
            "pdf_word_counts": word_counts,
            "fonts": fonts,
            "visual_review_completed": args.visual_review_complete,
        }
    )
)
