"""T010 finding F-T010-02 regression test: ONNX Runtime telemetry.

ONNX Runtime 1.32.0 official builds ship with 1DS telemetry ON by
default.  Before the fix, one CLI check created a persistent device
identifier plus a SQLite telemetry outbox
(``~/.cache/Microsoft/DeveloperTools/.onnxruntime/onnxruntime.db``)
with 5 queued events (SessionCreation, SessionCreationEnd,
ProcessInfo, EpDeviceUsage, ModelLoadEnd) — environment/session
metadata only, no image bytes, expected text or OCR text (payloads
decoded in the T010 investigation), and no upload was observed
(0 ``connect()`` calls under strace).  Even so, a telemetry outbox
violates PROJECT_BOOK.md §9 ("不写数据库、不调用遥测、不发外部
HTTP 请求").

The fix (``src/textproof/ocr/rapidocr_adapter.py``) sets
``ORT_DISABLE_TELEMETRY=1`` at import time, before ONNX Runtime
can initialize — the documented runtime opt-out.  This test proves
it from the outside: a fresh cache directory stays completely
empty after a real CLI check, with no ``ORT_DISABLE_TELEMETRY`` in
the subprocess environment (so the product, not the shell, does
the disabling), and OCR still works.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from t010_privacy_helpers import REPO_ROOT, fixture_path


def test_adapter_disables_ort_telemetry_at_import():
    import textproof.ocr.rapidocr_adapter as adapter_mod

    assert os.environ.get("ORT_DISABLE_TELEMETRY") == "1", (
        "importing the OCR adapter must set ORT_DISABLE_TELEMETRY=1 "
        "before ONNX Runtime initializes")


def test_cli_check_creates_no_telemetry_files(tmp_path):
    """Real CLI check, fresh cache: no deviceid, no telemetry db."""
    cache_dir = tmp_path / "xdg-cache"
    cache_dir.mkdir()
    expected = tmp_path / "expected.txt"
    expected.write_text("限时优惠", encoding="utf-8")
    env = dict(os.environ)
    env["PYTHONPATH"] = str(REPO_ROOT / "src") + os.pathsep + \
        env.get("PYTHONPATH", "")
    env["XDG_CACHE_HOME"] = str(cache_dir)
    env.pop("ORT_DISABLE_TELEMETRY", None)  # the product must do it
    completed = subprocess.run(
        [sys.executable, "-m", "textproof.cli", "check",
         "--image", str(fixture_path("TP-S0-ZH-001")),
         "--expected-file", str(expected)],
        cwd=REPO_ROOT, env=env,
        capture_output=True, text=True, timeout=600)
    assert completed.returncode == 1, (
        f"CLI check rc={completed.returncode}: "
        f"{completed.stdout[:300]}{completed.stderr[:300]}")
    report = json.loads(completed.stdout)
    assert report["verdict"] == "MISMATCH"  # OCR still works
    leftovers = [p for p in cache_dir.rglob("*")]
    assert leftovers == [], (
        f"telemetry/cache files created under fresh XDG_CACHE_HOME: "
        f"{leftovers}")
