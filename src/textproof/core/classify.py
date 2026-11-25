"""Error classification (§4.5, §7.4, §7.5) (PROJECT_BOOK.md).

Classification rules (frozen):

* Substitution of one Unicode decimal digit (``Nd``, §7.4) by a
  different digit → ``NUMERIC_CHANGE``.  This takes precedence over
  every other substitution class, including visual-confusion pairs
  (a confusion pair is always letter-vs-digit, never digit-vs-digit).
* Any other substitution → ``SUBSTITUTION`` — including visual
  confusion pairs (``O``→``0`` etc.): their lower 0.65 *cost* only
  influences alignment choice, never the error type, and never
  suppresses the record (§4.5).
* Expected character absent from OCR → ``MISSING_CHARACTER`` — even
  when the missing character is a digit (§7.4: "数字缺失仍为
  ``MISSING_CHARACTER``").
* OCR character absent from expected → ``EXTRA_CHARACTER`` — even
  when the extra character is a digit (§7.4).
* A whole expected line with no OCR partner → ``MISSING_LINE``.
* A whole OCR line with no expected partner → ``EXTRA_LINE``.

Fragments: consecutive ops of the *same* error type merge into one
``Difference`` (so "新客立减20元" vs "新客立减元" is a single
``MISSING_CHARACTER`` with ``expected_fragment="20"``, as §8.1
TP-S0-ZH-003 requires — "至少 1 条 ... expected_fragment=20").  A
run of substitutions that changes type mid-run (e.g. a letter
substitution followed by a digit substitution) splits at the type
boundary.  Spans are half-open ``[start, end)`` code-point indices
into the *normalised* line text (§4.3.6).

Coordinates (§4.6, §7.5): a character difference's bbox is the whole
OCR *line* box that contains it — never a synthesised single-character
box.  A missing line has no OCR box, so its bbox is ``None``; no
neighbouring box is ever substituted for it.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Sequence

from textproof.core.weighted_edit import EditOp, is_digit, weighted_edit_ops

__all__ = [
    "Difference",
    "classify_substitution",
    "op_error_type",
    "diffs_for_aligned_pair",
    "missing_line_difference",
    "extra_line_difference",
]

ErrorType = Literal[
    "SUBSTITUTION",
    "MISSING_CHARACTER",
    "EXTRA_CHARACTER",
    "NUMERIC_CHANGE",
    "MISSING_LINE",
    "EXTRA_LINE",
    "AMBIGUOUS_ALIGNMENT",
]


@dataclass(frozen=True)
class Difference:
    """One classified difference, before report-id assignment.

    ``expected_span`` / ``recognized_span`` are half-open code-point
    spans into the normalised expected / recognised line; either may
    be ``None`` when that side has no line (``MISSING_LINE`` /
    ``EXTRA_LINE``).  ``bbox_xyxy`` is the containing OCR line box, or
    ``None`` for a missing line.  ``confidence`` is the containing OCR
    line's confidence, or ``None`` when there is no OCR line.
    """

    type: ErrorType
    expected_line_index: int | None
    ocr_line_index: int | None
    expected_span: tuple[int, int] | None
    recognized_span: tuple[int, int] | None
    expected_fragment: str
    recognized_fragment: str
    bbox_xyxy: tuple[float, float, float, float] | None
    confidence: float | None


def classify_substitution(expected_ch: str, recognized_ch: str) -> ErrorType:
    """Classify one differing character pair (§7.4).

    Digit-to-digit → ``NUMERIC_CHANGE``; anything else (including
    confusion pairs and punctuation) → ``SUBSTITUTION``.  Callers only
    pass pairs with ``expected_ch != recognized_ch``.
    """
    if is_digit(expected_ch) and is_digit(recognized_ch):
        return "NUMERIC_CHANGE"
    return "SUBSTITUTION"


def op_error_type(
    op: EditOp, expected_line: str, recognized_line: str
) -> ErrorType | None:
    """Error type for one edit op; ``None`` for a ``match`` op."""
    if op.kind == "match":
        return None
    if op.kind == "delete":
        return "MISSING_CHARACTER"
    if op.kind == "insert":
        return "EXTRA_CHARACTER"
    # substitute: both indices are set by construction.
    assert op.expected_index is not None and op.recognized_index is not None
    return classify_substitution(
        expected_line[op.expected_index], recognized_line[op.recognized_index]
    )


def _merge_ops(
    ops: Sequence[EditOp], expected_line: str, recognized_line: str
) -> list[Difference]:
    """Merge consecutive same-type ops into fragment-level differences.

    Spans are computed from the running DP positions, not from a
    single side's index: a ``delete`` consumes an expected character
    and sits at a *point* in the recognised text (empty span), an
    ``insert`` consumes a recognised character and sits at a point in
    the expected text.  Two adjacent deletes therefore share the same
    recognised point (e.g. "20" missing → recognised span ``[4, 4)``),
    and two adjacent inserts share the same expected point.

    The caller fills in line indices / bbox / confidence afterwards;
    this helper only computes type, spans and fragments.
    """
    merged: list[dict[str, object]] = []
    exp_pos = 0  # expected code points consumed by ops so far
    rec_pos = 0  # recognised code points consumed by ops so far
    for op in ops:
        error_type = op_error_type(op, expected_line, recognized_line)
        if op.kind == "match":
            exp_pos += 1
            rec_pos += 1
            continue
        if op.kind == "delete":
            exp_span = (exp_pos, exp_pos + 1)
            rec_span = (rec_pos, rec_pos)
            exp_frag = expected_line[exp_pos]
            rec_frag = ""
            exp_pos += 1
        elif op.kind == "insert":
            exp_span = (exp_pos, exp_pos)
            rec_span = (rec_pos, rec_pos + 1)
            exp_frag = ""
            rec_frag = recognized_line[rec_pos]
            rec_pos += 1
        else:  # substitute
            exp_span = (exp_pos, exp_pos + 1)
            rec_span = (rec_pos, rec_pos + 1)
            exp_frag = expected_line[exp_pos]
            rec_frag = recognized_line[rec_pos]
            exp_pos += 1
            rec_pos += 1
        # Merge with the previous difference iff it is the same error
        # type *and* directly adjacent on both sides (a match op in
        # between breaks the run, as does a type change).
        if (
            merged
            and merged[-1]["type"] == error_type
            and merged[-1]["exp_end"] == exp_span[0]
            and merged[-1]["rec_end"] == rec_span[0]
        ):
            prev = merged[-1]
            prev["exp_end"] = exp_span[1]
            prev["rec_end"] = rec_span[1]
            prev["exp_frag"] = str(prev["exp_frag"]) + exp_frag
            prev["rec_frag"] = str(prev["rec_frag"]) + rec_frag
        else:
            merged.append(
                {
                    "type": error_type,
                    "exp_end": exp_span[1],
                    "rec_end": rec_span[1],
                    "exp_start": exp_span[0],
                    "rec_start": rec_span[0],
                    "exp_frag": exp_frag,
                    "rec_frag": rec_frag,
                }
            )
    return [
        Difference(
            type=str(item["type"]),  # type: ignore[arg-type]
            expected_line_index=None,  # filled in by the caller
            ocr_line_index=None,
            expected_span=(int(item["exp_start"]), int(item["exp_end"])),
            recognized_span=(int(item["rec_start"]), int(item["rec_end"])),
            expected_fragment=str(item["exp_frag"]),
            recognized_fragment=str(item["rec_frag"]),
            bbox_xyxy=None,
            confidence=None,
        )
        for item in merged
    ]


def diffs_for_aligned_pair(
    expected_line: str,
    recognized_line: str,
    expected_line_index: int,
    ocr_line_index: int,
    bbox_xyxy: tuple[float, float, float, float],
    confidence: float,
) -> list[Difference]:
    """Character differences for one aligned line pair (§4.5, §7.3–§7.5).

    Runs the weighted edit DP on the two *normalised* lines, merges
    adjacent same-type ops, and stamps every difference with the
    containing OCR line's box and confidence (§4.6: line box, not a
    single-character box).  An identical pair yields no differences.
    """
    result = weighted_edit_ops(expected_line, recognized_line)
    partial = _merge_ops(result.ops, expected_line, recognized_line)
    return [
        Difference(
            type=d.type,
            expected_line_index=expected_line_index,
            ocr_line_index=ocr_line_index,
            expected_span=d.expected_span,
            recognized_span=d.recognized_span,
            expected_fragment=d.expected_fragment,
            recognized_fragment=d.recognized_fragment,
            bbox_xyxy=bbox_xyxy,
            confidence=confidence,
        )
        for d in partial
    ]


def missing_line_difference(
    expected_line: str, expected_line_index: int
) -> Difference:
    """A whole expected line with no OCR partner (§4.6, §7.5).

    ``bbox_xyxy`` is ``None``: a missing line has no OCR box and none
    is fabricated.  The span covers the whole normalised line.
    """
    return Difference(
        type="MISSING_LINE",
        expected_line_index=expected_line_index,
        ocr_line_index=None,
        expected_span=(0, len(expected_line)),
        recognized_span=None,
        expected_fragment=expected_line,
        recognized_fragment="",
        bbox_xyxy=None,
        confidence=None,
    )


def extra_line_difference(
    recognized_line: str,
    ocr_line_index: int,
    bbox_xyxy: tuple[float, float, float, float],
    confidence: float,
) -> Difference:
    """A whole OCR line with no expected partner (§4.6).

    The extra line *is* an OCR line, so its own line box is the bbox
    (unlike ``MISSING_LINE``, which has none).
    """
    return Difference(
        type="EXTRA_LINE",
        expected_line_index=None,
        ocr_line_index=ocr_line_index,
        expected_span=None,
        recognized_span=(0, len(recognized_line)),
        expected_fragment="",
        recognized_fragment=recognized_line,
        bbox_xyxy=bbox_xyxy,
        confidence=confidence,
    )
