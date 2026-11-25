"""T010 acceptance 1/4 (syscall half): strace the real CLI check.

``strace -f -e trace=openat,connect`` watches the whole process
tree of one live-OCR CLI check and proves, at the syscall level:

* **zero ``connect()`` calls** — the process never even attempts a
  network connection (stronger than "no request succeeded");
* **no file creation outside ``__pycache__``** — the only
  ``O_CREAT`` opens are Python bytecode caches; in particular no
  image/temp/database file is created anywhere, including the ONNX
  Runtime telemetry outbox (see F-T010-02: fixed by
  ``ORT_DISABLE_TELEMETRY=1``; the cache dir is pointed at a fresh
  temp dir here so any telemetry write would show up).

Skipped (not faked) when ``strace`` is unavailable.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from t010_offline_helpers import (
    REPO_ROOT,
    STRACE,
    evidence_dir,
    fixture_path,
    product_env,
)

_OPENAT_RE = re.compile(r"openat\(AT_FDCWD, \"([^\"]+)\", ([^)]*)\)")


@pytest.mark.skipif(STRACE is None, reason="strace(1) is not installed")
def test_strace_cli_check_no_connect_no_file_creation(tmp_path):
    expected = tmp_path / "expected.txt"
    expected.write_text("限时优惠", encoding="utf-8")
    cache_dir = tmp_path / "xdg-cache"
    cache_dir.mkdir()
    strace_log = tmp_path / "strace.log"
    env = product_env({"XDG_CACHE_HOME": str(cache_dir)})
    env.pop("ORT_DISABLE_TELEMETRY", None)
    completed = subprocess.run(
        [STRACE, "-f", "-e", "trace=openat,connect",
         "-o", str(strace_log),
         sys.executable, "-m", "textproof.cli", "check",
         "--image", str(fixture_path("TP-S0-ZH-001")),
         "--expected-file", str(expected)],
        cwd=REPO_ROOT, env=env,
        capture_output=True, text=True, timeout=600)
    assert completed.returncode == 1, (
        f"CLI check rc={completed.returncode}: "
        f"{completed.stdout[:300]}{completed.stderr[:300]}")
    assert json.loads(completed.stdout)["verdict"] == "MISMATCH"
    out = evidence_dir()
    if out is not None:
        shutil.copyfile(strace_log, out / "strace_cli_check.log")

    lines = strace_log.read_text(encoding="utf-8").splitlines()
    assert len(lines) > 500, (
        f"strace log implausibly short ({len(lines)} lines) — "
        "tracing may not have worked")

    connects = [ln for ln in lines if "connect(" in ln]
    assert connects == [], (
        f"{len(connects)} connect() syscall(s) during a CLI check: "
        f"{connects[:3]}")

    created: list[str] = []
    for ln in lines:
        if "O_CREAT" not in ln:
            continue
        match = _OPENAT_RE.search(ln)
        if not match:
            continue
        path = match.group(1)
        if "__pycache__" in path or path.endswith(".pyc"):
            continue
        created.append(path)
    assert created == [], (
        f"file(s) created outside __pycache__ during a check: {created}")

    leftovers = [p for p in cache_dir.rglob("*")]
    assert leftovers == [], (
        f"files created under fresh XDG_CACHE_HOME: {leftovers}")
