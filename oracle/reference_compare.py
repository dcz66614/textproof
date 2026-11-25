"""Independent reference comparison oracle for TextProof (P033), T006.

Implemented from the frozen specification alone:

* ``PROJECT_BOOK.md`` §4.3 (normalisation), §4.4 (reading order and
  line alignment), §4.5 (weighted character edit distance), §4.6
  (coordinates), §5 (frozen ``textproof.report/v1`` contract), §7
  (algorithms) and §8.1 (fixed S0 samples);
* ``IMPLEMENTATION_PLAN.md`` §5.1 (interface shapes) and the T006 card.

This module is a deliberately separate code path from the production
implementation.  It imports nothing from ``textproof`` (standard library
only), reads no images and calls no OCR engine: it compares an expected
text against already-recognised OCR line records and builds a
``textproof.report/v1`` report dict.

Frozen constants (spec §4.4 / §7.2 / §7.6):

* line gap penalty ``0.35``; ambiguity margin ``0.05``;
  high pair cost ``0.70``; low-confidence threshold ``0.65``.
* character weights (§4.5): equal ``0``, visual-confusion substitution
  ``0.65``, punctuation substitution ``0.50``, digit-to-digit
  substitution ``1.25``, other substitution ``1.00``,
  missing / extra character ``1.00``.

Decisions where the specification text leaves room (recorded here so a
reviewer can challenge them; see also ``TASK_RESULT.md``):

1. Confusion pairs (§4.5 says "如", i.e. the list is exemplary).  Only
   the pairs named in the spec are used, literally: ``O/0``, ``I/1``,
   ``I/l``, ``1/l``, ``S/5``, ``B/8``.  Lowercase ``o/0``, ``s/5`` and
   ``b/8`` are NOT treated as confusion pairs.
2. Line splitting follows ``contracts.py`` ("LF-separated segments"):
   the text is split on ``"\\n"`` literally, so ``""`` is one empty
   line and a trailing newline yields a trailing empty line.
3. The punctuation-substitution cost (``0.50``) applies only when
   *both* characters are Unicode punctuation (category ``P*``).
4. A pair cost above ``0.70`` is excluded from the line DP.  This is
   exactly equivalent to letting the DP choose: delete + insert costs
   ``0.35 + 0.35 = 0.70``, so any optimal alignment already avoids such
   a pair; the exclusion only makes the intent explicit.
5. ``AMBIGUOUS_ALIGNMENT`` is emitted as one entry in ``errors`` (§5.3
   lists it in the error-type enum).  When ambiguous, no deterministic
   character/line conclusions are emitted (§7.2: "不输出确定性字符结论"),
   so ``errors`` holds exactly that one entry.
6. Consecutive operations of the same kind inside one line pair merge
   into a single error record (this is what makes §8.1 ZH-003 report
   the missing ``"20"`` as one ``MISSING_CHARACTER`` with span
   ``[4, 6]``).  Consecutive substitutions of *different* classified
   types (e.g. ``SUBSTITUTION`` followed by ``NUMERIC_CHANGE``) are
   kept as separate records.
7. Warnings are objects ``{"code", "message", ...}``: one
   ``LOW_OCR_CONFIDENCE`` object per OCR line below ``0.65``, and one
   ``OCR_EMPTY`` object when OCR produced no usable text.  The spec
   (§5.3) fixes the warning *codes* but shows no warning object shape.
8. ``MISSING_LINE`` carries ``bbox_xyxy: null`` and ``bbox_scope:
   "none"``; every other error carries ``bbox_scope: "ocr_line"`` with
   the paired / extra OCR line's box.  Error-level ``expected_text`` /
   ``recognized_text`` are the *normalised* line texts (spans index
   normalised text); the report top level keeps the raw expected text
   and the raw recognised text (§4.3.6).
9. The ``image`` block is always present.  The oracle takes no image
   bytes, so callers pass ``image_info`` (``sha256`` / ``format`` /
   ``width`` / ``height``) when known; unknown fields are ``null``.
10. No usable OCR text and non-empty expected text is ``OCR_FAILED``
    with an ``OCR_EMPTY`` warning and no error records.  Empty expected
    text together with empty OCR is ``MATCH``.
11. ``tool_version`` defaults to ``"0.1.0"``, the value in the §5.4
    sample.
12. Reading order: OCR line records are re-sorted by bbox vertical
    centre, then bbox ``x1``, then ``source_order`` (§4.4: rows by ``y``
    ascending, same visual row by ``x`` ascending); ``line_index`` in
    the report is the reassigned sorted zero-based index (§7.1).
    Records without a bbox keep their relative input order after
    records with one.
13. Ambiguity (§4.4: "两个最优对齐路径代价差小于 0.05") is judged
    over *distinct alignments*, where an alignment is its set of
    paired lines.  Two DP paths that differ only by swapping adjacent
    delete/insert steps encode the same alignment (same pairs, same
    missing/extra lines) and do not count as two paths; otherwise
    every missing-plus-extra case would be "ambiguous" by
    construction.  The second-best cost is therefore the cheapest
    alignment whose pair set differs from the best one's.
"""

