"""Unit tests for the handwritten report validator
(``scripts/validate_report_schema.py``, PROJECT_BOOK.md §5).

T013 (findings R-05, R-15):

* R-05 — ``summary.expected_lines`` must count lines the way
  production does: unify CR/CRLF to LF first, then split.  A lone CR
  (``'a\\rb'``) is two lines for production (``image_loader``) but was
  one for the old ``count("\\n") + 1`` formula, so a legal report
  failed its own self-check (CLI exit 5).
* R-15 — the present side of an error must carry a non-null line
  index: MISSING_LINE requires ``expected_line_index``,
  EXTRA_LINE requires ``ocr_line_index``, character errors require
  both.  Production never emits a null present-side index
  (``classify.missing_line_difference`` / ``extra_line_difference``
  take the index as a required argument; character errors come from
  aligned pairs), so this is defence in depth — but a hand-built
  report with a null present-side index previously passed both the
  validator and the JSON Schema.

The JSON Schema file (``schemas/textproof.report.v1.schema.json``)
carries the same R-15 rule; it is cross-checked with the system
``jsonschema`` as evidence (T009 precedent — ``jsonschema`` is not in
the frozen lock, so it is not a test dependency here).
"""

from __future__ import annotations

import copy
import sys
from pathlib import Path

import pytest

from textproof.io.image_loader import validate_expected_text

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scripts.validate_report_schema import validate_report  # noqa: E402

LINE_BBOX = [0.0, 0.0, 100.0, 20.0]
LINE_QUAD = [[0.0, 0.0], [100.0, 0.0], [100.0, 20.0], [0.0, 20.0]]


def _ocr_line():
    return {
        "line_index": 0,
        "text": "ab",
        "confidence": 0.99,
        "bbox_xyxy": list(LINE_BBOX),
        "quad": copy.deepcopy(LINE_QUAD),
    }


def _base_report(**overrides):
    report = {
        "schema": "textproof.report/v1",
        "tool_version": "0.1.0",
        "verdict": "MATCH",
        "image": {
            "sha256": "0" * 64,
            "format": "PNG",
            "width": 1200,
            "height": 480,
            "coordinate_system": "oriented_image_px_top_left",
        },
        "expected_text": "ab",
        "recognized_text": "ab",
        "ocr_lines": [_ocr_line()],
        "errors": [],
        "warnings": [],
        "summary": {
            "expected_lines": 1,
            "ocr_lines": 1,
            "error_count": 0,
            "warning_count": 0,
        },
    }
    report.update(overrides)
    return report


def _with_error(error):
    return _base_report(
        verdict="MISMATCH",
        errors=[error],
        summary={
            "expected_lines": 1,
            "ocr_lines": 1,
            "error_count": 1,
            "warning_count": 0,
        },
    )


def _missing_line_error(**overrides):
    error = {
        "id": "E001",
        "type": "MISSING_LINE",
        "expected_line_index": 0,
        "ocr_line_index": None,
        "expected_text": "ab",
        "recognized_text": "",
        "expected_span": [0, 2],
        "recognized_span": None,
        "expected_fragment": "ab",
        "recognized_fragment": "",
        "bbox_xyxy": None,
        "bbox_scope": None,
        "confidence": None,
    }
    error.update(overrides)
    return error


def _extra_line_error(**overrides):
    error = {
        "id": "E001",
        "type": "EXTRA_LINE",
        "expected_line_index": None,
        "ocr_line_index": 0,
        "expected_text": "",
        "recognized_text": "ab",
        "expected_span": None,
        "recognized_span": [0, 2],
        "expected_fragment": "",
        "recognized_fragment": "ab",
        "bbox_xyxy": list(LINE_BBOX),
        "bbox_scope": "ocr_line",
        "confidence": 0.99,
    }
    error.update(overrides)
    return error


