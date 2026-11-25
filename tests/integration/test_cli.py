"""Integration tests for the T009 CLI (PROJECT_BOOK.md §5.5).

Acceptance command: ``python -m pytest tests/integration/test_cli.py -q``.

Coverage maps to the T009 acceptance criteria:

1. ``check`` / ``serve`` / ``verify-s0`` / ``version`` all usable.
2. ``check`` output is the same ``textproof.report/v1`` as the API
   (same ``run_check`` pipeline; dict-equal for the same inputs).
3. Exit codes 0-5 per §5.5, one test per code (argparse usage errors
   exit 3, never argparse's default 2, which already means
   ``REVIEW_REQUIRED``).
4. Privacy: JSON output contains no image base64, no absolute path,
   no home path — exercised with inputs that live under the user's
   home directory.
5. Every report passes JSON Schema validation: the frozen
   ``schemas/textproof.report.v1.schema.json`` plus the handwritten
   ``scripts/validate_report_schema.py`` (``jsonschema`` is NOT in the
   frozen lock, so no new dependency is added; the schema file is
   additionally cross-checked with the system ``jsonschema`` as
   evidence in ``task_handoffs/T009/``, not as a test dependency).
   The frozen F-03 forms are asserted both ways: production forms
   validate, Oracle forms (``[0, 0]`` absent-side span,
   ``bbox_scope == "none"``, warning ``confidence`` field) do not.

Most ``check`` tests use a stub OCR engine injected through the
routes singleton (``set_ocr_adapter``), so verdicts are deterministic
and fast.  Two tests run the real engine end to end (one in-process
via the stub-free path is deliberately avoided — the real-engine
proof is the subprocess ``check`` below plus the S0 rerun evidence).
No network is used anywhere.
"""

from __future__ import annotations

import base64
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

import pytest

from textproof import cli as cli_module
from textproof.cli import EXIT_FOR_VERDICT, build_parser, main
from textproof.core.report import build_report
from textproof.io.image_loader import load_image
from textproof.ocr.rapidocr_adapter import OCRLine

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURES = REPO_ROOT / "tests" / "fixtures" / "s0"
MANIFEST = json.loads((FIXTURES / "manifest.json").read_text(encoding="utf-8"))
SCHEMA_PATH = REPO_ROOT / "schemas" / "textproof.report.v1.schema.json"

sys.path.insert(0, str(REPO_ROOT))
from scripts.validate_report_schema import validate_report  # noqa: E402

from textproof.api.routes import (  # noqa: E402
    reset_ocr_adapter,
    run_check,
    set_ocr_adapter,
)

ZH001 = next(f for f in MANIFEST["fixtures"] if f["id"] == "TP-S0-ZH-001")
ZH001_BYTES = (FIXTURES / ZH001["filename"]).read_bytes()
ZH001_B64 = base64.b64encode(ZH001_BYTES).decode("ascii")
# ZH-001 image is 1200x480 per the S0 fixture; read the real size so
# stub bboxes always stay inside the image bounds.
ZH001_IMAGE = load_image(ZH001_BYTES)
_W, _H = ZH001_IMAGE.width, ZH001_IMAGE.height


def _line(text: str, confidence: float = 0.99) -> OCRLine:
    return OCRLine(
        line_index=0,
        text=text,
        confidence=confidence,
        bbox_xyxy=(10.0, 10.0, float(_W - 10), float(_H - 10)),
        quad=((10.0, 10.0), (float(_W - 10), 10.0),
              (float(_W - 10), float(_H - 10)), (10.0, float(_H - 10))),
        source_order=0,
    )


class _StubAdapter:
    """Deterministic stub OCR engine returning fixed lines."""

    def __init__(self, lines: list[OCRLine]) -> None:
        self._lines = lines

    def recognize(self, image):  # noqa: ARG002 - signature matches adapter
        return list(self._lines)


class _FailingAdapter:
    def recognize(self, image):  # noqa: ARG002
        raise RuntimeError("simulated engine failure")


@pytest.fixture(autouse=True)
def _clean_adapter():
    reset_ocr_adapter()
    yield
    reset_ocr_adapter()


@pytest.fixture()
def check_files(tmp_path: Path):
    """A real S0 PNG plus an expected-text file, under tmp_path."""
    image = tmp_path / "poster.png"
    image.write_bytes(ZH001_BYTES)
    expected = tmp_path / "expected.txt"
    expected.write_text("限时优惠", encoding="utf-8")
    return image, expected