from __future__ import annotations

import re
import unicodedata
from fractions import Fraction
from typing import Any, Optional, Sequence

__all__ = [
    "SCHEMA_ID",
    "COORDINATE_SYSTEM",
    "TOOL_VERSION",
    "GAP_PENALTY",
    "AMBIGUITY_MARGIN",
    "HIGH_PAIR_COST",
    "LOW_CONFIDENCE_THRESHOLD",
    "normalize_text",
    "split_normalized_lines",
    "substitution_cost",
    "weighted_edit_distance",
    "pair_cost",
    "compare",
]

# ---------------------------------------------------------------------------
# Frozen identity and thresholds (PROJECT_BOOK.md §5.1, §4.4, §7.2, §7.6)
# ---------------------------------------------------------------------------

SCHEMA_ID = "textproof.report/v1"
COORDINATE_SYSTEM = "oriented_image_px_top_left"
TOOL_VERSION = "0.1.0"

GAP_PENALTY = 0.35
AMBIGUITY_MARGIN = 0.05
HIGH_PAIR_COST = 0.70
LOW_CONFIDENCE_THRESHOLD = 0.65

_GAP = Fraction(35, 100)
_MARGIN = Fraction(5, 100)
_HIGH_COST = Fraction(70, 100)
_BIG = Fraction(10**9, 1)  # "infinity" for the line DP; real costs stay << 1.

# Character weights in integer hundredths (§4.5) so the character DP is
# exact and free of float drift.
_W_EQUAL = 0
_W_CONFUSION = 65
_W_PUNCTUATION = 50
_W_DIGIT = 125
_W_OTHER = 100
_W_INDEL = 100

# Visual-confusion pairs named in §4.5, taken literally (see docstring 1).
_CONFUSION_PAIRS = frozenset(
    frozenset(pair)
    for pair in (("O", "0"), ("I", "1"), ("I", "l"), ("1", "l"),
                 ("S", "5"), ("B", "8"))
)

_WS_RUN = re.compile(r"\s+")
_FULLWIDTH_SPACE = 0x3000
_FULLWIDTH_ASCII_FIRST = 0xFF01
_FULLWIDTH_ASCII_LAST = 0xFF5E
_FULLWIDTH_OFFSET = 0xFEE0


# ---------------------------------------------------------------------------
# §4.3 normalisation
# ---------------------------------------------------------------------------

def _map_fullwidth(ch: str) -> str:
    """Map one full-width ASCII char to half-width; full-width space to space."""
    code = ord(ch)
    if _FULLWIDTH_ASCII_FIRST <= code <= _FULLWIDTH_ASCII_LAST:
        return chr(code - _FULLWIDTH_OFFSET)
    if code == _FULLWIDTH_SPACE:
        return " "
    return ch


