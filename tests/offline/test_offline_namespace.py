"""T010 acceptance 1 (offline half): the product works with no network
namespace at all, and the namespace is proven to be really isolated
(an external connect attempt fails inside it).

Paths covered under ``unshare -n``:

* CLI ``check`` — live OCR, real fixture, exit 1 (MISMATCH).
* ``serve`` — real uvicorn started *inside* the namespace; its
  LISTEN socket is proven to be 127.0.0.1-only from the kernel
  table there.  No live HTTP check inside the namespace: its
  loopback stays DOWN (no CAP_NET_ADMIN) — see the isolation test.
* ``verify-s0`` — the S0 gate script with the committed cached
  live-OCR results (300 records); exit 0, ``S0 VERDICT: PASS``.
  The ``--force-live`` variant is deliberately NOT run here: it
  re-runs live OCR over all 300 fixtures (~11 min) and is covered
  by T006 / the main-chat verdict instead.
"""

from __future__ import annotations

import json
import shutil
import socket
from pathlib import Path

import pytest

from t010_offline_helpers import (
    REPO_ROOT,
    VENV_PYTHON,
    evidence_dir,
    fixture_path,
    product_env,
    run_under_unshare,
)


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def test_namespace_is_really_isolated(unshare_available):
    """Inside unshare -n: no route, no external connect, no loopback.

    This is the control that makes the other tests meaningful: if
    the namespace were not isolated, a passing offline run would
    prove nothing.  Two environment facts, verified 2026-11-25:

    * ``/sys/class/net`` is NOT network-namespace aware on this VM
      (it lists the parent's ``host0`` inside the namespace), so it
      must not be used as evidence; ``/proc/net/route`` and
      ``/proc/net/tcp`` ARE namespace-aware and are used instead.
    * ``unshare -n`` here grants no ``CAP_NET_ADMIN``: the
      namespace's loopback stays DOWN and cannot be brought up, so
      even a 127.0.0.1 connect fails.  The namespace therefore has
      NO usable networking at all — stronger isolation than a
      normal namespace, and the reason the serve test below can
      only prove bind (not a live HTTP check) inside it.
    """
    probe = (
        "import socket, sys\n"
        "routes = open('/proc/net/route').read().splitlines()[1:]\n"
        "assert routes == [], f'routes present inside namespace: {routes}'\n"
        "for host, port in (('8.8.8.8', 53), ('127.0.0.1', 59999)):\n"
        "    s = socket.socket()\n"
        "    s.settimeout(3)\n"
        "    try:\n"
        "        s.connect((host, port))\n"
        "        print(f'UNEXPECTED: connect to {host} succeeded')\n"
        "        sys.exit(9)\n"
        "    except OSError as e:\n"
        "        print(f'connect to {host} failed as expected: {e}')\n"
        "    finally:\n"
        "        s.close()\n"
    )
    completed = run_under_unshare(
        [VENV_PYTHON, "-c", probe],
        capture_output=True, text=True, timeout=60)
    assert completed.returncode == 0, (
        f"namespace isolation probe failed: {completed.stdout}"
        f"{completed.stderr}")
    assert "failed as expected" in completed.stdout


def test_cli_check_under_unshare(unshare_available, tmp_path):
    """CLI check completes with no network namespace (live OCR)."""
    expected = tmp_path / "expected.txt"
    expected.write_text("限时优惠", encoding="utf-8")
    completed = run_under_unshare(
        [VENV_PYTHON, "-m", "textproof.cli", "check",
         "--image", str(fixture_path("TP-S0-ZH-001")),
         "--expected-file", str(expected)],
        cwd=REPO_ROOT, env=product_env(),
        capture_output=True, text=True, timeout=600)
    assert completed.returncode == 1, (
        f"CLI check rc={completed.returncode}: "
        f"{completed.stdout[:500]}{completed.stderr[:500]}")
    report = json.loads(completed.stdout)
    assert report["verdict"] == "MISMATCH"
    assert report["expected_text"] == "限时优惠"
    assert report["recognized_text"] == "限时优"
    assert completed.stderr == "", (
        f"CLI check wrote to stderr: {completed.stderr[:500]!r}")


def test_serve_under_unshare(unshare_available, tmp_path):
    """serve binds loopback-only inside the namespace (bind proof).

    A live HTTP check inside the namespace is impossible here: the
    namespace's loopback stays DOWN (no CAP_NET_ADMIN to bring it
    up — see ``test_namespace_is_really_isolated``).  The probe
    therefore proves the strongest check available there: the
    server starts, stays alive, and its only LISTEN socket is
    127.0.0.1:<port> (kernel table, inside the namespace).  The
    HTTP half is covered by the live-server tests in tests/privacy/.
    """
    probe = Path(__file__).resolve().parent / "_serve_probe.py"
    log_file = tmp_path / "serve_probe.log"
    completed = run_under_unshare(
        [VENV_PYTHON, str(probe),
         "--port", str(_free_port()),
         "--log-file", str(log_file)],
        cwd=REPO_ROOT, env=product_env(),
        capture_output=True, text=True, timeout=300)
    assert completed.returncode == 0, (
        f"serve probe rc={completed.returncode}: "
        f"{completed.stdout[-2000:]}{completed.stderr[-2000:]}")
    assert "SERVE_PROBE_PASS" in completed.stdout


def test_verify_s0_cached_under_unshare(unshare_available, tmp_path):
    """verify-s0 (cached live results) passes with no network."""
    out_dir = tmp_path / "s0"
    out_dir.mkdir()
    shutil.copyfile(
        REPO_ROOT / "task_handoffs" / "T006" / "live_ocr_results.jsonl",
        out_dir / "live_ocr_results.jsonl",
    )
    completed = run_under_unshare(
        [VENV_PYTHON, "scripts/verify_s0.py",
         "--manifest", "tests/fixtures/s0/manifest.json",
         "--out-dir", str(out_dir)],
        cwd=REPO_ROOT, env=product_env(),
        capture_output=True, text=True, timeout=600)
    assert completed.returncode == 0, (
        f"verify-s0 rc={completed.returncode}: "
        f"{completed.stdout[-2000:]}{completed.stderr[-2000:]}")
    assert "reusing cached live OCR results" in completed.stdout
    assert "S0 VERDICT: PASS" in completed.stdout
    out = evidence_dir()
    if out is not None:
        (out / "verify_s0_offline_stdout.log").write_text(
            completed.stdout, encoding="utf-8")