def _run_check_cli(image: Path, expected: Path, *extra: str,
                   capsys) -> tuple[int, str, str]:
    code = main(["check", "--image", str(image),
                 "--expected-file", str(expected), *extra])
    captured = capsys.readouterr()
    return code, captured.out, captured.err


# --- version -------------------------------------------------------------

def test_version_reports_frozen_versions(capsys):
    assert main(["version"]) == 0
    out = capsys.readouterr().out
    info = json.loads(out)
    assert info["service"] == "textproof"
    assert info["tool_version"] == "0.1.0"
    assert info["schema"] == "textproof.report/v1"
    assert info["spec_version"] == "1.0.0"
    assert info["rapidocr_version"] == "3.10.0"
    assert info["onnxruntime_version"] == "1.32.0"
    assert info["providers"] == ["CPUExecutionProvider"]
    # package_version is reported distinctly from tool_version; in the
    # dev checkout the package is not installed, which is reported
    # honestly rather than invented.
    assert info["package_version"] in ("1.0.0", "not-installed")


def test_version_via_module_subprocess():
    env = dict(os.environ, PYTHONPATH=str(REPO_ROOT / "src"))
    result = subprocess.run(
        [sys.executable, "-m", "textproof.cli", "version"],
        capture_output=True, text=True, cwd=REPO_ROOT, env=env, timeout=120,
    )
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["tool_version"] == "0.1.0"


# --- check: verdict -> exit code (one test per §5.5 code 0, 1, 2, 4) ---

def test_check_match_exits_0(check_files, capsys):
    set_ocr_adapter(_StubAdapter([_line("限时优惠")]))
    image, expected = check_files
    code, out, _ = _run_check_cli(image, expected, capsys=capsys)
    assert code == EXIT_FOR_VERDICT["MATCH"] == 0
    report = json.loads(out)
    assert report["verdict"] == "MATCH"
    assert validate_report(report) == []


def test_check_mismatch_exits_1(check_files, capsys):
    set_ocr_adapter(_StubAdapter([_line("限时优")]))
    image, expected = check_files
    code, out, _ = _run_check_cli(image, expected, capsys=capsys)
    assert code == EXIT_FOR_VERDICT["MISMATCH"] == 1
    report = json.loads(out)
    assert report["verdict"] == "MISMATCH"
    assert report["errors"][0]["type"] == "MISSING_CHARACTER"
    assert validate_report(report) == []


def test_check_review_required_exits_2(check_files, capsys):
    # Same text, but a sub-threshold line forces REVIEW_REQUIRED.
    set_ocr_adapter(_StubAdapter([_line("限时优惠", confidence=0.5)]))
    image, expected = check_files
    code, out, _ = _run_check_cli(image, expected, capsys=capsys)
    assert code == EXIT_FOR_VERDICT["REVIEW_REQUIRED"] == 2
    report = json.loads(out)
    assert report["verdict"] == "REVIEW_REQUIRED"
    assert report["warnings"][0]["code"] == "LOW_OCR_CONFIDENCE"
    assert validate_report(report) == []


def test_check_ocr_failed_verdict_exits_4(check_files, capsys):
    # No usable OCR text: verdict OCR_FAILED, exit 4 (not 2).
    set_ocr_adapter(_StubAdapter([]))
    image, expected = check_files
    code, out, _ = _run_check_cli(image, expected, capsys=capsys)
    assert code == EXIT_FOR_VERDICT["OCR_FAILED"] == 4
    report = json.loads(out)
    assert report["verdict"] == "OCR_FAILED"
    assert report["warnings"][0]["code"] == "OCR_EMPTY"
    assert validate_report(report) == []


def test_check_engine_failure_exits_4(check_files, capsys):
    set_ocr_adapter(_FailingAdapter())
    image, expected = check_files
    code, out, err = _run_check_cli(image, expected, capsys=capsys)
    assert code == 4
    assert out == ""
    assert "OCR failed" in err


def test_check_unexpected_error_exits_5(check_files, capsys, monkeypatch):
    def _boom(**kwargs):
        raise RuntimeError("unexpected")

    monkeypatch.setattr(cli_module, "run_check", _boom)
    image, expected = check_files
    code, out, err = _run_check_cli(image, expected, capsys=capsys)
    assert code == 5
    assert out == ""
    assert "internal error" in err


# --- check: invalid input exits 3 ----------------------------------------

