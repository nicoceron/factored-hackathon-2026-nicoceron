"""Live sandbox checks; persist only allowlisted aggregate evidence."""

import argparse
import hashlib
import json
import re
import subprocess
import uuid
from datetime import UTC, datetime
from http.cookiejar import CookieJar
from http.cookies import SimpleCookie
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import HTTPCookieProcessor, Request, build_opener

from factored_banking.web_assets import render_index

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("url", help="Public HTTPS sandbox URL with external providers disabled")
parser.add_argument(
    "--commit", required=True, help="Commit visibly confirmed by the deployment host"
)
parser.add_argument("--output", type=Path, default=Path("artifacts/deployed-api-checks.json"))
args = parser.parse_args()
if not args.url.startswith("https://"):
    parser.error("Public verification requires HTTPS")
BASE = args.url.rstrip("/")
ROOT = Path(__file__).resolve().parents[1]
started = datetime.now(UTC).isoformat()


def client():
    return build_opener(HTTPCookieProcessor(CookieJar()))


def call(browser, path, body=None, method=None, csrf=None, origin=None, extra_headers=None):
    headers = {"Content-Type": "application/json"}
    headers.update(extra_headers or {})
    if csrf:
        headers["X-CSRF-Token"] = csrf
    if origin:
        headers["Origin"] = origin
    req = Request(
        BASE + path,
        data=json.dumps(body).encode() if body is not None else None,
        headers=headers,
        method=method,
    )
    try:
        result = browser.open(req, timeout=90)
    except HTTPError as error:
        result = error
    with result:
        data = result.read()
        return result.status, data, result.headers


def decoded(result):
    return json.loads(result[1])


def canonical_hash(data):
    return hashlib.sha256(
        json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    ).hexdigest()


public = client()
checks = {}
static_dir = ROOT / "src/factored_banking/static"
expected_index = render_index(static_dir).encode()
checks["health_http_200"] = call(public, "/healthz")[0] == 200
ready = call(public, "/readyz")
checks["readiness_http_200_and_ready"] = ready[0] == 200 and decoded(ready).get("ready") is True
checks["unauthenticated_transactions_http_401"] = call(public, "/api/transactions")[0] == 401
checks["foreign_origin_session_http_403"] = (
    call(
        public,
        "/api/session",
        {"persona": "customer_es", "language": "es"},
        origin="https://untrusted.example",
    )[0]
    == 403
)

assets = []
for path in sorted((ROOT / "src/factored_banking/static").rglob("*")):
    if not path.is_file():
        continue
    route = "/static/" + path.relative_to(ROOT / "src/factored_banking/static").as_posix()
    response = call(public, route)
    expected_bytes = expected_index if path.name == "index.html" else path.read_bytes()
    expected = hashlib.sha256(expected_bytes).hexdigest()
    actual = hashlib.sha256(response[1]).hexdigest()
    assets.append(
        {
            "path": route,
            "http_200": response[0] == 200,
            "sha256_matches_local": expected == actual,
            "local_sha256": expected,
            "deployed_sha256": actual,
            "revalidates_before_reuse": response[2].get("Cache-Control") == "no-cache",
        }
    )
index = call(public, "/")
checks["index_http_200_and_sha256_matches_local"] = (
    index[0] == 200 and hashlib.sha256(index[1]).digest() == hashlib.sha256(expected_index).digest()
)
checks["all_static_assets_http_200_and_byte_identical"] = all(
    a["http_200"] and a["sha256_matches_local"] for a in assets
)
checks["all_unversioned_static_assets_revalidate"] = all(
    a["revalidates_before_reuse"] for a in assets
)
etag = index[2].get("ETag", "")
conditional = call(public, "/", extra_headers={"If-None-Match": etag})
raw_entry = call(public, "/static/index.html")
checks["html_entrypoints_versioned_and_revalidate_with_content_etag"] = (
    index[2].get("Cache-Control") == "no-cache"
    and etag.removeprefix("W/") == '"' + hashlib.sha256(expected_index).hexdigest() + '"'
    and conditional[0] == 304
    and conditional[2].get("Cache-Control") == "no-cache"
    and raw_entry[1] == expected_index
    and raw_entry[2].get("ETag") == etag
)
versioned_urls = re.findall(
    r'(?:src|href)="(/static/[^"?]+\?v=[a-f0-9]{64})"', expected_index.decode()
)
versioned_assets = []
for route in versioned_urls:
    response = call(public, route)
    filename, version = route.removeprefix("/static/").split("?v=")
    expected_bytes = (static_dir / filename).read_bytes()
    versioned_assets.append(
        {
            "path": route,
            "current_version_sha256": hashlib.sha256(expected_bytes).hexdigest() == version,
            "deployed_bytes_match": response[0] == 200 and response[1] == expected_bytes,
        }
    )
