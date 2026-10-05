"""Render the static HTML template with asset-content versions at app creation."""

from hashlib import sha256
from pathlib import Path

ASSETS = ("app.css", "app.js", "favicon.svg")


def render_index(static_dir: Path) -> str:
    """Keep template bytes unchanged except for the three local asset URLs."""
    html = (static_dir / "index.html").read_text(encoding="utf-8")
    for name in ASSETS:
        version = sha256((static_dir / name).read_bytes()).hexdigest()
        html = html.replace(f'"/static/{name}"', f'"/static/{name}?v={version}"')
    return html