@pytest.mark.parametrize("mutate", [
    "missing_image",
    "garbage_image",
    "missing_expected",
    "empty_expected",
    "bad_utf8_expected",
])
def test_check_invalid_input_exits_3(tmp_path, capsys, mutate):
    image = tmp_path / "poster.png"
    image.write_bytes(ZH001_BYTES)
    expected = tmp_path / "expected.txt"
    expected.write_text("限时优惠", encoding="utf-8")
    if mutate == "missing_image":
        image.unlink()
    elif mutate == "garbage_image":
        image.write_bytes(b"not an image at all")
    elif mutate == "missing_expected":
        expected.unlink()
    elif mutate == "empty_expected":
        expected.write_text("", encoding="utf-8")
    elif mutate == "bad_utf8_expected":
        expected.write_bytes(b"\xff\xfe invalid utf-8")
    code = main(["check", "--image", str(image),
                 "--expected-file", str(expected)])
    captured = capsys.readouterr()
    assert code == 3, (mutate, captured.out, captured.err)
    assert captured.out == ""
    # No path leaks into stderr either.
    assert str(image) not in captured.err
    assert str(expected) not in captured.err


def test_check_too_long_expected_text_exits_3(check_files, tmp_path, capsys):
    image, _ = check_files
    expected = tmp_path / "long.txt"
    expected.write_text("x" * 5001, encoding="utf-8")
    code = main(["check", "--image", str(image),
                 "--expected-file", str(expected)])
    assert code == 3


def test_check_json_output_file(check_files, tmp_path, capsys):
    set_ocr_adapter(_StubAdapter([_line("限时优惠")]))
    image, expected = check_files
    out_path = tmp_path / "report.json"
    code, out, _ = _run_check_cli(
        image, expected, "--json", str(out_path), capsys=capsys)
    assert code == 0
    assert out == ""  # report goes to the file, not stdout
    report = json.loads(out_path.read_text(encoding="utf-8"))
    assert report["verdict"] == "MATCH"
    assert validate_report(report) == []


def test_check_unwritable_json_path_exits_3(check_files, capsys):
    set_ocr_adapter(_StubAdapter([_line("限时优惠")]))
    image, expected = check_files
    code = main(["check", "--image", str(image),
                 "--expected-file", str(expected),
                 "--json", str(Path("/nonexistent-dir-xyz/report.json"))])
    assert code == 3


# --- check == API (acceptance 2) ------------------------------------------

def test_check_output_matches_api(check_files, capsys):
    """CLI check and API run_check return the identical report dict."""
    set_ocr_adapter(_StubAdapter([_line("限时优")]))
    image, expected = check_files
    code, out, _ = _run_check_cli(image, expected, capsys=capsys)
    assert code == 1
    cli_report = json.loads(out)
    api_report = run_check(
        image_mime="image/png", image_base64=ZH001_B64,
        expected_text="限时优惠",
    )
    assert cli_report == api_report
    assert validate_report(cli_report) == []
    assert validate_report(api_report) == []


# --- privacy (acceptance 4) ------------------------------------------------

def test_check_output_contains_no_paths_or_base64(capsys):
    """Inputs live under the user's home dir; the JSON must not leak
    the home path, the image path, or the image bytes (base64)."""
    home = Path.home()
    workdir = Path(tempfile.mkdtemp(prefix="textproof-t009-", dir=home))
    try:
        set_ocr_adapter(_StubAdapter([_line("限时优惠")]))
        image = workdir / "poster.png"
        image.write_bytes(ZH001_BYTES)
        expected = workdir / "expected.txt"
        expected.write_text("限时优惠", encoding="utf-8")
        code, out, err = _run_check_cli(image, expected, capsys=capsys)
        assert code == 0
        assert str(home) not in out
        assert str(image) not in out
        assert str(expected) not in out
        assert ZH001_B64 not in out
        assert "image_base64" not in out
        assert str(home) not in err
    finally:
        shutil.rmtree(workdir, ignore_errors=True)


# --- schema file + frozen F-03 forms (acceptance 5) ------------------------

def test_schema_file_is_frozen_report_v1():
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    assert schema["$id"] == \
        "https://textproof.local/schemas/textproof.report.v1.schema.json"
    assert schema["properties"]["tool_version"].get("const") == "0.1.0"
    assert schema["properties"]["errors"]["items"]["properties"][
        "bbox_scope"]["enum"] == ["ocr_line", None]
    assert schema["properties"]["verdict"]["enum"] == [
        "MATCH", "MISMATCH", "REVIEW_REQUIRED", "OCR_FAILED"]


def _fixed_report(fixture_id: str) -> dict:
    from scripts.parity_check import fixed_ocr_line
    entry = next(f for f in MANIFEST["fixtures"] if f["id"] == fixture_id)
    data = (FIXTURES / entry["filename"]).read_bytes()
    return build_report(load_image(data), entry["expected_text"],
                        [fixed_ocr_line(entry)])


