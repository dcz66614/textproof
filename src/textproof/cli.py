"""Command-line interface for TextProof (T009, PROJECT_BOOK.md §5.5).

Four commands, all thin wrappers over already-frozen modules — this
module contains **no** comparison algorithm of its own (T009 failure
fallback: "不创建第二套 CLI-only 错误算法"):

* ``check`` — the T007 API pipeline (:func:`textproof.api.routes.run_check`,
  i.e. T002 ``load_image`` + T003 ``RapidOCRAdapter`` + T004
  ``build_report``), driven from files instead of HTTP.  The image
  bytes are base64-encoded only so the *same* ``run_check`` entry
  point (including its MIME / size / base64 transport checks) is
  exercised; the report dict it returns is byte-identical in shape to
  the API response for the same inputs.
* ``serve`` — T007 :func:`textproof.api.app.serve` (loopback-only).
* ``verify-s0`` — thin subprocess wrapper around
  ``scripts/verify_s0.py`` (T006); the logic is not copied here.
  In an installed layout (no source checkout) the S0 runner is not
  shipped in the wheel, so the command exits 3 with a defined
  message instead of failing on a missing path (T013-U01).
* ``version`` — frozen versions only; never constructs the OCR engine.

Exit codes (PROJECT_BOOK.md §5.5, frozen):

=====  ================
code   meaning
=====  ================
0      ``MATCH`` (or a non-check command that succeeded)
1      ``MISMATCH``
2      ``REVIEW_REQUIRED``
3      invalid input (missing/unreadable/invalid image or expected
       file, bad CLI usage, non-loopback serve host, bad port,
       missing S0 manifest)
4      OCR failed (engine error, or a check whose verdict is
       ``OCR_FAILED``)
5      internal error (unexpected exception, or a report that fails
       its own §5 schema validation)
=====  ================

``argparse`` exits 2 on usage errors by default; that code already
means ``REVIEW_REQUIRED`` here, so this module's parser overrides
:meth:`ArgumentParser.error` to exit 3 instead.

Privacy (§5.5 acceptance 4, §9): nothing this module prints or writes
contains an image path, a home path, or image bytes.  ``run_check``
error details are stable snake_case codes (never paths or user text),
and file-not-found / read errors are reported with a fixed message
that does not repeat the path the user passed.
"""

from __future__ import annotations

import argparse
import base64
import importlib.metadata
import json
import subprocess
import sys
from pathlib import Path
from typing import Final

from textproof.api.app import DEFAULT_HOST, DEFAULT_PORT, serve
from textproof.api.routes import (
    CODE_INTERNAL_ERROR,
    CODE_OCR_FAILED,
    SPEC_VERSION,
    ApiError,
    run_check,
)
from textproof.contracts import MIME_BY_FORMAT, SCHEMA_ID
from textproof.core.report import TOOL_VERSION
from textproof.core.report_schema import validate_report
from textproof.io.image_loader import detect_format
from textproof.ocr.rapidocr_adapter import (
    ALLOWED_PROVIDERS,
    ONNXRUNTIME_VERSION,
    RAPIDOCR_VERSION,
)

__all__ = ["EXIT_FOR_VERDICT", "build_parser", "main"]


def _validate_report(report: dict) -> list[str]:
    """Validate ``report`` with the in-package §5 validator.

    The validator lives in ``textproof.core.report_schema`` and ships
    in the wheel, so an installed ``textproof`` validates its own
    reports without a source checkout (T013-U01; the old
    repo-layout-relative ``scripts/`` import failed closed with
    "validator unavailable" in an installed layout).  Import failure
    is a violation, not a skip: a check must never emit a report it
    could not validate (fail closed, exit 5).
    """
    return validate_report(report)

#: CLI exit code for each report verdict (PROJECT_BOOK.md §5.5).
EXIT_FOR_VERDICT: Final[dict[str, int]] = {
    "MATCH": 0,
    "MISMATCH": 1,
    "REVIEW_REQUIRED": 2,
    "OCR_FAILED": 4,
}

#: Exit codes for non-verdict failures (PROJECT_BOOK.md §5.5).
EXIT_INVALID_INPUT: Final[int] = 3
EXIT_OCR_FAILED: Final[int] = 4
EXIT_INTERNAL_ERROR: Final[int] = 5

REPO_ROOT: Final[Path] = Path(__file__).resolve().parents[2]
DEFAULT_MANIFEST: Final[Path] = (
    REPO_ROOT / "tests" / "fixtures" / "s0" / "manifest.json"
)


