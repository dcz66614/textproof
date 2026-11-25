"""Shared helpers for the T010 offline tests (PROJECT_BOOK.md §9).

The offline tests run the real product inside a network namespace
with no interfaces except loopback (``unshare -n``).  That is the
strongest form of the "zero external requests" claim: there is no
network to reach at all, yet CLI check, serve + UI, and verify-s0
(with cached live results) all complete.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURES = REPO_ROOT / "tests" / "fixtures" / "s0"
MANIFEST = json.loads((FIXTURES / "manifest.json").read_text(encoding="utf-8"))
VENV_PYTHON = sys.executable  # the venv python running pytest

UNSHARE = shutil.which("unshare")
STRACE = shutil.which("strace")


def fixture_record(fixture_id: str) -> dict:
    return next(f for f in MANIFEST["fixtures"] if f["id"] == fixture_id)


def fixture_path(fixture_id: str) -> Path:
    return FIXTURES / fixture_record(fixture_id)["filename"]


def product_env(extra: dict[str, str] | None = None) -> dict[str, str]:
    """Env for running the product out-of-process: ``src/`` on path."""
    env = dict(os.environ)
    src = str(REPO_ROOT / "src")
    env["PYTHONPATH"] = src + os.pathsep + env.get("PYTHONPATH", "")
    env.pop("TEXTPROOF_PRIVACY_EVIDENCE_DIR", None)
    if extra:
        env.update(extra)
    return env


def run_under_unshare(argv: list[str], **kwargs) -> subprocess.CompletedProcess:
    """Run *argv* inside ``unshare -n`` (network namespace, lo only)."""
    return subprocess.run(
        [UNSHARE, "-n", "--", *argv], **kwargs)


def evidence_dir() -> Path | None:
    raw = os.environ.get("TEXTPROOF_PRIVACY_EVIDENCE_DIR", "")
    if not raw:
        return None
    path = Path(raw)
    path.mkdir(parents=True, exist_ok=True)
    return path