@pytest.mark.parametrize("case_id",
                         ["TP-S0-ZH-001", "TP-S0-ZH-002",
                          "TP-S0-NUM-001", "TP-S0-ZH-003"])
def test_s0_four_fixed_reports_pass_schema(case_id):
    report = _fixed_report(case_id)
    assert report["verdict"] == "MISMATCH"
    assert validate_report(report) == []


def _report_with_lines(expected: str, lines: list[OCRLine]) -> dict:
    return build_report(ZH001_IMAGE, expected, lines)


def test_frozen_line_error_forms_validate():
    """F-03 production forms: absent-side span null, bbox_scope null."""
    # MISSING_LINE: two expected lines, one OCR line.
    report = _report_with_lines(
        "限时优惠\n新品上市", [_line("限时优惠")])
    missing = [e for e in report["errors"] if e["type"] == "MISSING_LINE"]
    assert len(missing) == 1
    assert missing[0]["recognized_span"] is None
    assert missing[0]["bbox_xyxy"] is None
    assert missing[0]["bbox_scope"] is None
    assert missing[0]["ocr_line_index"] is None
    assert missing[0]["expected_span"] == [0, 4]
    assert validate_report(report) == []
    # EXTRA_LINE: one expected line, two OCR lines.
    extra_line = OCRLine(
        line_index=1, text="多余一行", confidence=0.99,
        bbox_xyxy=(10.0, 300.0, 500.0, 360.0),
        quad=((10.0, 300.0), (500.0, 300.0), (500.0, 360.0),
              (10.0, 360.0)),
        source_order=1,
    )
    report = _report_with_lines(
        "限时优惠", [_line("限时优惠"), extra_line])
    extra = [e for e in report["errors"] if e["type"] == "EXTRA_LINE"]
    assert len(extra) == 1
    assert extra[0]["expected_span"] is None
    assert extra[0]["expected_line_index"] is None
    assert extra[0]["bbox_scope"] == "ocr_line"
    assert validate_report(report) == []
    # AMBIGUOUS_ALIGNMENT via core compare: two identical expected
    # lines against two identical OCR lines is ambiguous.
    from textproof.core.report import compare
    result = compare("相同\n相同", [_line("相同"), extra_line])
    assert result.verdict == "REVIEW_REQUIRED"
    assert result.errors[0]["type"] == "AMBIGUOUS_ALIGNMENT"
    assert result.errors[0]["expected_span"] is None
    assert result.errors[0]["recognized_span"] is None
    assert result.errors[0]["bbox_scope"] is None
    amb_report = build_report(
        ZH001_IMAGE, "相同\n相同", [_line("相同"), extra_line])
    assert amb_report["errors"][0]["type"] == "AMBIGUOUS_ALIGNMENT"
    assert validate_report(amb_report) == []


@pytest.mark.parametrize("mutate", [
    "bbox_scope_none",
    "missing_span_00",
    "warning_confidence_field",
    "warning_line_index_on_empty",
    "tool_version_other",
])
def test_frozen_forms_reject_oracle_variants(mutate):
    """The Oracle's F-03 variants must NOT pass the frozen schema."""
    report = _report_with_lines(
        "限时优惠\n新品上市", [_line("限时优惠")])
    assert validate_report(report) == []
    missing = next(e for e in report["errors"]
                   if e["type"] == "MISSING_LINE")
    if mutate == "bbox_scope_none":
        missing["bbox_scope"] = "none"
    elif mutate == "missing_span_00":
        missing["recognized_span"] = [0, 0]
    elif mutate == "warning_confidence_field":
        report["warnings"] = [{"code": "LOW_OCR_CONFIDENCE",
                               "message": "x", "ocr_line_index": 0,
                               "confidence": 0.5}]
        report["summary"]["warning_count"] = 1
    elif mutate == "warning_line_index_on_empty":
        report["warnings"] = [{"code": "OCR_EMPTY", "message": "x",
                               "ocr_line_index": 0}]
        report["summary"]["warning_count"] = 1
    elif mutate == "tool_version_other":
        report["tool_version"] = "9.9.9"
    assert validate_report(report) != []


# --- usage errors -----------------------------------------------------------

@pytest.mark.parametrize("argv", [
    ["check"],  # missing required --image/--expected-file
    ["bogus"],
    [],
])
def test_usage_errors_exit_3_not_2(argv):
    with pytest.raises(SystemExit) as excinfo:
        main(argv)
    assert excinfo.value.code == 3


