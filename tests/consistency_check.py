"""API / CLI / UI three-way JSON consistency check for P033 (T011).

Acceptance 5 of the T011 card: the same input through the API, the
CLI and the real browser UI must produce semantically identical JSON
reports.  Two inputs are checked:

* ``TP-S0-ZH-002`` — an S0 fixed sample (substitution, MISMATCH);
* the first clean fixture in the manifest (expected == drawn, MATCH).

Paths (all live, no stubs):

* API — a real uvicorn server on 127.0.0.1 (same pattern as
  ``tests/e2e/conftest.py``), ``POST /api/v1/check``.
* CLI — the real ``textproof check`` entry point in a subprocess
  (``--json`` output file; exit 1 for MISMATCH is expected, not a
  failure of this script).
* UI — a real headless Chrome driven over CDP (``tests/e2e/cdp.py``):
  file input + expected text + real mouse clicks on ``#btn-check`` /
  ``#btn-download``, reading the downloaded ``textproof-report.json``.

Comparison is on the parsed JSON dicts (key order ignored), field by
field; any difference is listed with a JSON path.  The report is
fully deterministic (no timestamps / UUIDs — see
``src/textproof/core/report.py``), so exact equality is the bar.

Fixture-text notice: this script only ever runs against the
committed S0 synthetic fixtures in ``tests/fixtures/s0/``.  Its
outputs — stdout, the per-case JSON reports and the summary JSON —
contain fixture expected/drawn text and full fixture reports.  It
must never be pointed at real user images: do not reuse it for
real user data, and treat every file it writes as fixture evidence
only.  Shared scratch files (``expected.txt`` and the shared
download name) are deleted when the run finishes; only the
per-case ``<kind>-<case>.json`` evidence files are kept, each
recorded with its SHA-256 in the summary JSON.

Loopback only: every HTTP call in this script targets the
``LiveServer`` on ``http://127.0.0.1:<port>``.  ``_http_post`` and
``_http_get`` assert that their ``base`` starts with
``http://127.0.0.1:`` and refuse anything else, so the helpers
cannot be reused against an external host.

Location note (T013, R-02): this script lives in ``tests/``,
outside the T010 privacy scan tree (``src/**/*.py`` +
``scripts/*.py``), because it legitimately uses the loopback HTTP
client for the API leg.  It must not be moved back to ``scripts/``.

Usage::

    python tests/consistency_check.py --manifest tests/fixtures/s0/manifest.json \
        --out task_handoffs/T013/consistency/consistency_report.json

Exit code 0 iff both inputs agree exactly across all three paths.
"""

from __future__ import annotations

import argparse
import asyncio
import base64
import hashlib
import json
import socket
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "tests" / "e2e"))

import uvicorn  # noqa: E402
from cdp import Chrome, navigate_fresh  # noqa: E402

from textproof.api.app import create_app  # noqa: E402

FIXTURES = REPO_ROOT / "tests" / "fixtures" / "s0"
CHECK_TIMEOUT = 300.0


def _require_loopback(base: str) -> None:
    """Refuse any HTTP target that is not our own loopback server."""
    assert isinstance(base, str) and base.startswith("http://127.0.0.1:"), (
        f"refusing non-loopback HTTP base: {base!r}")


def _sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _write_case_report(workdir: Path, kind: str, case_id: str,
                       raw: bytes) -> tuple[Path, str]:
    """Store one leg's report as ``<kind>-<case_id>.json`` + SHA-256.

    Per-case filenames (R-06): earlier runs shared one
    ``cli-report.json`` across cases, so the second case overwrote
    the first and its IDENTICAL verdict could not be re-checked from
    the retained files.  Each leg of each case now keeps its own
    file, and the summary JSON records every file's SHA-256.
    """
    path = workdir / f"{kind}-{case_id}.json"
    path.write_bytes(raw)
    return path, _sha256_bytes(raw)


def _cleanup_scratch(workdir: Path, download_dir: Path) -> None:
    """Delete shared scratch files; per-case evidence files stay.

    R-08: ``expected.txt`` (fixture expected text) and the shared
    ``cli-report.json`` / downloaded ``textproof-report.json`` names
    are scratch, not evidence — the retained evidence is the
    per-case ``<kind>-<case>.json`` files.  Missing files are fine.
    """
    for path in (workdir / "expected.txt",
                 workdir / "cli-report.json",
                 download_dir / "textproof-report.json"):
        path.unlink(missing_ok=True)


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def _http_post(base: str, path: str, payload: dict) -> tuple[int, bytes]:
    _require_loopback(base)
    req = urllib.request.Request(
        base + path,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=CHECK_TIMEOUT) as resp:
            return resp.status, resp.read()
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read()


