"""Shared fixtures for the T008 UI end-to-end tests.

* ``live_server`` — the real FastAPI app (with the T008 static UI
  mount) on a real loopback socket, same pattern as T007's
  ``tests/integration/test_api.py`` (no TestClient: httpx is not in
  the frozen lockfile).
* ``chrome`` / ``page`` — a real headless Chrome (from the Playwright
  browser cache; no download, no new dependency) driven over CDP by
  the stdlib-only client in ``cdp.py``.
* ``evidence_dir`` — where screenshots and the network-request log
  are written; the T008 handoff copies them into
  ``task_handoffs/T008/``.

No test here touches the network: the server binds 127.0.0.1 and the
browser is pointed at that origin only.
"""

from __future__ import annotations

import asyncio
import json
import os
import socket
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

import pytest
import uvicorn

from textproof.api.app import create_app

from cdp import Chrome  # noqa: E402  (tests/e2e is on sys.path via rootdir)

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURES = REPO_ROOT / "tests" / "fixtures" / "s0"
UI_DIR = REPO_ROOT / "src" / "textproof" / "ui"
MANIFEST = json.loads((FIXTURES / "manifest.json").read_text(encoding="utf-8"))

EVIDENCE_DIR = Path(
    os.environ.get(
        "TEXTPROOF_E2E_EVIDENCE",
        str(Path(__file__).resolve().parent / "evidence"),
    )
)


def fixture_record(fixture_id: str) -> dict:
    return next(f for f in MANIFEST["fixtures"] if f["id"] == fixture_id)


def fixture_path(fixture_id: str) -> Path:
    return FIXTURES / fixture_record(fixture_id)["filename"]


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def _http_get(base: str, path: str) -> tuple[int, dict, bytes]:
    req = urllib.request.Request(base + path)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status, dict(resp.headers), resp.read()
    except urllib.error.HTTPError as exc:
        return exc.code, dict(exc.headers), exc.read()


@pytest.fixture(scope="module")
def live_server():
    """Real uvicorn server on 127.0.0.1; yields the base URL."""
    port = _free_port()
    server = uvicorn.Server(
        uvicorn.Config(
            create_app(), host="127.0.0.1", port=port, log_level="error"
        )
    )
    thread = threading.Thread(
        target=asyncio.run, args=(server.serve(),), daemon=True
    )
    thread.start()
    base = f"http://127.0.0.1:{port}"
    deadline = time.monotonic() + 60
    while True:
        try:
            status, _, _ = _http_get(base, "/api/v1/health")
            if status == 200:
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
def evidence_dir():
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    return EVIDENCE_DIR


@pytest.fixture(scope="module")
def chrome(evidence_dir):
    """One headless Chrome for the whole browser module."""
    browser = Chrome()
    try:
        browser.set_download_dir(evidence_dir / "downloads")
        browser.grant_clipboard()
        yield browser
    finally:
        browser.stop()


@pytest.fixture(scope="module")
def page(chrome):
    """The single tab; each test navigates it fresh."""
    return chrome.new_page()
