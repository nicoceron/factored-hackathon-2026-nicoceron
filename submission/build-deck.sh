#!/usr/bin/env bash
set -euo pipefail
TASK_REPO=$(cd "$(dirname "$0")/.." && pwd)
TASK_RUNTIME="${CLARO_RUNTIME_ROOT:-$HOME/.cache/codex-runtimes/codex-primary-runtime/dependencies}"
export CLARO_FONT_DIR="$TASK_RUNTIME/native/libreoffice-headless/libreoffice/LibreOfficeDev.app/Contents/Resources/fonts/truetype"
export CLARO_REPO="$TASK_REPO"
export CLARO_RUNTIME_PYTHON="$TASK_RUNTIME/python/bin/python3"
export RUNTIME_NODE_MODULES="$TASK_RUNTIME/node/node_modules"
export RUNTIME_NODE="$TASK_RUNTIME/node/bin/node"
export RUNTIME_PYTHON="$TASK_RUNTIME/python/bin/python3"
export CLARO_PRESENTATIONS_SKILL="${CLARO_PRESENTATIONS_SKILL:-$HOME/.codex/plugins/cache/openai-primary-runtime/presentations/26.909.12148/skills/presentations}"
mkdir -p "$TASK_REPO/.local/deck-build" "$TASK_REPO/.local/deck-finalized"
ln -sfn "$TASK_RUNTIME/node/node_modules" "$TASK_REPO/.local/deck-build/node_modules"
cp "$TASK_REPO/submission/build-deck.mjs" "$TASK_REPO/.local/deck-build/build-deck.mjs"
"$TASK_RUNTIME/node/bin/node" "$TASK_REPO/.local/deck-build/build-deck.mjs"
chmod 644 "$TASK_REPO/submission/Claro-Hackathon-2026.pptx"
"$TASK_RUNTIME/bin/override/soffice" -env:UserInstallation="file://$TASK_REPO/.local/deck-lo-profile" --headless --convert-to pdf --outdir "$TASK_REPO/submission" "$TASK_REPO/submission/Claro-Hackathon-2026.pptx"

"$TASK_RUNTIME/python/bin/python3" "$TASK_REPO/submission/verify-deck.py"