def _character_error(error_type="SUBSTITUTION", **overrides):
    error = {
        "id": "E001",
        "type": error_type,
        "expected_line_index": 0,
        "ocr_line_index": 0,
        "expected_text": "ab",
        "recognized_text": "ac",
        "expected_span": [1, 2],
        "recognized_span": [1, 2],
        "expected_fragment": "b",
        "recognized_fragment": "c",
        "bbox_xyxy": list(LINE_BBOX),
        "bbox_scope": "ocr_line",
        "confidence": 0.99,
    }
    error.update(overrides)
    return error


# --- R-05: expected_lines counts lone CR as a line break -----------

@pytest.mark.parametrize("raw", ["a\rb", "a\r"])
def test_expected_lines_lone_cr_matches_production(raw):
    """A lone CR splits a line for production and for the validator."""
    production_lines = len(validate_expected_text(raw).normalized_lines)
    assert production_lines == 2
    report = _base_report(
        expected_text=raw,
        summary={
            "expected_lines": production_lines,
            "ocr_lines": 1,
            "error_count": 0,
            "warning_count": 0,
        },
    )
    assert validate_report(report) == []


@pytest.mark.parametrize(
    ("raw", "lines"), [("a\r\nb", 2), ("a\nb", 2), ("a\nb\nc", 3)])
def test_expected_lines_crlf_and_lf_unchanged(raw, lines):
    """CRLF / LF counting is unchanged by the R-05 fix."""
    assert len(validate_expected_text(raw).normalized_lines) == lines
    report = _base_report(
        expected_text=raw,
        summary={
            "expected_lines": lines,
            "ocr_lines": 1,
            "error_count": 0,
            "warning_count": 0,
        },
    )
    assert validate_report(report) == []


def test_expected_lines_lone_cr_undercount_is_rejected():
    """Claiming 1 line for 'a\\rb' (the old formula's answer) fails."""
    report = _base_report(
        expected_text="a\rb",
        summary={
            "expected_lines": 1,
            "ocr_lines": 1,
            "error_count": 0,
            "warning_count": 0,
        },
    )
    violations = validate_report(report)
    assert any(
        "$.summary.expected_lines: must be 2, got 1" in v
        for v in violations
    )


# --- R-15: present-side line index must be non-null ---------------

def test_missing_line_null_expected_line_index_rejected():
    """R-15 counterexample: MISSING_LINE, expected_line_index null."""
    violations = validate_report(
        _with_error(_missing_line_error(expected_line_index=None)))
    assert any("expected_line_index" in v for v in violations)
    # The valid form still passes.
    assert validate_report(_with_error(_missing_line_error())) == []


def test_extra_line_null_ocr_line_index_rejected():
    """R-15 counterexample: EXTRA_LINE, ocr_line_index null."""
    violations = validate_report(
        _with_error(_extra_line_error(ocr_line_index=None)))
    assert any("ocr_line_index" in v for v in violations)
    # The valid form still passes.
    assert validate_report(_with_error(_extra_line_error())) == []


@pytest.mark.parametrize(
    "error_type",
    ["SUBSTITUTION", "MISSING_CHARACTER", "EXTRA_CHARACTER",
     "NUMERIC_CHANGE"],
)
@pytest.mark.parametrize("null_field", ["expected_line_index",
                                        "ocr_line_index"])
def test_character_error_null_line_index_rejected(error_type, null_field):
    """R-15: character errors carry both line indices, never null."""
    violations = validate_report(
        _with_error(_character_error(error_type, **{null_field: None})))
    assert any(null_field in v for v in violations)


@pytest.mark.parametrize(
    "error_type",
    ["SUBSTITUTION", "MISSING_CHARACTER", "EXTRA_CHARACTER",
     "NUMERIC_CHANGE"],
)
def test_character_error_both_indices_present_accepted(error_type):
    assert validate_report(_with_error(_character_error(error_type))) == []


def test_absent_side_index_must_still_be_null():
    """Guard: the fix must not flip the absent side to non-null."""
    # MISSING_LINE with a non-null OCR index is still rejected.
    assert validate_report(
        _with_error(_missing_line_error(ocr_line_index=0))) != []
    # EXTRA_LINE with a non-null expected index is still rejected.
    assert validate_report(
        _with_error(_extra_line_error(expected_line_index=0))) != []
