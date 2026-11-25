"""T010 acceptance 6 (browser half): clear revokes the preview object
URL and drops the report / text from the UI; acceptance 3 (browser
half): the page never touches persistent browser storage and issues
no non-same-origin request.

The OCR engine is stubbed for this module (``set_ocr_adapter``):
the clear behaviour does not depend on OCR, and stubbing keeps the
test fast.  The same clear flow with the real engine is already
proven by T008's ``test_clear_revokes_object_url_and_resets``; this
module re-proves it inside the privacy acceptance scope and adds
the network-log + storage-trap assertions.  The stub returns the
exact line live OCR reads on TP-S0-ZH-001 (``限时优``), so the
rendered verdict is the same MISMATCH the real engine produces.
"""

from __future__ import annotations

import asyncio
import json
import os
import socket
import sys
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

import pytest
import uvicorn

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "e2e"))

from cdp import Chrome, navigate_fresh  # noqa: E402
from textproof.api.app import create_app  # noqa: E402
from textproof.api.routes import reset_ocr_adapter, set_ocr_adapter  # noqa: E402
from textproof.ocr.rapidocr_adapter import OCRLine  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURES = REPO_ROOT / "tests" / "fixtures" / "s0"
MANIFEST = json.loads((FIXTURES / "manifest.json").read_text(encoding="utf-8"))


def _fixture_path(fixture_id: str) -> Path:
    record = next(f for f in MANIFEST["fixtures"] if f["id"] == fixture_id)
    return FIXTURES / record["filename"]


class _StubAdapter:
    """Fixed OCR output for TP-S0-ZH-001 (drawn text ``限时优``)."""

    def recognize(self, pil_image):
        return [OCRLine(
            line_index=0, text="限时优", confidence=0.99,
            bbox_xyxy=(100.0, 100.0, 400.0, 200.0),
            quad=((100.0, 100.0), (400.0, 100.0),
                  (400.0, 200.0), (100.0, 200.0)),
            source_order=0,
        )]


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def _http_get(base: str, path: str) -> int:
    try:
        with urllib.request.urlopen(base + path, timeout=30) as resp:
            resp.read()
            return resp.status
    except urllib.error.HTTPError as exc:
        return exc.code


@pytest.fixture(scope="module")
def live_server():
    port = _free_port()
    server = uvicorn.Server(
        uvicorn.Config(
            create_app(), host="127.0.0.1", port=port, log_level="error"))
    thread = threading.Thread(
        target=asyncio.run, args=(server.serve(),), daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{port}"
    deadline = time.monotonic() + 60
    while True:
        try:
            if _http_get(base, "/api/v1/health") == 200:
                break
        except Exception:
            pass
        if time.monotonic() > deadline:
            raise RuntimeError("live UI server did not come up in 60s")
        time.sleep(0.2)
    yield base
    server.should_exit = True
    thread.join(timeout=15)


@pytest.fixture(scope="module")
def evidence_dir(tmp_path_factory):
    raw = os.environ.get("TEXTPROOF_PRIVACY_EVIDENCE_DIR", "")
    if raw:
        path = Path(raw)
    else:
        path = tmp_path_factory.mktemp("t010-browser")
    path.mkdir(parents=True, exist_ok=True)
    return path


@pytest.fixture(scope="module")
def chrome(evidence_dir):
    browser = Chrome()
    try:
        browser.set_download_dir(evidence_dir / "downloads")
        browser.grant_clipboard()
        yield browser
    finally:
        browser.stop()


@pytest.fixture(scope="module")
def page(chrome):
    return chrome.new_page()


def _assert_no_storage_access(page):
    """Runtime storage trap (T008): no storage was ever touched."""
    accessed = page.evaluate("window.__tpStorageAccess")
    assert accessed == [], f"page touched browser storage: {accessed}"
    assert page.evaluate("localStorage.length") == 0


def _assert_same_origin_network(page, base, start_index, evidence_dir):
    page.cdp.drain_events()
    requests = page.network_requests()[start_index:]
    assert requests, "no network requests were observed at all"
    (evidence_dir / "browser_network_requests.jsonl").write_text(
        "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in requests),
        encoding="utf-8",
    )
    for req in requests:
        url = req["url"]
        ok = (
            url.startswith(base + "/")
            or url.startswith("blob:" + base + "/")
            or url.startswith("data:")
        )
        assert ok, f"non-same-origin request observed: {req}"


def test_clear_revokes_object_url_and_drops_report(
    page, live_server, evidence_dir
):
    """Acceptance 6 + 3 (browser): check, then clear, then nothing
    from the image or report is reachable from the UI anymore."""
    set_ocr_adapter(_StubAdapter())
    try:
        start = len(page.network_requests())
        navigate_fresh(page, live_server)
        page.set_file_input("#file-input", str(_fixture_path("TP-S0-ZH-001")))
        page.set_textarea("#expected-text", "限时优惠")
        page.wait_for(
            "document.querySelector('#btn-check').disabled === false",
            timeout=30, desc="check button to enable after upload",
        )
        time.sleep(1.0)  # FileReader base64 + preview <img> load
        page.click("#btn-check")
        page.wait_for(
            "document.querySelector('#verdict').textContent"
            ".indexOf('尚未核对') === -1",
            timeout=60, desc="verdict to appear after check",
        )
        verdict = page.evaluate(
            "document.querySelector('#verdict').textContent")
        assert "检测到差异" in verdict, f"unexpected verdict: {verdict!r}"
        assert "MISSING_CHARACTER" in page.evaluate(
            "document.querySelector('#error-list').textContent")
        # The export warning (§9) is visible on the page.
        assert "可能包含敏感文字" in page.evaluate(
            "document.querySelector('#export-warning').textContent")

        old_url = page.evaluate(
            "document.querySelector('#preview-img').src")
        assert old_url.startswith("blob:"), f"preview src: {old_url!r}"

        page.click("#btn-clear")
        page.wait_for(
            "document.querySelector('#verdict').textContent === '尚未核对'",
            timeout=10, desc="verdict to reset after clear",
        )
        assert page.evaluate(
            "document.querySelector('#preview-img').hidden") is True
        assert page.evaluate(
            "document.querySelector('#preview-img')"
            ".getAttribute('src')") is None
        assert page.evaluate(
            "document.querySelector('#file-input').value") == ""
        assert page.evaluate(
            "document.querySelector('#expected-text').value") == ""
        assert "暂无错误清单" in page.evaluate(
            "document.querySelector('#error-list').textContent")
        assert page.evaluate(
            "document.querySelector('#report-json').textContent") \
            == "尚未生成报告。"
        assert page.evaluate(
            "document.querySelector('#btn-check').disabled") is True
        assert page.evaluate(
            "document.querySelector('#btn-download').disabled") is True
        # The revoked blob URL must no longer resolve.
        fetched = page.evaluate(
            f"fetch({json.dumps(old_url)}).then(() => 'OK')"
            ".catch((e) => 'REJECTED:' + e.name)",
            await_promise=True,
        )
        assert str(fetched).startswith("REJECTED"), (
            f"old preview object URL still resolves after clear: "
            f"{fetched!r}")
        _assert_no_storage_access(page)
        _assert_same_origin_network(
            page, live_server, start, evidence_dir)
    finally:
        reset_ocr_adapter()
