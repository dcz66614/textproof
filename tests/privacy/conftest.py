"""Fixtures for the T010 privacy tests (PROJECT_BOOK.md §9).

Helpers (socket recorder, snapshots, sentinels) live in
:mod:`t010_privacy_helpers`; this module only wires the two
fixtures pytest injects by name.
"""

from __future__ import annotations

import asyncio
import json
import threading
import time

import pytest
import uvicorn

from t010_privacy_helpers import (
    SocketRecorder,
    _free_port,
    _http,
    evidence_dir,
)
from textproof.api.app import create_app


@pytest.fixture(scope="module")
def live_server():
    """Real uvicorn server on 127.0.0.1 with access logging on.

    ``log_level="info"`` (unlike T007's ``"error"``) is deliberate:
    the log-leak tests need the real access log to exist so they can
    prove it carries no user data.
    """
    port = _free_port()
    server = uvicorn.Server(
        uvicorn.Config(
            create_app(), host="127.0.0.1", port=port, log_level="info"
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
            status, _ = _http("GET", f"{base}/api/v1/health")
            if status == 200:
                break
        except Exception:
            pass
        if time.monotonic() > deadline:
            raise RuntimeError("live privacy server did not come up in 60s")
        time.sleep(0.2)
    yield base
    server.should_exit = True
    thread.join(timeout=15)


@pytest.fixture
def socket_recorder(monkeypatch, request):
    """Install the interceptor for one test; write its log if asked."""
    recorder = SocketRecorder()
    recorder.install(monkeypatch)
    yield recorder
    out = evidence_dir()
    if out is not None:
        name = request.node.nodeid.replace("::", "__").replace("/", "_")
        (out / f"socket_intercept_{name}.jsonl").write_text(
            "".join(json.dumps(a, ensure_ascii=False) + "\n"
                    for a in recorder.attempts),
            encoding="utf-8",
        )
