"""Validate a ``textproof.report/v1`` report against PROJECT_BOOK.md §5.

This is the in-package home of the handwritten §5 validator (T006
deliverable, plan §5.2 / T006 card item 6).  It used to live only in
``scripts/validate_report_schema.py``; T013-U01 moved the
implementation here so the installed wheel can validate its own
reports without a source checkout (``scripts/`` is not packaged).
``scripts/validate_report_schema.py`` is now a thin wrapper that
re-exports :func:`validate_report` and :func:`main` from this module,
so the script entry point and every existing ``from scripts...``
import keep working unchanged.

The formal ``.schema.json`` file is a T009 deliverable; this module is
the S0 validator, implemented by hand against the frozen contract text
because no JSON-Schema library is in the locked dependency set
(``requirements.lock``; checked 2026-11-25: ``jsonschema`` is not
installed and no new package may be added).

Rules enforced, each anchored to a §5 clause:

* §5.1 — ``schema`` is exactly ``"textproof.report/v1"``; encoding is
  UTF-8 (callers read files as UTF-8); ``coordinate_system`` is
  ``"oriented_image_px_top_left"``; character spans are half-open
  code-point spans into normalised text.
* §5.2 — ``verdict`` is one of ``MATCH`` / ``MISMATCH`` /
  ``REVIEW_REQUIRED`` / ``OCR_FAILED``.
* §5.3 — error ``type`` is one of the seven frozen types; warning
  ``code`` is one of ``LOW_OCR_CONFIDENCE`` /
  ``POSSIBLE_MULTI_COLUMN`` / ``ROTATED_TEXT_NOT_SUPPORTED`` /
  ``OCR_EMPTY``.
* §5.4 — top-level keys are exactly the sample's keys; the ``image``
  block has ``sha256`` (64 lowercase hex chars), ``format`` (``PNG`` /
  ``JPEG`` / ``WEBP``), positive integer ``width`` / ``height`` and
  the coordinate system above; ``tool_version`` is a non-empty
  string; ``expected_text`` / ``recognized_text`` are strings;
  ``ocr_lines`` entries have ``line_index`` (int >= 0), ``text``
  (str), ``confidence`` (number in [0, 1]), ``bbox_xyxy`` (four
  numbers, x1 <= x2, y1 <= y2) and ``quad`` (four [x, y] points);
  ``errors`` entries have ``id`` matching ``E`` + three digits,
  sequential from ``E001``; ``expected_line_index`` /
  ``ocr_line_index`` are ints >= 0 or ``null``; ``expected_text`` /
  ``recognized_text`` are strings; spans are ``null`` or ``[int,
  int]`` with ``0 <= start <= end``; fragments are strings;
  ``bbox_xyxy`` is ``null`` or four numbers inside the image bounds;
  ``bbox_scope`` is ``"ocr_line"`` or ``null``; ``confidence`` is
  ``null`` or a number in [0, 1]; ``summary`` counts equal the
  lengths of the arrays they count.
* §4.6 / §7.5 — a ``MISSING_LINE`` error has ``bbox_xyxy`` ``null``
  (no fabricated box); every other error has a non-null line bbox.
* §5.4 sample — error spans must lie inside the error's own
  ``expected_text`` / ``recognized_text`` (the normalised line texts
  the spans index into, §4.3.6).

Frozen by T009 (finding F-03, see ``schemas/textproof.report.v1.schema.json``
and ``task_handoffs/T009/TASK_RESULT.md``): the absent side of a
``MISSING_LINE`` / ``EXTRA_LINE`` span is ``null`` (never ``[0, 0]``),
a missing box has ``bbox_scope`` ``null`` (never ``"none"``), and a
warning is exactly ``{code, message}`` plus ``ocr_line_index`` only
for ``LOW_OCR_CONFIDENCE`` (no ``confidence`` field).  This validator
and the ``.schema.json`` file enforce the same frozen form; a report
is valid only if it passes both.

T013 (findings R-05, R-15): ``summary.expected_lines`` counts lines
after unifying CR/CRLF to LF first (the production rule in
``image_loader``), and the present side of every error carries a
non-null line index — MISSING_LINE: ``expected_line_index``;
EXTRA_LINE: ``ocr_line_index``; character errors: both.

Usage::

    PYTHONPATH=src python -m textproof.core.report_schema report.json
    python scripts/validate_report_schema.py report.json [report2.json ...]
    python scripts/validate_report_schema.py --reports-dir dir/

Exit code 0 iff every report is valid; every violation is printed
with its JSON path.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

SCHEMA_ID = "textproof.report/v1"
COORDINATE_SYSTEM = "oriented_image_px_top_left"
VERDICTS = {"MATCH", "MISMATCH", "REVIEW_REQUIRED", "OCR_FAILED"}
ERROR_TYPES = {
    "SUBSTITUTION",
    "MISSING_CHARACTER",
    "EXTRA_CHARACTER",
    "NUMERIC_CHANGE",
    "MISSING_LINE",
    "EXTRA_LINE",
    "AMBIGUOUS_ALIGNMENT",
}
WARNING_CODES = {
    "LOW_OCR_CONFIDENCE",
    "POSSIBLE_MULTI_COLUMN",
    "ROTATED_TEXT_NOT_SUPPORTED",
    "OCR_EMPTY",
}
IMAGE_FORMATS = {"PNG", "JPEG", "WEBP"}
TOP_LEVEL_KEYS = {
    "schema",
    "tool_version",
    "verdict",
    "image",
    "expected_text",
    "recognized_text",
    "ocr_lines",
    "errors",
    "warnings",
    "summary",
}
OCR_LINE_KEYS = {"line_index", "text", "confidence", "bbox_xyxy", "quad"}
ERROR_KEYS = {
    "id",
    "type",
    "expected_line_index",
    "ocr_line_index",
    "expected_text",
    "recognized_text",
    "expected_span",
    "recognized_span",
    "expected_fragment",
    "recognized_fragment",
    "bbox_xyxy",
    "bbox_scope",
    "confidence",
}
WARNING_KEYS = {"code", "message"}
SUMMARY_KEYS = {"expected_lines", "ocr_lines", "error_count", "warning_count"}

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_ERROR_ID_RE = re.compile(r"^E\d{3}$")


def _unified_lines(text: str) -> list[str]:
    """Split ``text`` into lines after unifying newlines to LF.

    Same rule as ``src/textproof/io/image_loader.py``
    (``validate_expected_text``) and the §4.3 normalisation: CRLF and
    a lone CR both become LF before splitting, so ``'a\\rb'`` is two
    lines, not one (T013, finding R-05).
    """
    return text.replace("\r\n", "\n").replace("\r", "\n").split("\n")


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _check_bbox(value: Any, path: str, errors: list[str],
                width: int | None, height: int | None) -> None:
    if value is None:
        return
    if not isinstance(value, list) or len(value) != 4 \
            or not all(_is_number(v) for v in value):
        errors.append(f"{path}: bbox must be null or [x1, y1, x2, y2] numbers")
        return
    x1, y1, x2, y2 = value
    if not (x1 <= x2 and y1 <= y2):
        errors.append(f"{path}: bbox corners out of order: {value}")
    if width is not None and height is not None:
        if x1 < 0 or y1 < 0 or x2 > width or y2 > height:
            errors.append(
                f"{path}: bbox {value} outside image bounds "
                f"{width}x{height} (§5.4 / §8.1)")
        if x1 < 0 or y1 < 0:
            errors.append(f"{path}: bbox has negative coordinates: {value}")


def _check_span(value: Any, path: str, errors: list[str],
                line_text: str | None) -> None:
    if value is None:
        return
    if not isinstance(value, list) or len(value) != 2 \
            or not all(isinstance(v, int) and not isinstance(v, bool)
                       for v in value):
        errors.append(f"{path}: span must be null or [int, int]")
        return
    start, end = value
    if not (0 <= start <= end):
        errors.append(f"{path}: span not half-open with 0 <= start <= end: {value}")
    if line_text is not None and end > len(line_text):
        errors.append(
            f"{path}: span end {end} exceeds its line text length "
            f"{len(line_text)} (§4.3.6)")


def validate_report(report: Any) -> list[str]:
    """Return the list of §5 violations in ``report`` (empty = valid)."""
    errors: list[str] = []
    if not isinstance(report, dict):
        return ["$: report must be a JSON object"]
    if set(report.keys()) != TOP_LEVEL_KEYS:
        errors.append(
            f"$: top-level keys must be exactly {sorted(TOP_LEVEL_KEYS)}; "
            f"got {sorted(report.keys())} (§5.4)")
    if report.get("schema") != SCHEMA_ID:
        errors.append(f"$.schema: must be {SCHEMA_ID!r} (§5.1)")
    tool_version = report.get("tool_version")
    if tool_version != "0.1.0":
        errors.append("$.tool_version: must be exactly \"0.1.0\" "
                      "(frozen product version, §5.4; T009)")
    if report.get("verdict") not in VERDICTS:
        errors.append(f"$.verdict: must be one of {sorted(VERDICTS)} (§5.2)")
    if not isinstance(report.get("expected_text"), str):
        errors.append("$.expected_text: must be a string (§5.4)")
    if not isinstance(report.get("recognized_text"), str):
        errors.append("$.recognized_text: must be a string (§5.4)")

    image = report.get("image")
    width = height = None
    if not isinstance(image, dict):
        errors.append("$.image: must be an object (§5.4)")
    else:
        if set(image.keys()) != {"sha256", "format", "width", "height",
                                 "coordinate_system"}:
            errors.append(
                "$.image: keys must be sha256/format/width/height/"
                "coordinate_system (§5.4)")
        sha = image.get("sha256")
        if not isinstance(sha, str) or not _SHA256_RE.match(sha):
            errors.append("$.image.sha256: must be 64 lowercase hex chars (§5.4)")
        if image.get("format") not in IMAGE_FORMATS:
            errors.append(f"$.image.format: must be one of {sorted(IMAGE_FORMATS)}")
        width, height = image.get("width"), image.get("height")
        for name, value in (("width", width), ("height", height)):
            if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
                errors.append(f"$.image.{name}: must be a positive integer (§5.4)")
        if image.get("coordinate_system") != COORDINATE_SYSTEM:
            errors.append(
                f"$.image.coordinate_system: must be {COORDINATE_SYSTEM!r} (§5.1)")

    ocr_lines = report.get("ocr_lines")
    if not isinstance(ocr_lines, list):
        errors.append("$.ocr_lines: must be a list (§5.4)")
        ocr_lines = []
    for i, line in enumerate(ocr_lines):
        path = f"$.ocr_lines[{i}]"
        if not isinstance(line, dict):
            errors.append(f"{path}: must be an object")
            continue
        if set(line.keys()) != OCR_LINE_KEYS:
            errors.append(f"{path}: keys must be exactly {sorted(OCR_LINE_KEYS)}")
        if not isinstance(line.get("line_index"), int) \
                or isinstance(line.get("line_index"), bool) \
                or line.get("line_index", -1) < 0:
            errors.append(f"{path}.line_index: must be an int >= 0")
        elif line.get("line_index") != i:
            errors.append(
                f"{path}.line_index: must equal its position {i} (§7.1)")
        if not isinstance(line.get("text"), str):
            errors.append(f"{path}.text: must be a string")
        conf = line.get("confidence")
        if not _is_number(conf) or not 0.0 <= conf <= 1.0:
            errors.append(f"{path}.confidence: must be a number in [0, 1] "
                          "(T009: an OCR line always carries a confidence)")
        _check_bbox(line.get("bbox_xyxy"), f"{path}.bbox_xyxy", errors,
                    width, height)
        quad = line.get("quad")
        if not isinstance(quad, list) or len(quad) != 4 or any(
                not isinstance(p, list) or len(p) != 2
                or not all(_is_number(v) for v in p) for p in quad):
            errors.append(f"{path}.quad: must be four [x, y] points (§5.4)")

    error_list = report.get("errors")
    if not isinstance(error_list, list):
        errors.append("$.errors: must be a list (§5.4)")
        error_list = []
    for i, err in enumerate(error_list):
        path = f"$.errors[{i}]"
        if not isinstance(err, dict):
            errors.append(f"{path}: must be an object")
            continue
        if set(err.keys()) != ERROR_KEYS:
            errors.append(f"{path}: keys must be exactly {sorted(ERROR_KEYS)}")
        err_id = err.get("id")
        if not isinstance(err_id, str) or not _ERROR_ID_RE.match(err_id):
            errors.append(f"{path}.id: must match E### (§5.4)")
        elif err_id != f"E{i + 1:03d}":
            errors.append(
                f"{path}.id: ids must be sequential E001...; expected "
                f"E{i + 1:03d}, got {err_id}")
        if err.get("type") not in ERROR_TYPES:
            errors.append(f"{path}.type: must be one of {sorted(ERROR_TYPES)} (§5.3)")
        for field in ("expected_line_index", "ocr_line_index"):
            value = err.get(field)
            if value is not None and (not isinstance(value, int)
                                      or isinstance(value, bool) or value < 0):
                errors.append(f"{path}.{field}: must be null or an int >= 0")
        exp_text = err.get("expected_text")
        rec_text = err.get("recognized_text")
        if not isinstance(exp_text, str):
            errors.append(f"{path}.expected_text: must be a string")
            exp_text = None
        if not isinstance(rec_text, str):
            errors.append(f"{path}.recognized_text: must be a string")
            rec_text = None
        _check_span(err.get("expected_span"), f"{path}.expected_span",
                    errors, exp_text)
        _check_span(err.get("recognized_span"), f"{path}.recognized_span",
                    errors, rec_text)
        if not isinstance(err.get("expected_fragment"), str):
            errors.append(f"{path}.expected_fragment: must be a string")
        if not isinstance(err.get("recognized_fragment"), str):
            errors.append(f"{path}.recognized_fragment: must be a string")
        bbox = err.get("bbox_xyxy")
        _check_bbox(bbox, f"{path}.bbox_xyxy", errors, width, height)
        # Frozen per-type shape (T009, finding F-03).  The absent side
        # of a line error is null, never [0, 0]: [0, 0] is a real empty
        # span at position 0, so it cannot also mean "no side".
        err_type = err.get("type")
        if err_type == "MISSING_LINE":
            if bbox is not None:
                errors.append(
                    f"{path}.bbox_xyxy: MISSING_LINE must have null bbox "
                    "(§4.6 / §7.5)")
            if err.get("recognized_span") is not None:
                errors.append(
                    f"{path}.recognized_span: MISSING_LINE has no OCR "
                    "side; must be null (T009 F-03)")
            if err.get("ocr_line_index") is not None:
                errors.append(
                    f"{path}.ocr_line_index: MISSING_LINE must be null")
            if err.get("expected_span") is None:
                errors.append(
                    f"{path}.expected_span: MISSING_LINE must carry the "
                    "whole-line span")
            if err.get("expected_line_index") is None:
                errors.append(
                    f"{path}.expected_line_index: MISSING_LINE must carry "
                    "its expected line index (T013 R-15: the present side "
                    "is never null)")
        elif err_type == "EXTRA_LINE":
            if bbox is None:
                errors.append(
                    f"{path}.bbox_xyxy: EXTRA_LINE must carry its OCR "
                    "line bbox (§4.6 / §7.5)")
            if err.get("expected_span") is not None:
                errors.append(
                    f"{path}.expected_span: EXTRA_LINE has no expected "
                    "side; must be null (T009 F-03)")
            if err.get("expected_line_index") is not None:
                errors.append(
                    f"{path}.expected_line_index: EXTRA_LINE must be null")
            if err.get("recognized_span") is None:
                errors.append(
                    f"{path}.recognized_span: EXTRA_LINE must carry the "
                    "whole-line span")
            if err.get("ocr_line_index") is None:
                errors.append(
                    f"{path}.ocr_line_index: EXTRA_LINE must carry its "
                    "OCR line index (T013 R-15: the present side is "
                    "never null)")
        elif err_type == "AMBIGUOUS_ALIGNMENT":
            if err.get("expected_span") is not None \
                    or err.get("recognized_span") is not None:
                errors.append(
                    f"{path}.*_span: AMBIGUOUS_ALIGNMENT must have null "
                    "spans (T009 F-03)")
            if err.get("expected_line_index") is not None \
                    or err.get("ocr_line_index") is not None:
                errors.append(
                    f"{path}.*_line_index: AMBIGUOUS_ALIGNMENT must have "
                    "null line indices")
            if bbox is not None:
                errors.append(
                    f"{path}.bbox_xyxy: AMBIGUOUS_ALIGNMENT must have "
                    "null bbox")
        elif err_type in ("SUBSTITUTION", "MISSING_CHARACTER",
                          "EXTRA_CHARACTER", "NUMERIC_CHANGE"):
            if err.get("expected_span") is None \
                    or err.get("recognized_span") is None:
                errors.append(
                    f"{path}.*_span: character errors always carry both "
                    "spans (T009 F-03)")
            if err.get("expected_line_index") is None \
                    or err.get("ocr_line_index") is None:
                errors.append(
                    f"{path}.expected_line_index / ocr_line_index: "
                    "character errors always carry both line indices "
                    "(T013 R-15: the present side is never null)")
            if bbox is None:
                errors.append(
                    f"{path}.bbox_xyxy: character errors must carry "
                    "their OCR line bbox (§4.6 / §7.5)")
        scope = err.get("bbox_scope")
        if scope not in ("ocr_line", None):
            errors.append(
                f"{path}.bbox_scope: must be 'ocr_line' or null "
                "(T009 F-03: 'none' is not a frozen value)")
        if bbox is None and scope == "ocr_line":
            errors.append(f"{path}.bbox_scope: 'ocr_line' with null bbox")
        if bbox is not None and scope != "ocr_line":
            errors.append(
                f"{path}.bbox_scope: error with a bbox must have scope "
                "'ocr_line'")
        conf = err.get("confidence")
        if conf is not None and (not _is_number(conf) or not 0.0 <= conf <= 1.0):
            errors.append(f"{path}.confidence: must be null or a number in [0, 1]")

    warnings = report.get("warnings")
    if not isinstance(warnings, list):
        errors.append("$.warnings: must be a list (§5.4)")
        warnings = []
    for i, warn in enumerate(warnings):
        path = f"$.warnings[{i}]"
        if not isinstance(warn, dict):
            errors.append(f"{path}: must be an object")
            continue
        # Frozen warning shape (T009, finding F-03): exactly
        # {code, message}, plus ocr_line_index only for
        # LOW_OCR_CONFIDENCE.  No 'confidence' field: the line
        # confidence already lives on the ocr_lines entry.
        if set(warn.keys()) - {"code", "message", "ocr_line_index"}:
            errors.append(
                f"{path}: keys must be code/message and optionally "
                "ocr_line_index (T009 F-03)")
        if warn.get("code") not in WARNING_CODES:
            errors.append(
                f"{path}.code: must be one of {sorted(WARNING_CODES)} (§5.3)")
        if not isinstance(warn.get("message"), str):
            errors.append(f"{path}.message: must be a string")
        if "ocr_line_index" in warn:
            idx = warn["ocr_line_index"]
            if warn.get("code") != "LOW_OCR_CONFIDENCE":
                errors.append(
                    f"{path}.ocr_line_index: only LOW_OCR_CONFIDENCE "
                    "carries a line index (T009 F-03)")
            elif not isinstance(idx, int) or isinstance(idx, bool) or idx < 0:
                errors.append(
                    f"{path}.ocr_line_index: must be an int >= 0")

    summary = report.get("summary")
    if not isinstance(summary, dict):
        errors.append("$.summary: must be an object (§5.4)")
    else:
        if set(summary.keys()) != SUMMARY_KEYS:
            errors.append(
                f"$.summary: keys must be exactly {sorted(SUMMARY_KEYS)}")
        expected_counts = {
            # T013 R-05: count lines the way production does — unify
            # CR/CRLF to LF first, then split (image_loader.py).  The
            # old ``count("\n") + 1`` undercounted a lone CR: 'a\rb'
            # is 2 lines for production but was 1 here, so a legal
            # report failed its own self-check (CLI exit 5).
            "expected_lines": len(_unified_lines(report["expected_text"]))
            if isinstance(report.get("expected_text"), str) else None,
            "ocr_lines": len(ocr_lines),
            "error_count": len(error_list),
            "warning_count": len(warnings),
        }
        for key, value in expected_counts.items():
            actual = summary.get(key)
            if value is not None and actual != value:
                errors.append(
                    f"$.summary.{key}: must be {value}, got {actual} (§5.4)")

    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate textproof.report/v1 reports against §5.")
    parser.add_argument("reports", nargs="*", help="Report JSON file(s).")
    parser.add_argument("--reports-dir", type=Path, default=None,
                        help="Validate every *.json in this directory.")
    args = parser.parse_args(argv)

    paths: list[Path] = [Path(p) for p in args.reports]
    if args.reports_dir is not None:
        paths.extend(sorted(args.reports_dir.glob("*.json")))
    if not paths:
        parser.error("no reports given")

    total_bad = 0
    for path in paths:
        try:
            report = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:  # noqa: BLE001 - report and continue
            print(f"{path}: UNREADABLE: {exc}")
            total_bad += 1
            continue
        violations = validate_report(report)
        if violations:
            total_bad += 1
            print(f"{path}: INVALID ({len(violations)} violation(s))")
            for violation in violations:
                print(f"  - {violation}")
        else:
            print(f"{path}: VALID")
    print(f"schema validation: {len(paths) - total_bad}/{len(paths)} valid")
    return 0 if total_bad == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