def _http_get(base: str, path: str) -> int:
    _require_loopback(base)
    req = urllib.request.Request(base + path)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status
    except urllib.error.HTTPError as exc:
        return exc.code


class LiveServer:
    """Real uvicorn server on 127.0.0.1; context manager."""

    def __enter__(self) -> str:
        self.port = _free_port()
        self.server = uvicorn.Server(uvicorn.Config(
            create_app(), host="127.0.0.1", port=self.port, log_level="error"))
        self.thread = threading.Thread(
            target=asyncio.run, args=(self.server.serve(),), daemon=True)
        self.thread.start()
        base = f"http://127.0.0.1:{self.port}"
        deadline = time.monotonic() + 60
        first_error: BaseException | None = None
        last_error: BaseException | None = None
        while True:
            try:
                if _http_get(base, "/api/v1/health") == 200:
                    break
            except Exception as exc:  # R-07: record, then retry.
                # Readiness failures are connection errors while the
                # server is still starting; record the first one on
                # stderr (once) and keep the latest for the timeout
                # message instead of silently swallowing them.
                last_error = exc
                if first_error is None:
                    first_error = exc
                    print(f"  live server not ready yet "
                          f"({type(exc).__name__}: {exc}), retrying...",
                          file=sys.stderr)
            if time.monotonic() > deadline:
                raise RuntimeError(
                    "live server did not come up in 60s; last error: "
                    f"{type(last_error).__name__}: {last_error}")
            time.sleep(0.2)
        return base

    def __exit__(self, *exc) -> None:
        self.server.should_exit = True
        self.thread.join(timeout=15)


def api_check(base: str, image_path: Path, expected_text: str,
              workdir: Path, case_id: str) -> tuple[dict, str]:
    payload = {
        "image_mime": "image/png",
        "image_base64": base64.b64encode(image_path.read_bytes()).decode("ascii"),
        "expected_text": expected_text,
    }
    status, body = _http_post(base, "/api/v1/check", payload)
    if status != 200:
        raise RuntimeError(f"API check failed: HTTP {status}: {body[:500]!r}")
    _, sha = _write_case_report(workdir, "api", case_id, body)
    return json.loads(body.decode("utf-8")), sha


def cli_check(image_path: Path, expected_text: str, workdir: Path,
              case_id: str) -> tuple[dict, str]:
    expected_file = workdir / "expected.txt"
    expected_file.write_text(expected_text, encoding="utf-8")
    out_json = workdir / f"cli-{case_id}.json"
    cmd = [sys.executable, "-m", "textproof.cli", "check",
           "--image", str(image_path),
           "--expected-file", str(expected_file),
           "--json", str(out_json)]
    import os  # noqa: PLC0415
    env = dict(os.environ)
    # The package is not installed in the venv; tests run against the
    # worktree sources (root conftest.py does the same for pytest).
    env["PYTHONPATH"] = str(REPO_ROOT / "src")
    proc = subprocess.run(cmd, capture_output=True, text=True,
                          cwd=str(REPO_ROOT), timeout=600, env=env)
    # Exit codes (§5.5): 0 MATCH, 1 MISMATCH, 2 REVIEW_REQUIRED,
    # 4 OCR_FAILED; anything else is a CLI failure.
    if proc.returncode not in (0, 1, 2, 4):
        raise RuntimeError(
            f"CLI check failed: exit {proc.returncode}\n"
            f"stdout: {proc.stdout}\nstderr: {proc.stderr}")
    raw = out_json.read_bytes()
    return json.loads(raw.decode("utf-8")), _sha256_bytes(raw)


def ui_check(page, base: str, image_path: Path, expected_text: str,
             download_dir: Path, workdir: Path,
             case_id: str) -> tuple[dict, str]:
    for old in download_dir.glob("textproof-report.json"):
        old.unlink()
    navigate_fresh(page, base)
    page.set_file_input("#file-input", str(image_path))
    page.set_textarea("#expected-text", expected_text)
    page.wait_for("document.querySelector('#btn-check').disabled === false",
                  timeout=30, desc="check button to enable")
    time.sleep(0.5)  # FileReader (base64) + preview load, as in the e2e test
    page.click("#btn-check")
    page.wait_for(
        "document.querySelector('#verdict').textContent.indexOf('尚未核对') === -1",
        timeout=CHECK_TIMEOUT, desc="verdict to appear")
    page.wait_for("document.querySelector('#btn-download').disabled === false",
                  timeout=10, desc="download button to enable")
    page.click("#btn-download")
    deadline = time.monotonic() + 30
    target = download_dir / "textproof-report.json"
    while not target.exists():
        if time.monotonic() > deadline:
            raise RuntimeError("UI download did not appear in 30s")
        time.sleep(0.2)
    raw = target.read_bytes()
    _write_case_report(workdir, "ui", case_id, raw)
    return json.loads(raw.decode("utf-8")), _sha256_bytes(raw)


