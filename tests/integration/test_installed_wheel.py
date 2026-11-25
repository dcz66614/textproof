"""Regression tests for T013-U01: the installed wheel must run standalone.

T014's offline-install smoke test found the installed wheel could not
run ``check`` (exit 5, "validator unavailable"), ``serve`` (crash:
``textproof/ui`` missing from the wheel) or ``verify-s0`` (missing
``scripts/verify_s0.py``) — because the validator, the UI and the OCR
assets were all resolved relative to a source checkout that does not
exist in an installed layout.  The fix moves the validator and the
dictionary rebuild into the package, ships the UI and the frozen ONNX
models as package data, and gives ``verify-s0`` a defined installed
behaviour (exit 3, "requires a source checkout").

These tests lock that fix at both levels:

* unit level — the packaged validator agrees with the script wrapper,
  the packaged model copies are byte-identical to the checkout files,
  the adapter still prefers checkout assets in a source tree, and the
  installed ``verify-s0`` refusal is exit 3;
* end-to-end level — :func:`test_installed_wheel_offline_smoke`
  builds a wheel from this working tree, installs it offline from the
  release wheelhouse into a fresh venv (no checkout on the path), runs
  the in-wheel dictionary rebuild, and then runs ``check`` (exit 1,
  ``MISMATCH``), ``serve`` (health + UI) and ``verify-s0`` (exit 3)
  against the installed tool.

No network is used anywhere: the wheel build runs with
``--no-isolation`` and the install with ``--no-index`` against the
local wheelhouse.  The end-to-end test is slow (fresh venv + offline
install + real OCR, roughly two minutes) and is the point of this
file — do not "speed it up" by stubbing the engine or by putting the
checkout on the path, or it stops testing the installed layout.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURES = REPO_ROOT / "tests" / "fixtures" / "s0"
WHEELHOUSE = REPO_ROOT / "release" / "wheelhouse"

sys.path.insert(0, str(REPO_ROOT))

from scripts.validate_report_schema import (  # noqa: E402
    validate_report as script_validate_report,
)
from textproof import cli as cli_module  # noqa: E402
from textproof.cli import main  # noqa: E402
from textproof.core.report_schema import (  # noqa: E402
    validate_report as package_validate_report,
)
from textproof.ocr.rapidocr_adapter import (  # noqa: E402
    MODEL_FILES,
    default_assets_dir,
)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _valid_report(**overrides):
    report = {
        "schema": "textproof.report/v1",
        "tool_version": "0.1.0",
        "verdict": "MATCH",
        "image": {
            "sha256": "0" * 64,
            "format": "PNG",
            "width": 100,
            "height": 20,
            "coordinate_system": "oriented_image_px_top_left",
        },
        "expected_text": "ab",
        "recognized_text": "ab",
        "ocr_lines": [],
        "errors": [],
        "warnings": [],
        "summary": {
            "expected_lines": 1,
            "ocr_lines": 0,
            "error_count": 0,
            "warning_count": 0,
        },
    }
    report.update(overrides)
    return report


# --- unit level -----------------------------------------------------------

def test_package_validator_agrees_with_script_wrapper():
    """The in-package validator and the script wrapper are one rule."""
    assert package_validate_report(_valid_report()) == []
    assert script_validate_report(_valid_report()) == []
    bad = _valid_report(verdict="NOPE")
    assert package_validate_report(bad) != []
    assert script_validate_report(bad) != []
    assert package_validate_report(bad) == script_validate_report(bad)


def test_default_assets_dir_prefers_checkout_in_source_tree():
    """In a source tree the checkout assets still win (unchanged)."""
    assert default_assets_dir() == REPO_ROOT / "assets" / "ocr"


def test_packaged_model_copies_match_checkout():
    """Wheel model copies are verbatim: same bytes, frozen hashes."""
    packaged = REPO_ROOT / "src" / "textproof" / "assets" / "ocr" / "models"
    checkout = REPO_ROOT / "assets" / "ocr" / "models"
    for name, _url, sha256, _key in MODEL_FILES:
        packed = packaged / name
        assert packed.is_file(), f"missing packaged model copy: {name}"
        assert _sha256_file(packed) == sha256, f"hash mismatch: {name}"
        assert _sha256_file(packed) == _sha256_file(checkout / name), (
            f"packaged copy drifted from checkout: {name}")


def test_verify_s0_installed_layout_exits_3(monkeypatch, tmp_path, capsys):
    """No S0 runner (installed layout): defined exit 3, never a crash."""
    monkeypatch.setattr(cli_module, "_find_verify_s0_script",
                        lambda: None)
    manifest = tmp_path / "manifest.json"
    manifest.write_text("{}", encoding="utf-8")
    assert main(["verify-s0", "--manifest", str(manifest)]) == 3
    assert "source checkout" in capsys.readouterr().err


def test_verify_s0_default_manifest_installed_layout(monkeypatch, capsys):
    """Same refusal with the default manifest (it exists in a checkout)."""
    monkeypatch.setattr(cli_module, "_find_verify_s0_script",
                        lambda: None)
    assert main(["verify-s0"]) == 3
    assert "source checkout" in capsys.readouterr().err


# --- end to end: fresh venv, offline wheel install, no checkout ----------

def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def _clean_env(tmpdir: Path) -> dict[str, str]:
    """Child env with no checkout on the path and no network use."""
    env = dict(os.environ)
    env.pop("PYTHONPATH", None)
    env["TMPDIR"] = str(tmpdir)
    env["PIP_DISABLE_PIP_VERSION_CHECK"] = "1"
    return env


def _run(argv: list[str], env: dict[str, str], timeout: int,
         cwd: str | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        argv, capture_output=True, text=True, env=env, timeout=timeout,
        cwd=cwd)


def _poll_health(port: int, deadline: float) -> dict:
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(
                    f"http://127.0.0.1:{port}/api/v1/health",
                    timeout=5) as resp:
                assert resp.status == 200
                return json.loads(resp.read())
        except (urllib.error.URLError, ConnectionError):
            time.sleep(0.5)
    raise AssertionError("installed serve did not come up in 60s")


def test_installed_wheel_offline_smoke(tmp_path):
    """Build the wheel, install it offline, run check + serve + verify-s0."""
    work = tmp_path / "work"
    tmpdir = work / "tmp"
    tmpdir.mkdir(parents=True)

    # 1. Build the wheel from a scratch copy of the source tree, so the
    #    build cannot pollute the worktree and cannot see the checkout.
    build_src = work / "build-src"
    (build_src / "src").mkdir(parents=True)
    shutil.copy(REPO_ROOT / "pyproject.toml", build_src / "pyproject.toml")
    shutil.copy(REPO_ROOT / "LICENSE", build_src / "LICENSE")
    shutil.copytree(REPO_ROOT / "src" / "textproof",
                    build_src / "src" / "textproof")
    env = _clean_env(tmpdir)
    built = _run(
        [sys.executable, "-m", "build", "--wheel", "--no-isolation",
         "--outdir", str(work / "dist")],
        env, timeout=300, cwd=str(build_src))
    assert built.returncode == 0, built.stderr[-2000:]
    wheels = sorted((work / "dist").glob("textproof-*.whl"))
    assert len(wheels) == 1, f"expected one wheel, got {wheels}"
    wheel = wheels[0]

    # 2. The wheel ships the UI, the models and the validator — and no
    #    dictionary (licence UNVERIFIED, THIRD_PARTY_NOTICES.md §4).
    with zipfile.ZipFile(wheel) as zf:
        names = zf.namelist()
    for needed in ("textproof/ui/index.html", "textproof/ui/app.js",
                   "textproof/ui/style.css",
                   "textproof/core/report_schema.py",
                   "textproof/setup_dictionary.py",
                   "textproof/assets/ocr/models/PP-OCRv6_det_small.onnx",
                   "textproof/assets/ocr/models/PP-OCRv6_rec_small.onnx",
                   "textproof/assets/ocr/models/"
                   "ch_ppocr_mobile_v2.0_cls_mobile.onnx"):
        assert needed in names, f"missing from wheel: {needed}"
    assert not [n for n in names if "ppocrv6_dict" in n], (
        "dictionary file present in wheel")

    # 3. Fresh venv, offline install from the release wheelhouse.
    venv = work / "venv"
    created = _run([sys.executable, "-m", "venv", str(venv)], env, 300)
    assert created.returncode == 0, created.stderr[-2000:]
    venv_python = venv / "bin" / "python"
    venv_textproof = venv / "bin" / "textproof"
    assert WHEELHOUSE.is_dir(), "release/wheelhouse missing"
    installed = _run(
        [str(venv_python), "-m", "pip", "install", "--no-index",
         "--find-links", str(WHEELHOUSE), str(wheel)],
        env, timeout=600)
    assert installed.returncode == 0, installed.stderr[-2000:]
    assert "Successfully installed" in installed.stdout

    # 4. The installed tool answers --help / version on its own.
    version = _run([str(venv_textproof), "version"], env, timeout=120)
    assert version.returncode == 0, version.stderr
    info = json.loads(version.stdout)
    assert info["tool_version"] == "0.1.0"
    assert info["package_version"] == "1.0.0"
    assert info["spec_version"] == "1.0.0"

    # 5. Rebuild the dictionary inside the installed package, then
    #    check TP-S0-ZH-001 against "限时优惠": exit 1, MISMATCH.
    rebuilt = _run(
        [str(venv_python), "-m", "textproof.setup_dictionary"],
        env, timeout=300)
    assert rebuilt.returncode == 0, rebuilt.stderr[-2000:]
    assert "18,708" in rebuilt.stdout or "18708" in rebuilt.stdout, (
        rebuilt.stdout)
    image = work / "poster.png"
    manifest = json.loads((FIXTURES / "manifest.json").read_text(
        encoding="utf-8"))
    zh001 = next(f for f in manifest["fixtures"] if f["id"] == "TP-S0-ZH-001")
    image.write_bytes((FIXTURES / zh001["filename"]).read_bytes())
    expected = work / "expected.txt"
    expected.write_text("限时优惠", encoding="utf-8")
    report_path = work / "report.json"
    checked = _run(
        [str(venv_textproof), "check", "--image", str(image),
         "--expected-file", str(expected), "--json", str(report_path)],
        env, timeout=300)
    assert checked.returncode == 1, checked.stderr
    assert report_path.is_file(), "installed check produced no report"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["verdict"] == "MISMATCH"
    assert report["schema"] == "textproof.report/v1"
    assert script_validate_report(report) == []
    assert str(work) not in json.dumps(report, ensure_ascii=False)

    # 6. Serve from the installed wheel: health + the UI page.
    port = _free_port()
    proc = subprocess.Popen(
        [str(venv_textproof), "serve", "--port", str(port)],
        env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True)
    try:
        body = _poll_health(port, time.monotonic() + 60)
        assert body["status"] == "ok"
        assert body["tool_version"] == "0.1.0"
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/",
                                    timeout=10) as resp:
            assert resp.status == 200
            html = resp.read().decode("utf-8")
        assert "TextProof" in html
        assert "可能包含敏感文字" in html
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=15)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=10)

    # 7. verify-s0 in the installed layout: defined exit 3, both ways.
    no_manifest = _run([str(venv_textproof), "verify-s0"], env, timeout=120)
    assert no_manifest.returncode == 3
    assert "S0 manifest not found" in no_manifest.stderr
    with_manifest = _run(
        [str(venv_textproof), "verify-s0", "--manifest",
         str(FIXTURES / "manifest.json")],
        env, timeout=120)
    assert with_manifest.returncode == 3
    assert "source checkout" in with_manifest.stderr