class _Parser(argparse.ArgumentParser):
    """ArgumentParser whose usage errors exit 3, not argparse's 2.

    Exit code 2 already means ``REVIEW_REQUIRED`` (§5.5), so a usage
    error must never use it; invalid CLI usage is invalid input (3).
    ``--help`` still exits 0 (argparse default).
    """

    def error(self, message: str) -> None:  # noqa: D102 - argparse hook
        self.print_usage(sys.stderr)
        print(f"{self.prog}: error: {message}", file=sys.stderr)
        raise SystemExit(EXIT_INVALID_INPUT)


def build_parser() -> argparse.ArgumentParser:
    """Build the ``textproof`` argument parser (§5.5 command shapes)."""
    parser = _Parser(
        prog="textproof",
        description="TextProof (字证): deterministic AI-image text "
        "verification, local CPU-only OCR.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    check = sub.add_parser(
        "check",
        help="Check one image against expected text; print or write "
        "a textproof.report/v1 JSON report.",
    )
    check.add_argument("--image", required=True,
                       help="Image file (PNG/JPEG/WEBP, §4.2 limits).")
    check.add_argument("--expected-file", required=True,
                       help="File holding the expected text (UTF-8).")
    check.add_argument("--json", default=None, metavar="PATH",
                       help="Write the report JSON to this file instead "
                       "of stdout.")

    serve_cmd = sub.add_parser(
        "serve", help="Serve the local API (loopback only, 127.0.0.1).")
    serve_cmd.add_argument("--host", default=DEFAULT_HOST,
                           help="Bind host; only 127.0.0.1 is accepted "
                           "(default: %(default)s).")
    serve_cmd.add_argument("--port", type=int, default=DEFAULT_PORT,
                           help="Bind port (default: %(default)s).")

    verify = sub.add_parser(
        "verify-s0",
        help="Run the S0 gate (scripts/verify_s0.py) and pass through "
        "its exit code.",
    )
    verify.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST,
                        help="S0 manifest (default: %(default)s).")
    verify.add_argument("--blind", type=Path, default=None,
                        help="Blind-subset JSON (default: next to manifest).")
    verify.add_argument("--expected-output", type=Path, default=None,
                        help="Expected-output JSON (default: next to manifest).")
    verify.add_argument("--out-dir", type=Path, default=None,
                        help="Evidence output directory.")
    verify.add_argument("--force-live", action="store_true",
                        help="Re-run live OCR even if cached results exist.")

    sub.add_parser("version", help="Print frozen versions as JSON.")
    return parser


def _read_file_bytes(path_str: str, what: str) -> bytes | None:
    """Read a file as bytes; on failure print a path-free error.

    Returns ``None`` (after printing) when the file cannot be read.
    The message never repeats the path, so a home or absolute path
    can never leak into logs through this module (§9).
    """
    try:
        return Path(path_str).read_bytes()
    except OSError:
        print(f"textproof: cannot read {what} file.", file=sys.stderr)
        return None


def _check(args: argparse.Namespace) -> int:
    """Run ``check``: files in, ``textproof.report/v1`` out."""
    raw_bytes = _read_file_bytes(args.image, "image")
    if raw_bytes is None:
        return EXIT_INVALID_INPUT
    expected_bytes = _read_file_bytes(args.expected_file, "expected-text")
    if expected_bytes is None:
        return EXIT_INVALID_INPUT
    try:
        expected_text = expected_bytes.decode("utf-8")
    except UnicodeDecodeError:
        print("textproof: expected-text file is not valid UTF-8.",
              file=sys.stderr)
        return EXIT_INVALID_INPUT

    # Reuse the API pipeline verbatim (same function, same checks):
    # MIME sniffed from magic bytes only, never from the file name.
    image_format = detect_format(raw_bytes)
    image_mime = MIME_BY_FORMAT.get(image_format or "", "image/png")
    try:
        report = run_check(
            image_mime=image_mime,
            image_base64=base64.b64encode(raw_bytes).decode("ascii"),
            expected_text=expected_text,
        )
    except ApiError as exc:
        # ApiError.detail is a stable snake_case code, never user
        # text or a path, so it is safe to print.
        if exc.code == CODE_OCR_FAILED:
            print(f"textproof: OCR failed ({exc.detail}).", file=sys.stderr)
            return EXIT_OCR_FAILED
        if exc.code == CODE_INTERNAL_ERROR:
            print("textproof: internal error.", file=sys.stderr)
            return EXIT_INTERNAL_ERROR
        print(f"textproof: invalid input ({exc.detail}).", file=sys.stderr)
        return EXIT_INVALID_INPUT
    except Exception:  # noqa: BLE001 - last resort, never a bare traceback
        print("textproof: internal error.", file=sys.stderr)
        return EXIT_INTERNAL_ERROR
    finally:
        del raw_bytes

    # Fail closed: a report that does not pass its own §5 validation
    # is an internal error, not something to write out as if valid.
    violations = _validate_report(report)
    if violations:
        print("textproof: internal error: generated report failed "
              "schema validation.", file=sys.stderr)
        return EXIT_INTERNAL_ERROR

    verdict = str(report.get("verdict", ""))
    exit_code = EXIT_FOR_VERDICT.get(verdict)
    if exit_code is None:  # pragma: no cover - build_report verdicts are fixed
        print("textproof: internal error: unknown verdict.",
              file=sys.stderr)
        return EXIT_INTERNAL_ERROR

    text = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.json is not None:
        try:
            Path(args.json).write_text(text, encoding="utf-8")
        except OSError:
            print("textproof: cannot write report file.", file=sys.stderr)
            return EXIT_INVALID_INPUT
    else:
        sys.stdout.write(text)
    return exit_code