checks["css_js_and_icon_use_current_content_versions"] = len(versioned_assets) == 3 and all(
    r["current_version_sha256"] and r["deployed_bytes_match"] for r in versioned_assets
)

remote_reports_response = call(public, "/api/evaluation")
remote_evaluation = decoded(remote_reports_response)
remote_reports = remote_evaluation.get("reports", {})
remote_report_files = remote_evaluation.get("report_files", {})
current_regressions = {
    "system-evaluation": "chat-system-regression.json",
    "system-challenge-regression": "chat-challenge-regression.json",
    "service-segment-evaluation": "chat-service-segment-regression.json",
}
reports = []
for name in (
    "language-evaluation",
    "fraud-evaluation",
    "system-evaluation",
    "system-challenge-evaluation",
    "system-challenge-regression",
    "service-segment-evaluation",
):
    resource = ROOT / "src/factored_banking/resources" / f"{name}.json"
    updated = resource.with_name(f"{name}-v2.json")
    selected = updated if updated.exists() else resource
    current_name = current_regressions.get(name)
    current = resource.with_name(current_name) if current_name else None
    if current is not None and current.exists():
        selected = current
    local = json.loads(selected.read_text())
    remote = remote_reports.get(name)
    expected = canonical_hash(local)
    actual = canonical_hash(remote)
    reports.append(
        {
            "name": name,
            "present": remote is not None,
            "expected_file": selected.name,
            "declared_file_matches_local": remote_report_files.get(name) == selected.name,
            "canonical_json_sha256_matches_local": expected == actual,
            "local_sha256": expected,
            "deployed_sha256": actual,
        }
    )
checks["evaluation_http_200_and_all_six_reports_equal"] = remote_reports_response[0] == 200 and all(
    r["present"] and r["declared_file_matches_local"] and r["canonical_json_sha256_matches_local"]
    for r in reports
)

browsers = [client(), client()]
tokens = [None, None]
cookie_checks = {}
try:
    response = call(
        browsers[0], "/api/session", {"persona": "customer_es", "language": "es"}, origin=BASE
    )
    checks["same_origin_session_http_200"] = response[0] == 200
    tokens[0] = decoded(response)["csrf_token"]
    assert decoded(response)["ai"]["external_enabled"] is False, (
        "This free release check requires external AI disabled"
    )
    cookies = SimpleCookie()
    for line in response[2].get_all("Set-Cookie", []):
        cookies.load(line)
    for name in ("claro_session", "claro_workspace"):
        cookie = cookies.get(name)
        cookie_checks[name] = {
            "present": cookie is not None,
            "secure": bool(cookie and cookie["secure"]),
            "http_only": bool(cookie and cookie["httponly"]),
            "same_site_strict": bool(cookie and cookie["samesite"].lower() == "strict"),
        }
    checks["both_cookies_secure_httponly_samesite_strict"] = all(
        all(flags.values()) for flags in cookie_checks.values()
    )
    checks["missing_csrf_mutation_http_403"] = (
        call(browsers[0], "/api/conversation/reset", {}, origin=BASE)[0] == 403
    )
    checks["foreign_origin_authenticated_mutation_http_403"] = (
        call(
            browsers[0],
            "/api/conversation/reset",
            {},
            csrf=tokens[0],
            origin="https://untrusted.example",
        )[0]
        == 403
    )
    transactions = decoded(call(browsers[0], "/api/transactions"))["transactions"]
    proposal_response = call(
        browsers[0],
        "/api/chat",
        {
            "message": "No reconozco este cargo",
            "language": "es",
            "transaction_id": transactions[0]["id"],
            "idempotency_key": str(uuid.uuid4()),
        },
        csrf=tokens[0],
        origin=BASE,
    )
    proposal = decoded(proposal_response)
    checks["isolated_workspace_proposal_created"] = (
        proposal_response[0] == 200 and proposal["state"] == "awaiting_confirmation"
    )
    confirm_response = call(
        browsers[0],
        "/api/actions/confirm",
        {"proposal_id": proposal["proposal"]["id"], "idempotency_key": str(uuid.uuid4())},
        csrf=tokens[0],
        origin=BASE,
    )
    receipt = decoded(confirm_response)["receipt"]
    checks["isolated_workspace_case_verified"] = (
        confirm_response[0] == 200 and receipt["verified"] is True
    )
    case_id = receipt["case_id"]
    response = call(
        browsers[1], "/api/session", {"persona": "analyst", "language": "es"}, origin=BASE
    )
    tokens[1] = decoded(response)["csrf_token"]
    checks["separate_browser_analyst_sees_empty_case_list"] = (
        decoded(call(browsers[1], "/api/cases"))["cases"] == []
    )
    checks["separate_browser_analyst_foreign_case_http_404"] = (
        call(browsers[1], "/api/cases/" + case_id)[0] == 404
    )
    checks["separate_browser_analyst_foreign_resolution_http_404"] = (
        call(
            browsers[1],
            "/api/cases/" + case_id + "/resolve",
            {"resolution": "reviewed_closed", "idempotency_key": str(uuid.uuid4())},
            csrf=tokens[1],
            origin=BASE,
        )[0]
        == 404
    )
    response = call(
        browsers[0], "/api/session", {"persona": "analyst", "language": "es"}, origin=BASE
    )
    tokens[0] = decoded(response)["csrf_token"]
    cases = decoded(call(browsers[0], "/api/cases"))["cases"]
    checks["same_browser_analyst_sees_exact_own_case"] = (
        len(cases) == 1 and cases[0]["id"] == case_id
    )
    checks["foreign_attempt_did_not_change_case_status"] = cases[0]["status"] == "open"
