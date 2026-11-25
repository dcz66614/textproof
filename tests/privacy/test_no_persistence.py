"""T010 acceptance 3/4/5: no persistence of user data, no temp files.

* Acceptance 3 — image bytes, expected text and OCR full text are
  written to no log, no database and no localStorage (log half is
  here; the localStorage half is static + the real-browser test in
  ``test_ui_clear_privacy.py``).
* Acceptance 4 — the API never writes the image to a persistent
  temp file: the route takes JSON base64 (no ``UploadFile`` /
  multipart anywhere in ``src/``), no ``tempfile`` is used, and a
  live check leaves the filesystem unchanged.
* Acceptance 5 — the server is stateless: two sequential checks
  share nothing, and no database file appears anywhere.
"""

from __future__ import annotations

import json
import logging
import os
import re
from pathlib import Path

import pytest

from t010_privacy_helpers import (
    REPO_ROOT,
    SENTINEL_EXPECTED,
    SENTINEL_OCR_FRAGMENT,
    _http,
    fixture_b64,
    fixture_bytes,
    take_snapshot,
)

from textproof.api import routes as api_routes
from textproof.api.routes import (
    ApiError,
    reset_ocr_adapter,
    run_check,
    set_ocr_adapter,
)
from textproof.cli import main as cli_main
from textproof.ocr.rapidocr_adapter import OCRAdapterError, RapidOCRAdapter


def _check_payload(expected_text: str = SENTINEL_EXPECTED) -> dict:
    return {
        "image_mime": "image/png",
        "image_base64": fixture_b64("TP-S0-ZH-001"),
        "expected_text": expected_text,
    }


def test_check_writes_no_files(live_server, tmp_path, monkeypatch):
    """Two live /check calls change no file under the repo or TMPDIR.

    ``TMPDIR`` is pointed at a fresh directory so any ``tempfile``
    use by the stack would show up there too.
    """
    tmpdir = tmp_path / "tmpdir"
    tmpdir.mkdir()
    monkeypatch.setenv("TMPDIR", str(tmpdir))
    before = take_snapshot((tmpdir,))
    for _ in range(2):
        status, raw = _http(
            "POST", f"{live_server}/api/v1/check",
            body=_check_payload())
        assert status == 200, raw[:300]
    assert take_snapshot((tmpdir,)) == before, (
        "a check created/changed files under the repo or TMPDIR")


def test_no_database_files_anywhere():
    """No sqlite / db file exists under the repo (acceptance 3)."""
    found = [
        p for p in REPO_ROOT.rglob("*")
        if p.is_file() and p.suffix.lower() in
        (".db", ".sqlite", ".sqlite3")
    ]
    assert found == [], f"database file(s) present: {found}"


# --- static: no persistence / network-client surface in our code --------

#: Tokens that must not occur in TextProof's own Python sources.
#: ``requests`` is deliberately NOT in this list: it is installed in
#: the venv as a transitive dependency of ``rapidocr`` (see
#: ``requirements.lock``: ``requests==2.34.2  # via rapidocr``), so
#: its mere presence proves nothing.  What matters is that our code
#: never imports it — and the socket-interception tests prove at
#: runtime that nothing ever calls it.
_FORBIDDEN_TOKENS = (
    "UploadFile", "multipart", "tempfile", "NamedTemporaryFile",
    "mkstemp", "TemporaryFile", "sqlite3", "telemetry", "sentry",
    "httpx", "urlopen", "urlretrieve", "os.system", "shell=True",
    "create_connection", "getaddrinfo",
)


@pytest.mark.parametrize("token", _FORBIDDEN_TOKENS)
def test_forbidden_token_absent_from_sources(token):
    hits = []
    for path in list(REPO_ROOT.glob("src/**/*.py")) + \
            list(REPO_ROOT.glob("scripts/*.py")):
        for lineno, line in enumerate(
                path.read_text(encoding="utf-8").splitlines(), 1):
            code = line.split("#", 1)[0]
            if token in code:
                hits.append(f"{path.relative_to(REPO_ROOT)}:{lineno}")
    assert hits == [], f"token {token!r} found in: {hits}"


