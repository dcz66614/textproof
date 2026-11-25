"""Shared fixtures for the T010 privacy tests (PROJECT_BOOK.md §9).

Two instruments live here:

* :func:`socket_recorder` — a process-wide socket interceptor.  It
  wraps :meth:`socket.socket.connect` / ``connect_ex`` and
  :func:`socket.getaddrinfo`, records every attempt, lets loopback
  (``127.0.0.0/8``, ``::1``, ``localhost``) and AF_UNIX traffic
  through, and *blocks* anything else with ``OSError``.  A plain
  ``connect_ex`` probe is NOT used as evidence anywhere in this
  directory: on this VM outbound TCP is intercepted by the egress
  proxy (``198.19.0.1:3128``) and a connect to an unlistened port
  still returns success (T007/T008).  The recorder + the offline
  namespace tests are the honest replacements.
* :func:`take_snapshot` — a file-set snapshot used to prove a check
  writes nothing to disk (``__pycache__`` / ``*.pyc`` bytecode and
  ``.pytest_cache`` are excluded: they are interpreter/pytest
  artefacts, not product writes, and are listed separately).

Evidence: when the ``TEXTPROOF_PRIVACY_EVIDENCE_DIR`` environment
variable points at a directory, the recorder writes one JSONL log
per test (every connect / getaddrinfo attempt, allowed or blocked)
into it; otherwise the log is only asserted in-memory.
"""

from __future__ import annotations

import base64
import json
import os
import socket
import urllib.error
import urllib.request
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURES = REPO_ROOT / "tests" / "fixtures" / "s0"
MANIFEST = json.loads((FIXTURES / "manifest.json").read_text(encoding="utf-8"))

#: Unique expected text used by the leak tests.  It must appear in the
#: *response* (the user's own report) but never in any log, file or
#: second response.
SENTINEL_EXPECTED = "SENTINEL-T010-限时优惠-7f3a9"
#: What live OCR reads on TP-S0-ZH-001; must likewise never leak into
#: logs or files (it is part of the report, not of any log line).
SENTINEL_OCR_FRAGMENT = "限时优"

_WATCHED_SUBDIRS = ("src", "tests", "assets", "scripts", "schemas")


def fixture_record(fixture_id: str) -> dict:
    return next(f for f in MANIFEST["fixtures"] if f["id"] == fixture_id)


def fixture_bytes(fixture_id: str) -> bytes:
    record = fixture_record(fixture_id)
    return (FIXTURES / record["filename"]).read_bytes()


def fixture_path(fixture_id: str) -> Path:
    record = fixture_record(fixture_id)
    return FIXTURES / record["filename"]


def fixture_b64(fixture_id: str) -> str:
    return base64.b64encode(fixture_bytes(fixture_id)).decode("ascii")


def evidence_dir() -> Path | None:
    raw = os.environ.get("TEXTPROOF_PRIVACY_EVIDENCE_DIR", "")
    if not raw:
        return None
    path = Path(raw)
    path.mkdir(parents=True, exist_ok=True)
    return path


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def _http(method: str, url: str, body: object = None) -> tuple[int, bytes]:
    data = None
    headers: dict[str, str] = {}
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            return resp.status, resp.read()
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read()


# --- socket interception ---------------------------------------------------

def _is_loopback_host(host: object) -> bool:
    if host is None or host == "" or host == "localhost":
        return True
    if not isinstance(host, str):
        return False
    if host == "::1":
        return True
    parts = host.split(".")
    return (
        len(parts) == 4
        and all(part.isdigit() for part in parts)
        and int(parts[0]) == 127
        and all(0 <= int(part) <= 255 for part in parts)
    )


class SocketRecorder:
    """Records every connect / getaddrinfo; blocks non-loopback.

    ``attempts`` holds one dict per call: ``{"kind", "target",
    "allowed"}``.  ``external`` is the subset that was blocked.
    Loopback and AF_UNIX calls are passed through to the real
    implementation so the local server keeps working.
    """

    def __init__(self) -> None:
        self.attempts: list[dict[str, object]] = []
        self._orig_connect = socket.socket.connect
        self._orig_connect_ex = socket.socket.connect_ex
        self._orig_getaddrinfo = socket.getaddrinfo

    @property
    def external(self) -> list[dict[str, object]]:
        return [a for a in self.attempts if not a["allowed"]]

    @property
    def dns_hosts(self) -> list[object]:
        return [a["target"] for a in self.attempts if a["kind"] == "getaddrinfo"]

    def _connect(self, sock: socket.socket, address: object, *, use_ex: bool):
        # AF_UNIX: address is a filesystem path string.
        if isinstance(address, str):
            self.attempts.append(
                {"kind": "connect_ex" if use_ex else "connect",
                 "target": f"unix:{address}", "allowed": True})
            fn = self._orig_connect_ex if use_ex else self._orig_connect
            return fn(sock, address)
        host = address[0] if isinstance(address, tuple) else address
        allowed = _is_loopback_host(host)
        self.attempts.append(
            {"kind": "connect_ex" if use_ex else "connect",
             "target": repr(address), "allowed": allowed})
        if not allowed:
            if use_ex:
                return 101  # ENETUNREACH: fail closed, no packet leaves
            raise OSError(
                "T010 socket recorder: blocked non-loopback connect to "
                f"{address!r}")
        fn = self._orig_connect_ex if use_ex else self._orig_connect
        return fn(sock, address)

    def _getaddrinfo(self, host, port, *args, **kwargs):
        allowed = _is_loopback_host(host)
        self.attempts.append(
            {"kind": "getaddrinfo", "target": host, "allowed": allowed})
        if not allowed:
            raise socket.gaierror(
                "T010 socket recorder: blocked DNS lookup for "
                f"{host!r}")
        return self._orig_getaddrinfo(host, port, *args, **kwargs)

    def install(self, monkeypatch: pytest.MonkeyPatch) -> None:
        recorder = self

        def connect(sock, address, _orig=self._orig_connect):
            return recorder._connect(sock, address, use_ex=False)

        def connect_ex(sock, address, _orig=self._orig_connect_ex):
            return recorder._connect(sock, address, use_ex=True)

        def getaddrinfo(host, port, *args, **kwargs):
            return recorder._getaddrinfo(host, port, *args, **kwargs)

        monkeypatch.setattr(socket.socket, "connect", connect)
        monkeypatch.setattr(socket.socket, "connect_ex", connect_ex)
        monkeypatch.setattr(socket, "getaddrinfo", getaddrinfo)

    def assert_zero_external(self) -> None:
        assert self.external == [], (
            f"external network attempt(s) intercepted: {self.external}")


# --- filesystem snapshots ---------------------------------------------------

def _is_ignored(path: Path) -> bool:
    return (
        "__pycache__" in path.parts
        or path.suffix == ".pyc"
        or ".pytest_cache" in path.parts
    )


def take_snapshot(extra_roots: tuple[Path, ...] = ()) -> set[Path]:
    """File set under the watched repo dirs (+ any extra roots).

    Returns absolute paths; ``__pycache__`` / ``*.pyc`` /
    ``.pytest_cache`` are excluded (interpreter/pytest artefacts).
    """
    roots = [REPO_ROOT / sub for sub in _WATCHED_SUBDIRS] + list(extra_roots)
    found: set[Path] = set()
    for root in roots:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if path.is_file() and not _is_ignored(path):
                found.add(path)
    return found
