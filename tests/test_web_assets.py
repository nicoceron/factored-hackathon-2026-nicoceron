"""A returning browser gets current assets without clearing its cache."""

import os
from hashlib import sha256

import pytest
from fastapi.testclient import TestClient

from factored_banking import api
from factored_banking.web_assets import ASSETS, render_index


@pytest.fixture
def static_root(tmp_path, monkeypatch):
    static = tmp_path / "static"
    static.mkdir()
    static.joinpath("index.html").write_text(
        '<!doctype html><link rel="icon" href="/static/favicon.svg">'
        '<link rel="stylesheet" href="/static/app.css">'
        '<script type="module" src="/static/app.js"></script>',
        encoding="utf-8",
    )
    for name in ASSETS:
        static.joinpath(name).write_bytes(f"fixture-{name}".encode())
    monkeypatch.setattr(api, "ROOT", tmp_path)
    return tmp_path


def make_app(root, name="first"):
    return api.create_app(str(root / f"{name}.sqlite"), enable_external=False)


@pytest.mark.parametrize("entry", ["/", "/static/index.html"])
def test_both_entry_paths_render_content_versions_without_changing_template(static_root, entry):
    static = static_root / "static"
    original = (static / "index.html").read_bytes()
    with TestClient(make_app(static_root)) as client:
        response = client.get(entry)
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/html; charset=utf-8"
        assert response.headers["cache-control"] == "no-cache"
        assert response.headers["etag"] == f'"{sha256(response.content).hexdigest()}"'
        for name in ASSETS:
            version = sha256((static / name).read_bytes()).hexdigest()
            url = f"/static/{name}?v={version}"
            assert url in response.text
            asset = client.get(url)
            assert asset.status_code == 200
            assert asset.content == (static / name).read_bytes()
            assert asset.headers["cache-control"] == "no-cache"
        assert response.text == render_index(static)
    assert (static / "index.html").read_bytes() == original


@pytest.mark.parametrize("changed", ASSETS)
def test_new_app_changes_only_modified_asset_url_even_with_same_size_and_mtime(
    static_root, changed
):
    static = static_root / "static"
    with TestClient(make_app(static_root)) as first:
        previous = first.get("/")
        old_bytes = (static / changed).read_bytes()
        timestamps = (static / changed).stat()
        new_bytes = old_bytes[:-1] + b"X"
        assert len(new_bytes) == len(old_bytes) and new_bytes != old_bytes
        (static / changed).write_bytes(new_bytes)
        os.utime(static / changed, ns=(timestamps.st_atime_ns, timestamps.st_mtime_ns))
        # The app snapshots the entry HTML once; deployments construct a new app.
        assert first.get("/").content == previous.content
        with TestClient(make_app(static_root, "new-release")) as current:
            response = current.get("/", headers={"If-None-Match": previous.headers["etag"]})
            assert response.status_code == 200
            assert response.headers["etag"] != previous.headers["etag"]
            old_url = f"/static/{changed}?v={sha256(old_bytes).hexdigest()}"
            new_url = f"/static/{changed}?v={sha256(new_bytes).hexdigest()}"
            assert old_url in previous.text and old_url not in response.text
            assert new_url in response.text
            assert current.get(new_url).content == new_bytes
            for unchanged in set(ASSETS) - {changed}:
                url = (
                    f"/static/{unchanged}?v={sha256((static / unchanged).read_bytes()).hexdigest()}"
                )
                assert url in previous.text and url in response.text


@pytest.mark.parametrize("entry", ["/", "/static/index.html"])
@pytest.mark.parametrize("validator", ["exact", "weak-list", "wildcard"])
def test_html_conditional_get_and_head_keep_revalidation_headers(static_root, entry, validator):
    with TestClient(make_app(static_root)) as client:
        initial = client.get(entry)
        etag = initial.headers["etag"]
        header = {"exact": etag, "weak-list": f'"another-version", W/{etag}', "wildcard": "*"}[
            validator
        ]
        for method in (client.get, client.head):
            response = method(entry, headers={"If-None-Match": header})
            assert response.status_code == 304
            assert response.content == b""
            assert response.headers["etag"] == etag
            assert response.headers["cache-control"] == "no-cache"
        head = client.head(entry)
        assert head.status_code == 200 and head.content == b""
        assert head.headers["content-length"] == initial.headers["content-length"]
        assert head.headers["etag"] == etag
        assert head.headers["cache-control"] == "no-cache"
        assert client.get(entry, headers={"If-None-Match": '"old-release"'}).status_code == 200


def test_static_conditional_responses_revalidate_and_api_stays_no_store(static_root):
    with TestClient(make_app(static_root)) as client:
        initial = client.get("/static/app.js")
        assert initial.status_code == 200
        assert initial.headers["cache-control"] == "no-cache"
        for header in (
            {"If-None-Match": initial.headers["etag"]},
            {"If-Modified-Since": initial.headers["last-modified"]},
        ):
            cached = client.get("/static/app.js", headers=header)
            assert cached.status_code == 304 and cached.content == b""
            assert cached.headers["cache-control"] == "no-cache"
            assert cached.headers["etag"] == initial.headers["etag"]
        assert client.head("/static/app.js").headers["cache-control"] == "no-cache"
        assert client.get("/api/session").headers["cache-control"] == "no-store"
        assert client.post("/api/session", json={}).headers["cache-control"] == "no-store"
