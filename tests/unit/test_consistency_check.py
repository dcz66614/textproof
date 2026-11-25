"""T013 R-02/R-06/R-07/R-08: tests for ``tests/consistency_check.py``.

The script itself is a standalone three-way (API/CLI/UI) check that
needs a live server and a real browser; its full run is exercised
outside pytest (see ``task_handoffs/T013/consistency/``).  These unit
tests lock the T013 fixes at the helper level:

* R-02 — the script lives in ``tests/`` (outside the T010 privacy
  scan tree ``src/**/*.py`` + ``scripts/*.py``) and no copy remains
  in ``scripts/``.
* R-06 — every leg of every case is stored under its own
  ``<kind>-<case>.json`` filename, with the SHA-256 of the stored
  bytes.
* R-07 — the HTTP helpers refuse any non-loopback base, and only
  ever talk to ``http://127.0.0.1:<port>``.
* R-08 — shared scratch files are deleted after a run, per-case
  evidence files are kept, and the docstring declares that the
  outputs contain fixture text and must not be used for real user
  images.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "tests" / "consistency_check.py"


def _load_script():
    spec = importlib.util.spec_from_file_location(
        "consistency_check", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def cc():
    return _load_script()


# --- R-02: location ---------------------------------------------------------

def test_script_lives_in_tests_not_scripts():
    assert SCRIPT.is_file()
    assert not (REPO_ROOT / "scripts" / "consistency_check.py").exists()


# --- R-07: loopback-only HTTP -----------------------------------------------

@pytest.mark.parametrize("base", [
    "http://127.0.0.1:8123",
    "http://127.0.0.1:1",
])
def test_require_loopback_accepts_127_0_0_1(cc, base):
    cc._require_loopback(base)  # must not raise


@pytest.mark.parametrize("base", [
    "http://localhost:8123",
    "http://0.0.0.0:8123",
    "https://127.0.0.1:8123",
    "http://127.0.0.1.evil.example:8123",
    "http://example.com:80",
    "http://127.0.0.2:8123",
    "",
    "not-a-url",
])
def test_require_loopback_rejects_anything_else(cc, base):
    with pytest.raises(AssertionError):
        cc._require_loopback(base)


def test_http_helpers_reject_non_loopback_before_connect(cc):
    # The assertion fires before any socket is opened: no connection
    # attempt is made to the (unreachable) host.
    with pytest.raises(AssertionError):
        cc._http_post("http://example.com:80", "/api/v1/check", {})
    with pytest.raises(AssertionError):
        cc._http_get("http://example.com:80", "/api/v1/health")


class _EchoHandler(BaseHTTPRequestHandler):
    def do_GET(self):  # noqa: N802
        if self.path == "/ok":
            body = b'{"status": "ok"}'
            self.send_response(200)
        else:
            body = b"nope"
            self.send_response(404)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):  # noqa: N802
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length)
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def log_message(self, *args):  # keep test output clean
        pass


@pytest.fixture()
def loopback_server():
    server = ThreadingHTTPServer(("127.0.0.1", 0), _EchoHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_address[1]}"
    finally:
        server.shutdown()
        server.server_close()


def test_http_helpers_talk_to_loopback_server(cc, loopback_server):
    assert cc._http_get(loopback_server, "/ok") == 200
    assert cc._http_get(loopback_server, "/missing") == 404
    status, body = cc._http_post(
        loopback_server, "/echo", {"hello": "world"})
    assert status == 200
    assert json.loads(body) == {"hello": "world"}


# --- R-06: per-case files + SHA-256 -----------------------------------------

def test_write_case_report_per_case_files_and_sha(cc, tmp_path):
    api_raw = json.dumps({"verdict": "MISMATCH", "n": 1}).encode()
    cli_raw = json.dumps({"verdict": "MISMATCH", "n": 1}).encode()
    api_path, api_sha = cc._write_case_report(
        tmp_path, "api", "TP-S0-ZH-002", api_raw)
    cli_path, cli_sha = cc._write_case_report(
        tmp_path, "cli", "TP-S0-ZH-002", cli_raw)
    other_path, _ = cc._write_case_report(
        tmp_path, "api", "TP-CLN-001", api_raw)
    # Distinct filenames per case (no shared file to overwrite).
    assert api_path.name == "api-TP-S0-ZH-002.json"
    assert cli_path.name == "cli-TP-S0-ZH-002.json"
    assert other_path.name == "api-TP-CLN-001.json"
    assert api_path != other_path
    # SHA-256 matches the stored bytes exactly.
    assert api_sha == hashlib.sha256(api_raw).hexdigest()
    assert api_sha == hashlib.sha256(api_path.read_bytes()).hexdigest()
    assert cli_sha == hashlib.sha256(cli_path.read_bytes()).hexdigest()
    # A second case does not clobber the first.
    assert api_path.read_bytes() == api_raw
    assert json.loads(cli_path.read_bytes())["verdict"] == "MISMATCH"


# --- R-08: scratch cleanup + fixture-text declaration -----------------------

def test_cleanup_scratch_removes_shared_files_keeps_case_files(cc, tmp_path):
    workdir = tmp_path / "consistency_work"
    downloads = workdir / "downloads"
    downloads.mkdir(parents=True)
    for path in (workdir / "expected.txt",
                 workdir / "cli-report.json",
                 downloads / "textproof-report.json"):
        path.write_text("fixture text", encoding="utf-8")
    kept, _ = cc._write_case_report(
        workdir, "cli", "TP-S0-ZH-002", b'{"verdict": "MISMATCH"}')
    cc._cleanup_scratch(workdir, downloads)
    assert not (workdir / "expected.txt").exists()
    assert not (workdir / "cli-report.json").exists()
    assert not (downloads / "textproof-report.json").exists()
    assert kept.exists()  # per-case evidence is kept
    # Missing scratch files are fine (idempotent).
    cc._cleanup_scratch(workdir, downloads)


def test_docstring_declares_fixture_text_not_for_real_users(cc):
    doc = (cc.__doc__ or "").lower()
    assert "fixture" in doc
    assert "real user" in doc
