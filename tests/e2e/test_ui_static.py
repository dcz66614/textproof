"""T008 static (no-browser) UI tests.

Acceptance 4 (wording) and 5 (zero external references) and 6
(no browser storage) are provable from the shipped files alone;
acceptance 1–3 are covered by the real-browser module
``test_ui_browser.py``.  The static serving itself is exercised
here against the real server (same-origin mount, API routes still
win over the static mount).
"""

from __future__ import annotations

import json
import re
import urllib.error
import urllib.request
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
UI_DIR = REPO_ROOT / "src" / "textproof" / "ui"


def _http_get(base: str, path: str) -> tuple[int, dict, bytes]:
    req = urllib.request.Request(base + path)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return (resp.status,
                    {k.lower(): v for k, v in resp.headers.items()},
                    resp.read())
    except urllib.error.HTTPError as exc:
        return (exc.code,
                {k.lower(): v for k, v in exc.headers.items()},
                exc.read())

UI_FILES = {
    "index.html": (UI_DIR / "index.html").read_text(encoding="utf-8"),
    "app.js": (UI_DIR / "app.js").read_text(encoding="utf-8"),
    "style.css": (UI_DIR / "style.css").read_text(encoding="utf-8"),
}

# --- acceptance 5: no external references -------------------------------
# Anything that could pull a remote asset: an absolute http(s) URL, a
# protocol-relative URL with a dotted host, a @import, a url(http…),
# a script/link/img pointing at http(s), or a known font/CDN host.
EXTERNAL_PATTERNS = [
    re.compile(r"https?://", re.IGNORECASE),
    re.compile(r"(?<![\w:])//[A-Za-z0-9][\w.-]*\.[a-z]{2,}", re.IGNORECASE),
    re.compile(r"@import", re.IGNORECASE),
    re.compile(r"url\(\s*[\"']?https?:", re.IGNORECASE),
    re.compile(r"(?:src|href)\s*=\s*[\"']https?:", re.IGNORECASE),
    re.compile(r"fonts\.googleapis|googleapis\.com|gstatic\.com",
               re.IGNORECASE),
    re.compile(r"\bcdn\b", re.IGNORECASE),
    re.compile(r"unpkg\.com|jsdelivr\.net|cdnjs\.cloudflare\.com",
               re.IGNORECASE),
]


@pytest.mark.parametrize("name", ["index.html", "app.js", "style.css"])
def test_ui_file_exists(name):
    assert (UI_DIR / name).is_file()


@pytest.mark.parametrize("name", ["index.html", "app.js", "style.css"])
def test_no_external_references(name):
    text = UI_FILES[name]
    hits = [pat.pattern for pat in EXTERNAL_PATTERNS if pat.search(text)]
    assert not hits, f"{name} contains external-reference pattern(s): {hits}"


@pytest.mark.parametrize("name", ["index.html", "app.js", "style.css"])
def test_no_browser_storage_reference(name):
    """Acceptance 6 (static half): the UI never names any storage API."""
    text = UI_FILES[name]
    for token in ("localStorage", "sessionStorage", "indexedDB",
                  "document.cookie"):
        assert token not in text, f"{name} mentions {token}"


# --- acceptance 4: wording ----------------------------------------------

REQUIRED_WORDING = [
    # §3.2 empty state.
    "先上传图片，再输入期望文本",
    # §3.2 low-confidence wording, verbatim.
    "识别结果不确定，需要人工查看原图片区域",
    # REVIEW_REQUIRED / OCR_FAILED must be framed as "待确认".
    "待确认",
    "不是确定的错误",
    # Missing whole line: never invent a box (§4.6, FR-06).
    "无可定位 OCR 框",
    # Offline status + same-origin API prefix only.
    "离线 / 本机运行",
    "/api/v1/check",
]

FORBIDDEN_WORDING = [
    # §3.3: never claim the image is proven wrong.
    "已证明图片一定写错",
    "图片一定写错",
    "已证明图片写错",
]


@pytest.mark.parametrize("phrase", REQUIRED_WORDING)
def test_required_wording_present(phrase):
    haystack = "\n".join(UI_FILES.values())
    assert phrase in haystack, f"missing required wording: {phrase!r}"


@pytest.mark.parametrize("phrase", FORBIDDEN_WORDING)
def test_misleading_wording_absent(phrase):
    haystack = "\n".join(UI_FILES.values())
    assert phrase not in haystack, f"misleading wording present: {phrase!r}"


def test_ui_calls_only_same_origin_api():
    """app.js fetches /api/v1/* (relative constants); no absolute
    origin anywhere.  fetch() is called with the constants, so the
    test checks the constant definitions, not call-site literals."""
    js = UI_FILES["app.js"]
    urls = dict(re.findall(
        r"var (CHECK_URL|VERSION_URL) = \"([^\"]+)\";", js))
    assert urls.get("CHECK_URL") == "/api/v1/check"
    assert urls.get("VERSION_URL") == "/api/v1/version"
    fetch_calls = re.findall(r"fetch\(\s*([A-Za-z_]+)\s*,", js)
    assert fetch_calls, "app.js issues no fetch() call"
    for name in fetch_calls:
        assert name in urls, f"fetch() with unknown target: {name}"
    assert "127.0.0.1" not in js
    assert "localhost" not in js


# --- static serving ------------------------------------------------------

def test_serves_index_html(live_server):
    status, headers, body = _http_get(live_server, "/")
    assert status == 200
    assert "text/html" in headers.get("content-type", "")
    assert b"TextProof" in body
    assert b'id="file-input"' in body
    assert b'id="expected-text"' in body
    assert b'id="btn-check"' in body
    assert b'id="btn-recheck"' in body
    assert b'id="btn-download"' in body
    assert b'id="btn-clear"' in body
    assert b'id="error-list"' in body
    assert b'id="overlay"' in body


def test_serves_app_js_and_css(live_server):
    status, headers, body = _http_get(live_server, "/app.js")
    assert status == 200
    assert "javascript" in headers.get("content-type", "")
    assert b"URL.createObjectURL" in body
    assert b"URL.revokeObjectURL" in body
    status, headers, body = _http_get(live_server, "/style.css")
    assert status == 200
    assert "text/css" in headers.get("content-type", "")
    assert b".ocr-box" in body
    assert b".ocr-box.selected" in body


def test_api_routes_still_win_over_static_mount(live_server):
    """Acceptance: the T007 API is untouched — health/version/check
    still answer, and unknown paths keep the JSON 404 envelope."""
    status, _, body = _http_get(live_server, "/api/v1/health")
    assert status == 200
    assert json.loads(body)["status"] == "ok"
    status, _, body = _http_get(live_server, "/api/v1/version")
    assert status == 200
    assert json.loads(body)["tool_version"] == "0.1.0"
    status, _, body = _http_get(live_server, "/does-not-exist")
    assert status == 404
    assert json.loads(body)["error"]["code"] == "NOT_FOUND"