def test_no_network_client_import_in_sources():
    """Our code imports no HTTP/DNS client library at all."""
    import_re = re.compile(
        r"^\s*(?:import|from)\s+"
        r"(requests|httpx|urllib|http\.client|socket)\b")
    hits = []
    for path in list(REPO_ROOT.glob("src/**/*.py")) + \
            list(REPO_ROOT.glob("scripts/*.py")):
        for lineno, line in enumerate(
                path.read_text(encoding="utf-8").splitlines(), 1):
            if import_re.search(line):
                hits.append(f"{path.relative_to(REPO_ROOT)}:{lineno}:"
                            f"{line.strip()}")
    assert hits == [], f"network-client import(s) in our code: {hits}"


def test_subprocess_only_in_cli_verify_s0_with_list_argv():
    """The only subprocess call is CLI verify-s0, fixed list argv.

    No shell, no user-derived argv: the command is
    ``[sys.executable, <repo>/scripts/verify_s0.py, ...]`` plus flags.
    """
    hits = []
    for path in REPO_ROOT.glob("src/**/*.py"):
        text = path.read_text(encoding="utf-8")
        if "subprocess" in text:
            hits.append(str(path.relative_to(REPO_ROOT)))
    assert hits == ["src/textproof/cli.py"], (
        f"subprocess used outside cli.py: {hits}")
    cli = (REPO_ROOT / "src" / "textproof" / "cli.py").read_text(
        encoding="utf-8")
    assert "shell" not in cli


# --- logs must not carry user data (acceptance 3, §9 bullet 6) -----------

def test_http_check_logs_contain_no_user_data(
    live_server, caplog, socket_recorder
):
    """Real HTTP /check with sentinel text: logs stay clean.

    The *response* must contain the sentinel (proof the check really
    processed it); every captured log record — textproof, uvicorn
    access and error — must not.
    """
    for logger_name in ("textproof", "uvicorn", "uvicorn.access",
                        "uvicorn.error"):
        caplog.set_level(logging.DEBUG, logger=logger_name)
    b64_prefix = fixture_b64("TP-S0-ZH-001")[:48]
    status, raw = _http(
        "POST", f"{live_server}/api/v1/check", body=_check_payload())
    assert status == 200, raw[:300]
    assert SENTINEL_EXPECTED in raw.decode("utf-8")  # sanity: really ran
    logs = caplog.text
    assert logs, "no log records were captured at all"
    for secret, label in (
        (SENTINEL_EXPECTED, "expected text"),
        (SENTINEL_OCR_FRAGMENT, "OCR text"),
        (b64_prefix, "image base64"),
        ("/home/", "home directory"),
        (str(REPO_ROOT), "repo absolute path"),
    ):
        assert secret not in logs, (
            f"log leak: {label} found in captured logs")


def test_ocr_failure_log_contains_no_user_data(caplog):
    """The OCR-failed path logs only the exception type name (§9)."""
    caplog.set_level(logging.DEBUG, logger="textproof")

    class _FailingAdapter:
        def recognize(self, image):
            raise OCRAdapterError("boom")

    set_ocr_adapter(_FailingAdapter())
    try:
        with pytest.raises(ApiError) as excinfo:
            run_check(
                image_mime="image/png",
                image_base64=fixture_b64("TP-S0-ZH-001"),
                expected_text=SENTINEL_EXPECTED,
            )
        assert excinfo.value.code == "OCR_FAILED"
    finally:
        reset_ocr_adapter()
    for secret in (SENTINEL_EXPECTED, SENTINEL_OCR_FRAGMENT):
        assert secret not in caplog.text, (
            f"OCR-failure log leaks user data: {secret!r}")