def _serve(args: argparse.Namespace) -> int:
    """Run ``serve``: T007 loopback-only server (blocks until stopped)."""
    try:
        serve(host=args.host, port=args.port)
    except ValueError as exc:
        # serve() rejects non-loopback hosts / bad ports with
        # ValueError; that is invalid CLI input (3), not a crash.
        # The message is a fixed refusal string, never a path.
        print(f"textproof: {exc}", file=sys.stderr)
        return EXIT_INVALID_INPUT
    return 0


def _find_verify_s0_script() -> Path | None:
    """Locate the S0 runner, or ``None`` when there is no checkout.

    The runner (``scripts/verify_s0.py``) is a development gate, not
    part of the installed product: it needs the checkout's fixtures,
    manifest and helper scripts, none of which ship in the wheel.
    An installed ``textproof`` therefore has no runner to delegate
    to, and :func:`_verify_s0` reports that as a defined exit-3
    error instead of failing on a missing path (T013-U01).
    """
    candidate = REPO_ROOT / "scripts" / "verify_s0.py"
    return candidate if candidate.is_file() else None


def _verify_s0(args: argparse.Namespace) -> int:
    """Run ``verify-s0``: thin wrapper over scripts/verify_s0.py.

    The S0 logic lives only in that script; this command only checks
    the manifest exists, forwards the flags, and passes the exit code
    through unchanged.  In an installed layout (no checkout) there is
    no script to run: when the manifest exists but the runner does
    not, exit 3 with a defined message — the S0 gate requires a
    source checkout (fixtures + manifest + runner are not shipped in
    the wheel).  That is a defined refusal, never a silent pass: no
    S0 verdict is claimed from an installed layout.
    """
    manifest = Path(args.manifest)
    if not manifest.is_file():
        print("textproof: S0 manifest not found.", file=sys.stderr)
        return EXIT_INVALID_INPUT
    script = _find_verify_s0_script()
    if script is None:
        print(
            "textproof: verify-s0 requires a source checkout: the S0 "
            "runner is not shipped in the wheel.",
            file=sys.stderr,
        )
        return EXIT_INVALID_INPUT
    cmd = [sys.executable, str(script),
           "--manifest", str(manifest)]
    if args.blind is not None:
        cmd += ["--blind", str(args.blind)]
    if args.expected_output is not None:
        cmd += ["--expected-output", str(args.expected_output)]
    if args.out_dir is not None:
        cmd += ["--out-dir", str(args.out_dir)]
    if args.force_live:
        cmd += ["--force-live"]
    try:
        completed = subprocess.run(cmd, check=False)
    except OSError:
        print("textproof: internal error: could not start verify-s0.",
              file=sys.stderr)
        return EXIT_INTERNAL_ERROR
    return int(completed.returncode)


def _version() -> int:
    """Run ``version``: frozen versions as JSON (no OCR engine built)."""
    try:
        package_version = importlib.metadata.version("textproof")
    except importlib.metadata.PackageNotFoundError:
        # The package is not installed in the dev checkout (tests run
        # against the working-tree sources); report that honestly
        # instead of inventing a number.
        package_version = "not-installed"
    info = {
        "service": "textproof",
        "tool_version": TOOL_VERSION,
        "package_version": package_version,
        "schema": SCHEMA_ID,
        "spec_version": SPEC_VERSION,
        "rapidocr_version": RAPIDOCR_VERSION,
        "onnxruntime_version": ONNXRUNTIME_VERSION,
        "providers": list(ALLOWED_PROVIDERS),
    }
    sys.stdout.write(json.dumps(info, ensure_ascii=False, indent=2) + "\n")
    return 0


def main(argv: list[str] | None = None) -> int:
    """Entry point (``textproof`` console script): parse and dispatch."""
    args = build_parser().parse_args(argv)
    if args.command == "check":
        return _check(args)
    if args.command == "serve":
        return _serve(args)
    if args.command == "verify-s0":
        return _verify_s0(args)
    if args.command == "version":
        return _version()
    return EXIT_INVALID_INPUT  # pragma: no cover - parser requires a command


if __name__ == "__main__":
    sys.exit(main())