def diff_paths(a, b, path: str = "$") -> list[str]:
    """Field-by-field differences between two JSON values."""
    diffs: list[str] = []
    if type(a) is not type(b) and not (
            isinstance(a, (int, float)) and isinstance(b, (int, float))):
        diffs.append(f"{path}: type {type(a).__name__} vs {type(b).__name__}")
        return diffs
    if isinstance(a, dict):
        for key in sorted(set(a) | set(b)):
            if key not in a:
                diffs.append(f"{path}.{key}: missing in first")
            elif key not in b:
                diffs.append(f"{path}.{key}: missing in second")
            else:
                diffs.extend(diff_paths(a[key], b[key], f"{path}.{key}"))
    elif isinstance(a, list):
        if len(a) != len(b):
            diffs.append(f"{path}: length {len(a)} vs {len(b)}")
        for i, (x, y) in enumerate(zip(a, b)):
            diffs.extend(diff_paths(x, y, f"{path}[{i}]"))
    elif a != b:
        diffs.append(f"{path}: {a!r} vs {b!r}")
    return diffs


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    by_id = {f["id"]: f for f in manifest["fixtures"]}
    clean = next(f for f in manifest["fixtures"] if f["category"] == "clean")
    cases = [
        ("TP-S0-ZH-002", by_id["TP-S0-ZH-002"]),
        (clean["id"], clean),
    ]
    workdir = args.out.parent / "consistency_work"
    workdir.mkdir(parents=True, exist_ok=True)
    download_dir = workdir / "downloads"
    download_dir.mkdir(parents=True, exist_ok=True)

    results: dict[str, object] = {"cases": []}
    all_ok = True
    try:
        with LiveServer() as base:
            chrome = Chrome()
            try:
                chrome.set_download_dir(download_dir)
                page = chrome.new_page()
                for case_id, rec in cases:
                    image_path = FIXTURES / rec["filename"]
                    expected = rec["expected_text"]
                    # R-08: stdout carries case id + verdicts only,
                    # never fixture expected/drawn text.
                    print(f"=== {case_id} ===")
                    api, api_sha = api_check(base, image_path, expected,
                                             workdir, case_id)
                    print(f"  API verdict={api.get('verdict')}")
                    cli, cli_sha = cli_check(image_path, expected,
                                             workdir, case_id)
                    print(f"  CLI verdict={cli.get('verdict')}")
                    ui, ui_sha = ui_check(page, base, image_path, expected,
                                          download_dir, workdir, case_id)
                    print(f"  UI  verdict={ui.get('verdict')}")
                    diffs = []
                    diffs += [f"API-vs-CLI: {d}" for d in diff_paths(api, cli)]
                    diffs += [f"API-vs-UI: {d}" for d in diff_paths(api, ui)]
                    diffs += [f"CLI-vs-UI: {d}" for d in diff_paths(cli, ui)]
                    ok = not diffs
                    all_ok = all_ok and ok
                    print(f"  -> {'IDENTICAL' if ok else 'DIFFERENT: ' + '; '.join(diffs[:5])}")
                    results["cases"].append({
                        "fixture_id": case_id,
                        "filename": rec["filename"],
                        "expected_text": expected,
                        "drawn_text": rec["drawn_text"],
                        "verdicts": {"api": api.get("verdict"),
                                     "cli": cli.get("verdict"),
                                     "ui": ui.get("verdict")},
                        "identical": ok,
                        "differences": diffs,
                        # R-06: per-case retained files + SHA-256, so
                        # each case's IDENTICAL can be re-checked
                        # from the retained files alone.
                        "reports": {
                            "api": {"file": f"api-{case_id}.json",
                                    "sha256": api_sha},
                            "cli": {"file": f"cli-{case_id}.json",
                                    "sha256": cli_sha},
                            "ui": {"file": f"ui-{case_id}.json",
                                   "sha256": ui_sha},
                        },
                    })
            finally:
                chrome.stop()
    finally:
        # R-08: shared scratch files are deleted even if a case
        # fails; per-case evidence files are kept.
        _cleanup_scratch(workdir, download_dir)
    results["all_identical"] = all_ok
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(results, indent=2, ensure_ascii=False) + "\n",
                        encoding="utf-8")
    print(f"all identical: {all_ok}")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