def test_missing_asset_logs_contain_no_absolute_path(
    caplog, monkeypatch, tmp_path
):
    """R-04: a missing OCR asset must not leak an absolute path (§9).

    Two halves: (a) the adapter's own FileNotFoundError names only the
    file, never the absolute asset path; (b) even if construction
    raised with an old-style absolute-path message, run_check maps it
    to OCR_FAILED and logs only the exception type, so no absolute
    path reaches the log.  Offline behaviour is unchanged: the
    request still fails, only the log stays clean.
    """
    caplog.set_level(logging.DEBUG, logger="textproof")

    # (a) Real adapter, empty assets dir: the first missing model.
    with pytest.raises(FileNotFoundError) as excinfo:
        RapidOCRAdapter(assets_dir=tmp_path)
    message = str(excinfo.value)
    assert "PP-OCRv6_det_small.onnx" in message
    assert str(tmp_path) not in message
    assert "/" not in message

    # (b) Simulated pre-fix message carrying an absolute asset path.
    absolute_asset = (
        tmp_path / "assets" / "ocr" / "models" / "PP-OCRv6_det_small.onnx"
    )

    def _boom() -> None:
        raise FileNotFoundError(
            f"OCR model asset missing: {absolute_asset}. Refusing to "
            "download at runtime (offline-only operation)."
        )

    monkeypatch.setattr(api_routes, "get_ocr_adapter", _boom)
    with pytest.raises(ApiError) as excinfo:
        run_check(
            image_mime="image/png",
            image_base64=fixture_b64("TP-S0-ZH-001"),
            expected_text=SENTINEL_EXPECTED,
        )
    assert excinfo.value.code == "OCR_FAILED"
    logs = caplog.text
    assert logs, "no log records were captured at all"
    for secret, label in (
        (str(absolute_asset), "absolute asset path"),
        (str(tmp_path), "temporary directory"),
        ("/home/", "home directory"),
    ):
        assert secret not in logs, f"log leak: {label} found in logs"


def test_cli_stderr_contains_no_user_data(capsys, tmp_path):
    """CLI check: stdout is the user's report; stderr stays clean."""
    image = tmp_path / "TP-S0-ZH-001.png"
    image.write_bytes(fixture_bytes("TP-S0-ZH-001"))
    expected = tmp_path / "expected.txt"
    expected.write_text(SENTINEL_EXPECTED, encoding="utf-8")
    exit_code = cli_main([
        "check", "--image", str(image), "--expected-file", str(expected)])
    assert exit_code in (1, 2)
    captured = capsys.readouterr()
    assert SENTINEL_EXPECTED in captured.out  # the report itself
    assert captured.err == "", f"CLI stderr not empty: {captured.err!r}"
    # Invalid input: stderr carries only the stable code, never a
    # path or user text.
    bad = tmp_path / "bad.png"
    bad.write_bytes(b"not an image at all")
    exit_code = cli_main([
        "check", "--image", str(bad), "--expected-file", str(expected)])
    assert exit_code == 3
    captured = capsys.readouterr()
    assert "INVALID_IMAGE" in captured.err or "invalid input" in captured.err
    assert SENTINEL_EXPECTED not in captured.err
    assert str(tmp_path) not in captured.err
    assert str(bad) not in captured.err


# --- statelessness (acceptance 5) ----------------------------------------

def test_stateless_no_cross_request_leak(live_server):
    """Second response contains nothing from the first request."""
    status1, raw1 = _http(
        "POST", f"{live_server}/api/v1/check", body=_check_payload())
    status2, raw2 = _http("POST", f"{live_server}/api/v1/check", body={
        "image_mime": "image/png",
        "image_base64": fixture_b64("TP-S0-ZH-002"),
        "expected_text": "新品上市",
    })
    assert status1 == 200 and status2 == 200
    second = raw2.decode("utf-8")
    assert SENTINEL_EXPECTED not in second
    assert SENTINEL_OCR_FRAGMENT not in second
    assert "新品上市" in second
    assert json.loads(raw1)["image"]["sha256"] != \
        json.loads(raw2)["image"]["sha256"]
