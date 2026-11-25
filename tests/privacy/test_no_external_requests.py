"""T010 acceptance 1: TextProof initiates zero external network requests.

Method (see the task card — ``connect_ex`` is NOT evidence on this
VM, because outbound TCP is intercepted by the egress proxy
``198.19.0.1:3128`` and a connect to an unlistened port still
returns success): every ``socket.connect`` / ``connect_ex`` /
``getaddrinfo`` call made while the product runs is recorded by the
:class:`SocketRecorder` (``conftest.py``); loopback is allowed
through, anything else is blocked and the test fails.  The three
product paths are covered: CLI ``check`` (in-process, includes OCR
engine construction), the live API server + ``/check`` over HTTP,
and ``version`` / ``health``.  The offline-namespace tests in
``tests/offline/`` re-run the same paths with no network namespace
at all.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from t010_privacy_helpers import (
    SENTINEL_EXPECTED,
    _http,
    _is_loopback_host,
    fixture_b64,
    fixture_bytes,
)

from textproof.cli import main as cli_main


@pytest.mark.parametrize("host,expected", [
    ("127.0.0.1", True), ("127.0.0.2", True), ("127.255.255.255", True),
    ("::1", True), ("localhost", True), ("", True), (None, True),
    ("0.0.0.0", False), ("198.19.0.2", False), ("8.8.8.8", False),
    ("127.0.0.300", False), ("127.0.0", False), ("example.com", False),
    ("127.0.0.1.1", False),
])
def test_is_loopback_host(host, expected):
    """The recorder's loopback classifier itself (regression test:
    an earlier version misclassified 127.0.0.1 as external)."""
    assert _is_loopback_host(host) is expected


def _expected_file(tmp_path: Path, text: str = SENTINEL_EXPECTED) -> Path:
    path = tmp_path / "expected.txt"
    path.write_text(text, encoding="utf-8")
    return path


def test_cli_check_zero_external_connections(
    socket_recorder, capsys, tmp_path
):
    """CLI check (real OCR, engine constructed under the recorder).

    The sentinel expected text forces a real comparison; the report
    goes to stdout (the user's own output channel) and must contain
    the sentinel, while the recorder must have seen no external
    connect and no external DNS lookup.
    """
    image = tmp_path / "TP-S0-ZH-001.png"
    image.write_bytes(fixture_bytes("TP-S0-ZH-001"))
    exit_code = cli_main([
        "check",
        "--image", str(image),
        "--expected-file", str(_expected_file(tmp_path)),
    ])
    assert exit_code in (1, 2), f"unexpected CLI exit {exit_code}"
    captured = capsys.readouterr()
    report = json.loads(captured.out)
    assert report["verdict"] in ("MISMATCH", "REVIEW_REQUIRED")
    assert report["expected_text"] == SENTINEL_EXPECTED
    assert captured.err == "", f"unexpected CLI stderr: {captured.err!r}"
    socket_recorder.assert_zero_external()
    # The CLI path performs no socket I/O whatsoever — zero connects
    # AND zero DNS lookups is the expected outcome here, not a sign
    # the recorder was not installed (the API tests below prove the
    # recorder sees loopback traffic when there is any).
    assert socket_recorder.attempts == [], (
        f"CLI check made socket call(s): {socket_recorder.attempts}")
    assert socket_recorder.dns_hosts == []


def test_api_check_zero_external_connections(live_server, socket_recorder):
    """Live server /check over real HTTP, under the recorder."""
    status, raw = _http("POST", f"{live_server}/api/v1/check", body={
        "image_mime": "image/png",
        "image_base64": fixture_b64("TP-S0-ZH-001"),
        "expected_text": SENTINEL_EXPECTED,
    })
    assert status == 200, raw[:300]
    report = json.loads(raw)
    assert report["expected_text"] == SENTINEL_EXPECTED
    socket_recorder.assert_zero_external()
    loopback = [a for a in socket_recorder.attempts if a["allowed"]]
    assert loopback, "no loopback connection was recorded at all"


def test_version_and_health_zero_external_connections(
    live_server, socket_recorder
):
    for path in ("/api/v1/version", "/api/v1/health", "/version"):
        status, raw = _http("GET", f"{live_server}{path}")
        assert status == 200, path
        assert json.loads(raw)["service"] == "textproof"
    socket_recorder.assert_zero_external()
