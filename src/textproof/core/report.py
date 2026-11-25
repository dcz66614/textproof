"""Report assembly: ``textproof.report/v1`` (PROJECT_BOOK.md §5, §7.6).

Pipeline (each step owned by exactly one sibling module):

1. ``normalize`` — §4.3 normalisation of the expected text and of
   every OCR line (same rules on both sides).
2. ``line_order`` — §4.4 reading order; OCR lines are reindexed, the
   original order kept in ``source_order``.
3. ``align_lines`` — §7.2 global line DP (gap 0.35, ambiguity margin
   0.05, high-cost pair threshold 0.70).
4. ``classify`` — §4.5/§7.4 character differences per aligned pair,
   ``MISSING_LINE`` / ``EXTRA_LINE`` for unpaired lines.
5. This module — verdict (§7.6), warnings, error ids, summary, and
   the frozen §5.4 JSON shape.

Verdict rules (§7.6, applied in this order):

* No usable OCR text (no OCR lines at all, or every line normalises
  to empty) → ``OCR_FAILED`` with an ``OCR_EMPTY`` warning and no
  character/line errors: a failed recognition supports no
  determination at all, so no ``MISSING_LINE`` is invented for it.
* Ambiguous line alignment (two best paths within 0.05) →
  ``REVIEW_REQUIRED`` with a single ``AMBIGUOUS_ALIGNMENT`` error and
  no deterministic character conclusions (§7.2: "不输出确定性字符结论").
* Otherwise: errors with no warnings → ``MISMATCH``; errors with any
  warning → ``REVIEW_REQUIRED`` (this subsumes the §7.6 rule that a
  difference on a sub-threshold line forces review — the general rule
  is "若无警告且存在差异，才为 MISMATCH"); warnings with no errors →
  ``REVIEW_REQUIRED``; neither → ``MATCH``.

Warnings (§5.3, §7.6):

* ``LOW_OCR_CONFIDENCE`` — an OCR line's confidence is below 0.65.
  One warning per affected line, carrying its reading-order index.
* ``OCR_EMPTY`` — no usable OCR text (see above).

The warning codes ``POSSIBLE_MULTI_COLUMN`` and
``ROTATED_TEXT_NOT_SUPPORTED`` are listed in §5.3 but no detector for
them is specified in §4/§7, so this module does not invent one; they
are left for the task that owns layout detection.  Emitting them
without a specified rule would be fabrication.

JSON shape (§5.4, §4.3.6):

* Top-level ``expected_text`` is the user's *raw* expected text and
  top-level ``recognized_text`` / ``ocr_lines[].text`` are the *raw*
  OCR texts in reading order — the report retains the originals.
* Error-level ``expected_text`` / ``recognized_text`` are the
  *normalised* line texts, because the spans index into them.
* Spans are half-open code-point spans into the normalised line.
* A character difference's ``bbox_xyxy`` is its containing OCR line
  box (``bbox_scope": "ocr_line"``); a ``MISSING_LINE`` has
  ``bbox_xyxy": null`` and ``bbox_scope": null`` — never a fabricated
  box (§4.6, §7.5).
* Error ids are ``E001``, ``E002``, ... in deterministic order:
  alignment order, and within a line, character order.

``tool_version`` is ``"0.1.0"`` (IMPLEMENTATION_PLAN.md: "产品版本
初始目标：0.1.0"; PROJECT_BOOK.md §5.4 sample).  It is the *product*
version, distinct from the packaging version in ``pyproject.toml``.

Determinism: no sets, no randomness, no wall-clock, no dict-order
dependence anywhere in this pipeline — the same inputs produce the
same report dict (tested in ``tests/unit/test_core/test_report.py``).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Final, Sequence, Union

from textproof.contracts import (
    COORDINATE_SYSTEM,
    SCHEMA_ID,
    ExpectedTextInput,
    ImageInput,
)
from textproof.core.align_lines import align_lines
from textproof.core.classify import (
    Difference,
    diffs_for_aligned_pair,
    extra_line_difference,
    missing_line_difference,
)
from textproof.core.line_order import order_lines
from textproof.core.normalize import normalize_lines, split_normalized_lines
from textproof.ocr.rapidocr_adapter import OCRLine

__all__ = [
    "TOOL_VERSION",
    "LOW_CONFIDENCE_THRESHOLD",
    "ComparisonResult",
    "compare",
    "build_report",
    "difference_to_error",
    "ambiguous_alignment_error",
]

#: Product version (IMPLEMENTATION_PLAN.md initial target; §5.4 sample).
TOOL_VERSION: Final[str] = "0.1.0"
#: OCR confidence below this adds LOW_OCR_CONFIDENCE (§7.6).
LOW_CONFIDENCE_THRESHOLD: Final[float] = 0.65


@dataclass
class ComparisonResult:
    """The comparison half of a ``textproof.report/v1`` report (§5.1).

    ``errors`` / ``warnings`` / ``ocr_lines`` are JSON-ready dicts.
    ``expected_text`` is the raw user text; ``recognized_text`` is the
    raw OCR text (reading order, lines joined with ``\\n``).
    """

    verdict: str
    errors: list[dict[str, object]] = field(default_factory=list)
    warnings: list[dict[str, object]] = field(default_factory=list)
    summary: dict[str, int] = field(default_factory=dict)
    expected_text: str = ""
    recognized_text: str = ""
    ocr_lines: list[dict[str, object]] = field(default_factory=list)


def difference_to_error(
    difference: Difference,
    error_id: str,
    expected_line_text: str = "",
    recognized_line_text: str = "",
) -> dict[str, object]:
    """Render one classified :class:`Difference` as a §5.4 error object.

    ``expected_line_text`` / ``recognized_line_text`` are the
    *normalised* line texts (spans index into them).  For line errors
    they are the whole line, which equals the fragment; for character
    errors they are the full normalised line while the fragment is
    only the differing run.
    """
    return {
        "id": error_id,
        "type": difference.type,
        "expected_line_index": difference.expected_line_index,
        "ocr_line_index": difference.ocr_line_index,
        "expected_text": expected_line_text,
        "recognized_text": recognized_line_text,
        "expected_span": (
            list(difference.expected_span)
            if difference.expected_span is not None
            else None
        ),
        "recognized_span": (
            list(difference.recognized_span)
            if difference.recognized_span is not None
            else None
        ),
        "expected_fragment": difference.expected_fragment,
        "recognized_fragment": difference.recognized_fragment,
        "bbox_xyxy": (
            list(difference.bbox_xyxy) if difference.bbox_xyxy is not None else None
        ),
        "bbox_scope": "ocr_line" if difference.bbox_xyxy is not None else None,
        "confidence": difference.confidence,
    }


def ambiguous_alignment_error(
    expected_text: str, recognized_text: str
) -> dict[str, object]:
    """The single ``AMBIGUOUS_ALIGNMENT`` error (§4.4, §7.2).

    No line indices, spans, fragments or bbox: the ambiguity is a
    property of the whole alignment, and §7.2 forbids deterministic
    character conclusions, so no character-level claim is attached.
    """
    return {
        "id": "E001",
        "type": "AMBIGUOUS_ALIGNMENT",
        "expected_line_index": None,
        "ocr_line_index": None,
        "expected_text": expected_text,
        "recognized_text": recognized_text,
        "expected_span": None,
        "recognized_span": None,
        "expected_fragment": "",
        "recognized_fragment": "",
        "bbox_xyxy": None,
        "bbox_scope": None,
        "confidence": None,
    }


def _ocr_line_dict(line: OCRLine) -> dict[str, object]:
    """One §5.4 ``ocr_lines`` entry (raw text retained, §4.3.6)."""
    return {
        "line_index": line.line_index,
        "text": line.text,
        "confidence": line.confidence,
        "bbox_xyxy": list(line.bbox_xyxy),
        "quad": [list(point) for point in line.quad],
    }


def compare(
    expected: Union[str, ExpectedTextInput],
    ocr_lines: Sequence[OCRLine],
) -> ComparisonResult:
    """Compare expected text against OCR lines; return the report body.

    ``expected`` is the raw user text (or a T002
    ``ExpectedTextInput``); ``ocr_lines`` are raw T003 ``OCRLine``
    records in any order (reading order is derived here).  No image,
    OCR engine or UI is involved — the core is testable on fixed OCR
    line records alone (T004 completion definition).
    """
    raw_expected = expected.raw if isinstance(expected, ExpectedTextInput) else expected
    if isinstance(expected, ExpectedTextInput):
        expected_norm = normalize_lines(expected.normalized_lines)
    else:
        expected_norm = split_normalized_lines(raw_expected)

    ordered = order_lines(list(ocr_lines))
    recognized_norm = normalize_lines([ln.text for ln in ordered])
    recognized_raw = "\n".join(ln.text for ln in ordered)

    ocr_line_dicts = [_ocr_line_dict(ln) for ln in ordered]

    warnings: list[dict[str, object]] = []
    for ln in ordered:
        if ln.confidence < LOW_CONFIDENCE_THRESHOLD:
            warnings.append(
                {
                    "code": "LOW_OCR_CONFIDENCE",
                    "message": (
                        "OCR line confidence "
                        f"{ln.confidence} is below {LOW_CONFIDENCE_THRESHOLD}."
                    ),
                    "ocr_line_index": ln.line_index,
                }
            )

    usable = [i for i, text in enumerate(recognized_norm) if text != ""]
    if not usable:
        warnings.append(
            {
                "code": "OCR_EMPTY",
                "message": "OCR produced no usable text.",
            }
        )
        summary = {
            "expected_lines": len(expected_norm),
            "ocr_lines": len(ordered),
            "error_count": 0,
            "warning_count": len(warnings),
        }
        return ComparisonResult(
            verdict="OCR_FAILED",
            errors=[],
            warnings=warnings,
            summary=summary,
            expected_text=raw_expected,
            recognized_text=recognized_raw,
            ocr_lines=ocr_line_dicts,
        )

    alignment = align_lines(list(expected_norm), list(recognized_norm))

    if alignment.ambiguous:
        errors = [
            ambiguous_alignment_error(
                "\n".join(expected_norm), "\n".join(recognized_norm)
            )
        ]
        summary = {
            "expected_lines": len(expected_norm),
            "ocr_lines": len(ordered),
            "error_count": len(errors),
            "warning_count": len(warnings),
        }
        return ComparisonResult(
            verdict="REVIEW_REQUIRED",
            errors=errors,
            warnings=warnings,
            summary=summary,
            expected_text=raw_expected,
            recognized_text=recognized_raw,
            ocr_lines=ocr_line_dicts,
        )

    differences: list[Difference] = []
    for pair in alignment.pairs:
        if pair.expected_index is not None and pair.ocr_index is not None:
            differences.extend(
                diffs_for_aligned_pair(
                    expected_norm[pair.expected_index],
                    recognized_norm[pair.ocr_index],
                    pair.expected_index,
                    pair.ocr_index,
                    ordered[pair.ocr_index].bbox_xyxy,
                    ordered[pair.ocr_index].confidence,
                )
            )
        elif pair.expected_index is not None:
            differences.append(
                missing_line_difference(
                    expected_norm[pair.expected_index], pair.expected_index
                )
            )
        else:
            assert pair.ocr_index is not None
            differences.append(
                extra_line_difference(
                    recognized_norm[pair.ocr_index],
                    pair.ocr_index,
                    ordered[pair.ocr_index].bbox_xyxy,
                    ordered[pair.ocr_index].confidence,
                )
            )

    # Error-level line texts are the normalised line texts (spans index
    # into them); fragments stay as classified.
    errors: list[dict[str, object]] = []
    for n, diff in enumerate(differences, start=1):
        expected_line_text = (
            expected_norm[diff.expected_line_index]
            if diff.expected_line_index is not None
            else ""
        )
        recognized_line_text = (
            recognized_norm[diff.ocr_line_index]
            if diff.ocr_line_index is not None
            else ""
        )
        errors.append(
            difference_to_error(
                diff, f"E{n:03d}", expected_line_text, recognized_line_text
            )
        )

    if errors and not warnings:
        verdict = "MISMATCH"
    elif errors or warnings:
        verdict = "REVIEW_REQUIRED"
    else:
        verdict = "MATCH"

    summary = {
        "expected_lines": len(expected_norm),
        "ocr_lines": len(ordered),
        "error_count": len(errors),
        "warning_count": len(warnings),
    }
    return ComparisonResult(
        verdict=verdict,
        errors=errors,
        warnings=warnings,
        summary=summary,
        expected_text=raw_expected,
        recognized_text=recognized_raw,
        ocr_lines=ocr_line_dicts,
    )


def build_report(
    image: ImageInput,
    expected: Union[str, ExpectedTextInput],
    ocr_lines: Sequence[OCRLine],
) -> dict[str, object]:
    """Build the full ``textproof.report/v1`` dict (§5.4).

    ``image`` supplies the ``image`` block (SHA-256 of the original
    bytes, oriented dimensions); the comparison half comes from
    :func:`compare`.  The dict is JSON-serialisable as-is.
    """
    result = compare(expected, ocr_lines)
    return {
        "schema": SCHEMA_ID,
        "tool_version": TOOL_VERSION,
        "verdict": result.verdict,
        "image": {
            "sha256": image.sha256_hex(),
            "format": image.format,
            "width": image.width,
            "height": image.height,
            "coordinate_system": COORDINATE_SYSTEM,
        },
        "expected_text": result.expected_text,
        "recognized_text": result.recognized_text,
        "ocr_lines": result.ocr_lines,
        "errors": result.errors,
        "warnings": result.warnings,
        "summary": result.summary,
    }