def normalize_text(text: str) -> str:
    """Apply §4.3 to a whole text: NFC, newline unification, full-width
    mapping, per-line strip and horizontal-whitespace folding.

    Case is preserved; punctuation is preserved.
    """
    if not isinstance(text, str):
        raise TypeError("text must be str")
    text = unicodedata.normalize("NFC", text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = "".join(_map_fullwidth(ch) for ch in text)
    return "\n".join(_WS_RUN.sub(" ", line.strip()) for line in text.split("\n"))


def split_normalized_lines(text: str) -> list[str]:
    """Split an expected / OCR text into normalised lines (§4.3).

    Literal ``"\\n"`` split (see docstring 2): ``""`` yields ``[""]`` and
    a trailing newline yields a trailing empty line.
    """
    return normalize_text(text).split("\n")


# ---------------------------------------------------------------------------
# §4.5 / §7.3 character-level weighted edit distance
# ---------------------------------------------------------------------------

def _is_decimal_digit(ch: str) -> bool:
    return unicodedata.category(ch) == "Nd"


def _is_punctuation(ch: str) -> bool:
    return unicodedata.category(ch).startswith("P")


def _substitution_cost_cents(a: str, b: str) -> int:
    if a == b:
        return _W_EQUAL
    if frozenset((a, b)) in _CONFUSION_PAIRS:
        return _W_CONFUSION
    if _is_punctuation(a) and _is_punctuation(b):
        return _W_PUNCTUATION
    if _is_decimal_digit(a) and _is_decimal_digit(b):
        return _W_DIGIT
    return _W_OTHER


def substitution_cost(a: str, b: str) -> float:
    """Cost of substituting single character ``a`` with ``b`` (§4.5)."""
    if len(a) != 1 or len(b) != 1:
        raise ValueError("substitution_cost takes single characters")
    return _substitution_cost_cents(a, b) / 100.0


def _char_edit_ops(expected: str, recognized: str):
    """Character DP (§7.3).

    Returns ``(cost_cents, ops)`` where ``ops`` is a list of
    ``(kind, exp_index, rec_index)`` with kind in ``match`` / ``sub`` /
    ``missing`` / ``extra``; the absent side's index is ``None``.
    Ties resolve diagonal (match/sub) > missing > extra.
    """
    n, m = len(expected), len(recognized)
    dist = [[0] * (m + 1) for _ in range(n + 1)]
    choice = [[0] * (m + 1) for _ in range(n + 1)]  # 0 diag, 1 missing, 2 extra
    for i in range(1, n + 1):
        dist[i][0] = i * _W_INDEL
        choice[i][0] = 1
    for j in range(1, m + 1):
        dist[0][j] = j * _W_INDEL
        choice[0][j] = 2
    for i in range(1, n + 1):
        exp_ch = expected[i - 1]
        for j in range(1, m + 1):
            diag = dist[i - 1][j - 1] + _substitution_cost_cents(exp_ch, recognized[j - 1])
            dele = dist[i - 1][j] + _W_INDEL
            ins = dist[i][j - 1] + _W_INDEL
            best, pick = diag, 0
            if dele < best:
                best, pick = dele, 1
            if ins < best:
                best, pick = ins, 2
            dist[i][j] = best
            choice[i][j] = pick
    ops = []
    i, j = n, m
    while i > 0 or j > 0:
        pick = choice[i][j]
        if pick == 0:
            kind = "match" if expected[i - 1] == recognized[j - 1] else "sub"
            ops.append((kind, i - 1, j - 1))
            i -= 1
            j -= 1
        elif pick == 1:
            ops.append(("missing", i - 1, None))
            i -= 1
        else:
            ops.append(("extra", None, j - 1))
            j -= 1
    ops.reverse()
    return dist[n][m], ops


def weighted_edit_distance(expected: str, recognized: str) -> float:
    """Minimum weighted edit cost between two (single-line) strings (§4.5)."""
    cents, _ = _char_edit_ops(normalize_text(expected), normalize_text(recognized))
    return cents / 100.0


def _classify_substitution(exp_ch: str, rec_ch: str) -> str:
    """§7.4: both Unicode decimal digits -> NUMERIC_CHANGE, else SUBSTITUTION."""
    if _is_decimal_digit(exp_ch) and _is_decimal_digit(rec_ch):
        return "NUMERIC_CHANGE"
    return "SUBSTITUTION"


# ---------------------------------------------------------------------------
# §7.2 / §4.4 line alignment
# ---------------------------------------------------------------------------

def pair_cost(expected_line: str, recognized_line: str) -> float:
    """Normalised pair cost ``c(i,j) = d_w / max(|e|, |o|, 1)`` (§7.2)."""
    cents, _ = _char_edit_ops(
        normalize_text(expected_line), normalize_text(recognized_line)
    )
    denom = max(len(normalize_text(expected_line)),
                len(normalize_text(recognized_line)), 1)
    return float(Fraction(cents, 100 * denom))


def _pair_cost_fraction(expected_line: str, recognized_line: str) -> Fraction:
    cents, _ = _char_edit_ops(expected_line, recognized_line)
    denom = max(len(expected_line), len(recognized_line), 1)
    return Fraction(cents, 100 * denom)


def _line_dp(m: int, n: int, pair, forbidden=frozenset()):
    """Global sequence DP over lines (§7.2).

    ``pair`` is an ``m x n`` matrix of ``Fraction`` costs or ``None``
    (``None`` = pairing excluded, e.g. cost above 0.70).  ``forbidden``
    is a set of ``(dest_i, dest_j, kind)`` transitions to exclude, used
    to compute the second-best alignment.  ``kind`` is ``pair`` /
    ``del`` (missing expected line) / ``ins`` (extra OCR line).
    Tie-break: pair > del > ins (§4.4).

    Returns ``(cost_table, choice_table)``.
    """
    cost = [[_BIG] * (n + 1) for _ in range(m + 1)]
    choice: list[list[Optional[str]]] = [[None] * (n + 1) for _ in range(m + 1)]
    cost[0][0] = Fraction(0)
    for i in range(1, m + 1):
        if (i, 0, "del") not in forbidden and cost[i - 1][0] < _BIG:
            cost[i][0] = cost[i - 1][0] + _GAP
            choice[i][0] = "del"
    for j in range(1, n + 1):
        if (0, j, "ins") not in forbidden and cost[0][j - 1] < _BIG:
            cost[0][j] = cost[0][j - 1] + _GAP
            choice[0][j] = "ins"
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            best = _BIG
            pick: Optional[str] = None
            if pair[i - 1][j - 1] is not None and (i, j, "pair") not in forbidden:
                cand = cost[i - 1][j - 1] + pair[i - 1][j - 1]
                if cand < best:
                    best, pick = cand, "pair"
            if (i, j, "del") not in forbidden:
                cand = cost[i - 1][j] + _GAP
                if cand < best:
                    best, pick = cand, "del"
            if (i, j, "ins") not in forbidden:
                cand = cost[i][j - 1] + _GAP
                if cand < best:
                    best, pick = cand, "ins"
            cost[i][j] = best
            choice[i][j] = pick
    return cost, choice


def _backtrack_alignment(choice, m: int, n: int):
    """Backtrack the line DP into ``(kind, exp_i, rec_j)`` ops, in order.

    ``kind`` is ``pair`` / ``missing`` (expected line without OCR pair)
    / ``extra`` (OCR line without expected pair).
    """
    ops = []
    i, j = m, n
    while i > 0 or j > 0:
        pick = choice[i][j]
        if pick == "pair":
            ops.append(("pair", i - 1, j - 1))
            i -= 1
            j -= 1
        elif pick == "del":
            ops.append(("missing", i - 1, None))
            i -= 1
        elif pick == "ins":
            ops.append(("extra", None, j - 1))
            j -= 1
        else:
            raise RuntimeError("unreachable cell in line alignment")
    ops.reverse()
    return ops


def _backward_dp(m: int, n: int, pair):
    """Backward DP (§7.2): ``back[i][j]`` is the minimum cost from cell
    ``(i, j)`` to ``(m, n)``.  Used to price alignments that contain a
    given pair."""
    back = [[_BIG] * (n + 1) for _ in range(m + 1)]
    back[m][n] = Fraction(0)
    for i in range(m - 1, -1, -1):
        back[i][n] = back[i + 1][n] + _GAP
    for j in range(n - 1, -1, -1):
        back[m][j] = back[m][j + 1] + _GAP
    for i in range(m - 1, -1, -1):
        for j in range(n - 1, -1, -1):
            best = back[i + 1][j] + _GAP
            cand = back[i][j + 1] + _GAP
            if cand < best:
                best = cand
            if pair[i][j] is not None:
                cand = pair[i][j] + back[i + 1][j + 1]
                if cand < best:
                    best = cand
            back[i][j] = best
    return back


def _second_best_cost(m: int, n: int, pair, forward, best_ops) -> Fraction:
    """Exact cost of the cheapest alignment with a *different pair set*
    from the best alignment.

    An alignment is determined by its set of paired ``(exp, ocr)``
    lines: unpaired expected lines are missing, unpaired OCR lines are
    extra.  Two DP paths that differ only by swapping adjacent delete /
    insert steps (``del`` then ``ins`` vs ``ins`` then ``del``) encode
    the *same* alignment, so they must not count as the "two best
    paths" of §4.4.  Every genuinely different alignment either lacks
    some pair of the best alignment or contains a pair the best one
    lacks, so the second-best cost is the minimum of:

    (a) for each pair of the best alignment, the best alignment that
        does not contain that pair (a DP run with that diagonal
        forbidden); and
    (b) for each allowed pair the best alignment lacks, the cheapest
        alignment containing it (forward cost to the pair + pair cost +
        backward cost from the pair).

    Returns ``_BIG`` when no different alignment exists.
    """
    best_pairs = {(i, j) for kind, i, j in best_ops if kind == "pair"}
    second = _BIG
    for (i, j) in best_pairs:
        cost, _ = _line_dp(m, n, pair, forbidden={(i + 1, j + 1, "pair")})
        if cost[m][n] < second:
            second = cost[m][n]
    back = _backward_dp(m, n, pair)
    for i in range(m):
        for j in range(n):
            if pair[i][j] is None or (i, j) in best_pairs:
                continue
            cand = forward[i][j] + pair[i][j] + back[i + 1][j + 1]
            if cand < second:
                second = cand
    return second


# ---------------------------------------------------------------------------
# OCR line records and reading order (§4.4, §7.1)
# ---------------------------------------------------------------------------

def _field(record: Any, name: str, default: Any) -> Any:
    if isinstance(record, dict):
        return record.get(name, default)
    return getattr(record, name, default)


def _as_list(value: Any) -> Optional[list]:
    if value is None:
        return None
    if isinstance(value, (list, tuple)):
        return list(value)
    return value


def _as_quad(value: Any) -> Optional[list]:
    if value is None:
        return None
    if isinstance(value, (list, tuple)):
        return [list(point) for point in value]
    return value


def _normalise_record(raw: Any, position: int) -> dict:
    text = _field(raw, "text", "")
    if text is None:
        text = ""
    if not isinstance(text, str):
        text = str(text)
    confidence = _field(raw, "confidence", None)
    if confidence is not None:
        confidence = float(confidence)
    bbox = _as_list(_field(raw, "bbox_xyxy", None))
    return {
        "line_index": _field(raw, "line_index", position),
        "text": text,
        "confidence": confidence,
        "bbox_xyxy": bbox,
        "quad": _as_quad(_field(raw, "quad", None)),
        "source_order": _field(raw, "source_order", position),
        "normalized": normalize_text(text),
    }


def _reading_order(records: list[dict]) -> list[dict]:
    """Sort OCR lines into reading order (§4.4): bbox vertical centre
    ascending, then bbox x1 ascending, then source order."""

    def key(item):
        position, record = item
        bbox = record["bbox_xyxy"]
        if isinstance(bbox, (list, tuple)) and len(bbox) == 4:
            centre_y = (float(bbox[1]) + float(bbox[3])) / 2.0
            x1 = float(bbox[0])
        else:
            centre_y = float("inf")
            x1 = float("inf")
        return (centre_y, x1, record["source_order"], record["line_index"])

    return [record for _, record in sorted(enumerate(records), key=key)]


# ---------------------------------------------------------------------------
# Report construction (§5, §7.4–§7.6)
# ---------------------------------------------------------------------------

def _char_errors_for_pair(error_no_start: int, exp_idx: int, rec_idx: int,
                          exp_line: str, rec_line: str,
                          record: dict) -> list[dict]:
    """Merge the character DP ops of one aligned line pair into error
    records (§4.5, §7.4, §7.5)."""
    _, ops = _char_edit_ops(exp_line, rec_line)
    errors: list[dict] = []
    error_no = error_no_start
    exp_pos = 0
    rec_pos = 0
    k = 0
    while k < len(ops):
        kind = ops[k][0]
        if kind == "match":
            exp_pos += 1
            rec_pos += 1
            k += 1
            continue
        start_exp, start_rec = exp_pos, rec_pos
        run = []
        while k < len(ops):
            op_kind, op_i, op_j = ops[k]
            if op_kind != kind:
                break
            if kind == "sub" and run:
                prev_i, prev_j = run[-1][1], run[-1][2]
                if _classify_substitution(exp_line[prev_i], rec_line[prev_j]) != \
                        _classify_substitution(exp_line[op_i], rec_line[op_j]):
                    break
            run.append(ops[k])
            k += 1
            if kind == "missing":
                exp_pos += 1
            elif kind == "extra":
                rec_pos += 1
            else:
                exp_pos += 1
                rec_pos += 1
        error_no += 1
        if kind == "missing":
            error_type = "MISSING_CHARACTER"
            exp_span = [start_exp, exp_pos]
            rec_span = [start_rec, start_rec]
            exp_frag = exp_line[start_exp:exp_pos]
            rec_frag = ""
        elif kind == "extra":
            error_type = "EXTRA_CHARACTER"
            exp_span = [start_exp, start_exp]
            rec_span = [start_rec, rec_pos]
            exp_frag = ""
            rec_frag = rec_line[start_rec:rec_pos]
        else:
            error_type = _classify_substitution(exp_line[start_exp], rec_line[start_rec])
            exp_span = [start_exp, exp_pos]
            rec_span = [start_rec, rec_pos]
            exp_frag = exp_line[start_exp:exp_pos]
            rec_frag = rec_line[start_rec:rec_pos]
        errors.append({
            "id": f"E{error_no:03d}",
            "type": error_type,
            "expected_line_index": exp_idx,
            "ocr_line_index": rec_idx,
            "expected_text": exp_line,
            "recognized_text": rec_line,
            "expected_span": exp_span,
            "recognized_span": rec_span,
            "expected_fragment": exp_frag,
            "recognized_fragment": rec_frag,
            "bbox_xyxy": record["bbox_xyxy"],
            "bbox_scope": "ocr_line",
            "confidence": record["confidence"],
        })
    return errors


def compare(expected_text: str,
            ocr_lines: Sequence[Any],
            image_info: Optional[dict] = None,
            tool_version: str = TOOL_VERSION) -> dict:
    """Compare expected text against OCR line records; build a
    ``textproof.report/v1`` report dict (§5).

    ``expected_text`` is the user's raw expected text.  ``ocr_lines``
    is a sequence of OCR line records (dicts or objects) with fields
    ``line_index`` / ``text`` / ``confidence`` / ``bbox_xyxy`` / ``quad``
    / ``source_order`` (the shapes of ``OCRLine`` in §7.1 / plan §5.1).
    ``image_info``, when given, supplies ``sha256`` / ``format`` /
    ``width`` / ``height`` for the report ``image`` block; unknown
    fields are ``null`` (the oracle reads no images).
    """
    if not isinstance(expected_text, str):
        raise TypeError("expected_text must be str")
    if image_info is not None and not isinstance(image_info, dict):
        raise TypeError("image_info must be a dict or None")

    raw_expected = expected_text
    expected_lines = split_normalized_lines(expected_text)

    records = [_normalise_record(raw, pos) for pos, raw in enumerate(ocr_lines)]
    ordered = _reading_order(records)
    for new_index, record in enumerate(ordered):
        record["line_index"] = new_index

    recognized_raw = "\n".join(record["text"] for record in ordered)
    recognized_lines = [record["normalized"] for record in ordered]

    # §7.6 warnings: one LOW_OCR_CONFIDENCE per line below 0.65.
    warnings: list[dict] = []
    for record in ordered:
        confidence = record["confidence"]
        if confidence is not None and confidence < LOW_CONFIDENCE_THRESHOLD:
            warnings.append({
                "code": "LOW_OCR_CONFIDENCE",
                "message": (
                    f"OCR line {record['line_index']} confidence "
                    f"{confidence:.2f} is below {LOW_CONFIDENCE_THRESHOLD:.2f}."
                ),
                "ocr_line_index": record["line_index"],
                "confidence": confidence,
            })

    usable_ocr = any(line != "" for line in recognized_lines)
    usable_expected = any(line != "" for line in expected_lines)

    errors: list[dict] = []
    if not usable_ocr:
        if usable_expected:
            verdict = "OCR_FAILED"
            warnings.append({
                "code": "OCR_EMPTY",
                "message": "OCR produced no usable text.",
            })
        else:
            verdict = "MATCH"
    else:
        m, n = len(expected_lines), len(recognized_lines)
        pair = [[None] * n for _ in range(m)]
        for i in range(m):
            for j in range(n):
                cost = _pair_cost_fraction(expected_lines[i], recognized_lines[j])
                pair[i][j] = cost if cost <= _HIGH_COST else None
        cost_table, choice_table = _line_dp(m, n, pair)
        best_ops = _backtrack_alignment(choice_table, m, n)
        second_best = _second_best_cost(m, n, pair, cost_table, best_ops)
        if second_best - cost_table[m][n] < _MARGIN:
            errors = [{
                "id": "E001",
                "type": "AMBIGUOUS_ALIGNMENT",
                "expected_line_index": None,
                "ocr_line_index": None,
                "expected_text": raw_expected,
                "recognized_text": recognized_raw,
                "expected_span": None,
                "recognized_span": None,
                "expected_fragment": "",
                "recognized_fragment": "",
                "bbox_xyxy": None,
                "bbox_scope": "none",
                "confidence": None,
            }]
            verdict = "REVIEW_REQUIRED"
        else:
            error_no = 0
            for kind, exp_i, rec_j in best_ops:
                if kind == "pair":
                    new_errors = _char_errors_for_pair(
                        error_no, exp_i, rec_j,
                        expected_lines[exp_i], recognized_lines[rec_j],
                        ordered[rec_j],
                    )
                    errors.extend(new_errors)
                    error_no += len(new_errors)
                elif kind == "missing":
                    error_no += 1
                    exp_line = expected_lines[exp_i]
                    errors.append({
                        "id": f"E{error_no:03d}",
                        "type": "MISSING_LINE",
                        "expected_line_index": exp_i,
                        "ocr_line_index": None,
                        "expected_text": exp_line,
                        "recognized_text": "",
                        "expected_span": [0, len(exp_line)],
                        "recognized_span": [0, 0],
                        "expected_fragment": exp_line,
                        "recognized_fragment": "",
                        "bbox_xyxy": None,
                        "bbox_scope": "none",
                        "confidence": None,
                    })
                else:  # extra OCR line
                    error_no += 1
                    rec_line = recognized_lines[rec_j]
                    record = ordered[rec_j]
                    errors.append({
                        "id": f"E{error_no:03d}",
                        "type": "EXTRA_LINE",
                        "expected_line_index": None,
                        "ocr_line_index": rec_j,
                        "expected_text": "",
                        "recognized_text": rec_line,
                        "expected_span": [0, 0],
                        "recognized_span": [0, len(rec_line)],
                        "expected_fragment": "",
                        "recognized_fragment": rec_line,
                        "bbox_xyxy": record["bbox_xyxy"],
                        "bbox_scope": "ocr_line",
                        "confidence": record["confidence"],
                    })
            if warnings:
                verdict = "REVIEW_REQUIRED"
            elif errors:
                verdict = "MISMATCH"
            else:
                verdict = "MATCH"

    info = image_info or {}
    report = {
        "schema": SCHEMA_ID,
        "tool_version": tool_version,
        "verdict": verdict,
        "image": {
            "sha256": info.get("sha256"),
            "format": info.get("format"),
            "width": info.get("width"),
            "height": info.get("height"),
            "coordinate_system": COORDINATE_SYSTEM,
        },
        "expected_text": raw_expected,
        "recognized_text": recognized_raw,
        "ocr_lines": [
            {
                "line_index": record["line_index"],
                "text": record["text"],
                "confidence": record["confidence"],
                "bbox_xyxy": record["bbox_xyxy"],
                "quad": record["quad"],
            }
            for record in ordered
        ],
        "errors": errors,
        "warnings": warnings,
        "summary": {
            "expected_lines": len(expected_lines),
            "ocr_lines": len(ordered),
            "error_count": len(errors),
            "warning_count": len(warnings),
        },
    }
    return report