finally:
    for index, browser in enumerate(browsers):
        if tokens[index]:
            erased = call(
                browser, "/api/workspace", method="DELETE", csrf=tokens[index], origin=BASE
            )
            checks[f"audit_workspace_{index + 1}_erased"] = erased[0] == 200
            checks[f"audit_session_{index + 1}_invalid_after_erasure"] = (
                call(browser, "/api/session")[0] == 401
            )

smoke = json.loads(
    subprocess.check_output(
        ["uv", "run", "--locked", "python", str(ROOT / "scripts/smoke.py"), BASE],
        cwd=ROOT,
        text=True,
    )
)
checks["bilingual_smoke_passed"] = (
    smoke["passed"] is True
    and smoke["languages"] == ["es", "pt"]
    and smoke["verified_cases"] == 2
    and smoke["duplicate_writes"] == 0
    and smoke["analyst_resolution"]
    and smoke["workspace_erased"]
)
report = {
    "version": "deployed-api-checks-chat-v3",
    "url": BASE,
    "started_at_utc": started,
    "completed_at_utc": datetime.now(UTC).isoformat(),
    "local_release_commit": subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip(),
    "deployment_commit_reported_by_release_owner": args.commit,
    "commit_evidence_scope": "Release owner identifies deployed commit; this probe independently "
    "verifies static bytes and report contents, not a server commit-attestation endpoint.",
    "all_checks_passed": all(checks.values()),
    "checks": checks,
    "cookie_flags": cookie_checks,
    "static_assets": assets,
    "versioned_assets": versioned_assets,
    "html_validator": {
        "public_etag": etag,
        "application_etag_is_strong": True,
        "public_proxy_may_weaken_etag": etag.startswith("W/"),
        "validation": "Both entries match bytes; content digest and conditional 304 verified.",
    },
    "evaluation_reports": reports,
    "report_hash_method": "SHA256 of parsed JSON, sorted keys, compact separators, "
    "ensure_ascii=False; API serialization whitespace is not compared.",
    "bilingual_smoke": smoke,
    "data_scope": "Only team-authored public sandbox fixtures used. No cookie values, CSRF tokens, "
    "session/workspace/case identifiers or customer records persisted in this receipt.",
    "limits": [
        "Observed HTTPS checks at the recorded time; no uptime or production security guarantee.",
        "Test workspaces were erased after the probes; no restart durability is established.",
        "Browser rendering and interaction QA is separate.",
    ],
}
output = args.output
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
print(
    json.dumps(
        {
            "saved": str(output),
            "passed": report["all_checks_passed"],
            "checks_count": len(checks),
            "failed_checks": [name for name, passed in checks.items() if not passed],
            "static_assets": len(assets),
            "reports": len(reports),
        }
    )
)

raise SystemExit(0 if report["all_checks_passed"] else 1)