def test_help_exits_0():
    with pytest.raises(SystemExit) as excinfo:
        main(["--help"])
    assert excinfo.value.code == 0


def test_parser_defaults():
    args = build_parser().parse_args(["serve"])
    assert args.host == "127.0.0.1"
    assert args.port == 8765
    args = build_parser().parse_args(["verify-s0"])
    assert args.manifest == REPO_ROOT / "tests" / "fixtures" / "s0" / "manifest.json"
    assert args.force_live is False


# --- serve ------------------------------------------------------------------

def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def test_serve_rejects_non_loopback_host():
    assert main(["serve", "--host", "0.0.0.0", "--port", "8765"]) == 3


def test_serve_real_loopback_server():
    """Real `textproof serve` subprocess on 127.0.0.1; health answers."""
    port = _free_port()
    env = dict(os.environ, PYTHONPATH=str(REPO_ROOT / "src"))
    proc = subprocess.Popen(
        [sys.executable, "-m", "textproof.cli", "serve", "--port", str(port)],
        cwd=REPO_ROOT, env=env,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
    )
    try:
        deadline = time.monotonic() + 60
        body = None
        while time.monotonic() < deadline:
            try:
                with urllib.request.urlopen(
                        f"http://127.0.0.1:{port}/api/v1/health",
                        timeout=5) as resp:
                    assert resp.status == 200
                    body = json.loads(resp.read())
                    break
            except (urllib.error.URLError, ConnectionError):
                time.sleep(0.2)
        assert body is not None, "serve did not come up in 60s"
        assert body["status"] == "ok"
        assert body["tool_version"] == "0.1.0"
        with urllib.request.urlopen(
                f"http://127.0.0.1:{port}/api/v1/version",
                timeout=5) as resp:
            version = json.loads(resp.read())
        assert version["rapidocr_version"] == "3.10.0"
        assert version["providers"] == ["CPUExecutionProvider"]
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=15)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=10)


# --- verify-s0 (thin wrapper; logic lives in scripts/verify_s0.py) --------

def test_verify_s0_delegates_and_passes_exit_code(monkeypatch):
    seen: dict = {}

    class _Done:
        returncode = 0

    def fake_run(cmd, check=False):
        seen["cmd"] = cmd
        return _Done()

    monkeypatch.setattr(cli_module.subprocess, "run", fake_run)
    assert main(["verify-s0"]) == 0
    cmd = seen["cmd"]
    assert cmd[1].endswith("scripts/verify_s0.py")
    assert "--manifest" in cmd
    assert str(FIXTURES / "manifest.json") in cmd
    assert "--force-live" not in cmd


def test_verify_s0_forwards_flags_and_nonzero_exit(monkeypatch, tmp_path):
    class _Done:
        returncode = 1

    def fake_run(cmd, check=False):
        assert "--force-live" in cmd
        assert "--out-dir" in cmd
        return _Done()

    monkeypatch.setattr(cli_module.subprocess, "run", fake_run)
    code = main(["verify-s0", "--force-live",
                 "--out-dir", str(tmp_path)])
    assert code == 1


def test_verify_s0_missing_manifest_exits_3(monkeypatch, tmp_path):
    called = []

    def fake_run(cmd, check=False):
        called.append(cmd)
        raise AssertionError("must not spawn verify_s0")

    monkeypatch.setattr(cli_module.subprocess, "run", fake_run)
    code = main(["verify-s0", "--manifest", str(tmp_path / "nope.json")])
    assert code == 3
    assert called == []


# --- real OCR end to end (subprocess, no stub) ------------------------------

def test_check_real_ocr_subprocess(tmp_path):
    """`textproof check` with the real engine on the S0 ZH-001 PNG."""
    image = tmp_path / "poster.png"
    image.write_bytes(ZH001_BYTES)
    expected = tmp_path / "expected.txt"
    expected.write_text("限时优惠", encoding="utf-8")
    out_path = tmp_path / "report.json"
    env = dict(os.environ, PYTHONPATH=str(REPO_ROOT / "src"))
    result = subprocess.run(
        [sys.executable, "-m", "textproof.cli", "check",
         "--image", str(image), "--expected-file", str(expected),
         "--json", str(out_path)],
        capture_output=True, text=True, cwd=REPO_ROOT, env=env, timeout=300,
    )
    assert result.returncode in (0, 1), result.stderr
    report = json.loads(out_path.read_text(encoding="utf-8"))
    assert report["schema"] == "textproof.report/v1"
    assert validate_report(report) == []
    assert str(tmp_path) not in json.dumps(report, ensure_ascii=False)
