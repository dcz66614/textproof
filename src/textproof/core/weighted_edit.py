"""§4.5 / §7.3 character-level weighted edit distance (PROJECT_BOOK.md).

Frozen costs (§4.5 table — do not adjust):

===========================  =====
operation                    cost
===========================  =====
identical characters          0
visual-confusion substitution 0.65
punctuation substitution      0.50
digit-to-digit substitution   1.25
other substitution            1.00
missing character (deletion)  1.00
extra character (insertion)   1.00
===========================  =====

The DP is §7.3 exactly::

    D[i, j] = min(D[i-1, j] + 1,            # missing character
                  D[i, j-1] + 1,            # extra character
                  D[i-1, j-1] + w(e_i, o_j))  # match / substitution

Backtracking uses the fixed tie-break "diagonal (match /
substitution) → missing → extra", so the same input always yields the
same operation sequence and therefore the same report.

Literal readings:

* Confusion pairs are exactly the pairs the spec lists —
  ``O/0``, ``I/1``, ``I/l``, ``1/l``, ``S/5``, ``B/8`` — as
  unordered, case-sensitive pairs.  Lowercase ``o`` vs ``0`` is
  *not* listed (the spec mixes cases deliberately: capital ``I``,
  digit ``1``, lowercase ``l``), and §4.3 is case-sensitive, so it
  falls through to "other substitution" (1.00).  The spec introduces
  the list with "如" ("such as"), but no wider set is frozen anywhere,
  so the listed set — and only it — is implemented; widening it would
  be an unfrozen judgement call.
* "Punctuation substitution" (0.50) requires *both* characters to be
  Unicode punctuation (category ``P``).  A punctuation character
  replaced by a letter is "other substitution".
* "Digit" is Unicode decimal-digit category ``Nd`` (§7.4).  A
  digit-to-digit substitution costs 1.25 here; its *classification*
  (``NUMERIC_CHANGE``) lives in :mod:`textproof.core.classify`.
* A confusion pair's lower cost only influences which alignment the
  DP prefers.  A differing character *always* produces a difference
  record — the DP emits a ``substitute`` op for it and
  :mod:`textproof.core.classify` turns that op into an error (§4.5:
  "只要字符不同仍必须产生差异记录").
* Lengths and indices are Unicode code points (Python ``len`` on
  ``str``); spans are half-open ``[start, end)`` into the normalised
  text.
"""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass
from fractions import Fraction
from typing import Final, Literal

__all__ = [
    "COST_MATCH",
    "COST_CONFUSION",
    "COST_PUNCTUATION",
    "COST_DIGIT",
    "COST_SUBSTITUTION",
    "COST_DELETE",
    "COST_INSERT",
    "CONFUSION_PAIRS",
    "EditOp",
    "EditResult",
    "is_digit",
    "is_punctuation",
    "is_confusable",
    "substitution_cost",
    "weighted_edit_distance",
    "weighted_edit_ops",
]

#: Identical normalised characters (§4.5).
COST_MATCH: Final[float] = 0.0
#: Visual-confusion-pair substitution (§4.5).
COST_CONFUSION: Final[float] = 0.65
#: Punctuation-to-punctuation substitution (§4.5).
COST_PUNCTUATION: Final[float] = 0.50
#: Digit-to-digit substitution (§4.5).
COST_DIGIT: Final[float] = 1.25
#: Any other substitution (§4.5).
COST_SUBSTITUTION: Final[float] = 1.00
#: Missing character — expected char absent from OCR (§4.5, §7.3).
COST_DELETE: Final[float] = 1.00
#: Extra character — OCR char absent from expected (§4.5, §7.3).
COST_INSERT: Final[float] = 1.00

#: Unordered visual-confusion pairs, exactly as listed in §4.5.
CONFUSION_PAIRS: Final[frozenset[frozenset[str]]] = frozenset(
    frozenset(pair)
    for pair in (
        ("O", "0"),
        ("I", "1"),
        ("I", "l"),
        ("1", "l"),
        ("S", "5"),
        ("B", "8"),
    )
)

# Exact-decimal twins of the frozen §4.5 costs above.  The public
# constants stay ``float`` (the frozen API surface), but 0.65 / 0.50 /
# 1.25 are not exact in binary, so any DP that *accumulates* the float
# values drifts: e.g. 20 x 0.65 + 12 x 1.25 sums to
# 28.000000000000004 instead of 28, which flips a 0.70 threshold test
# and a 0.05 margin test (R-01).  All DP arithmetic in this module
# therefore runs on these ``Fraction`` values — the exact decimal
# costs the spec freezes — and converts back to ``float`` only at the
# public boundary, where ``float(Fraction("0.65"))`` is bit-identical
# to the literal ``0.65``.  The two sets must stay in sync: each
# Fraction is built from the decimal string of its float twin.
_FRACTION_MATCH: Final[Fraction] = Fraction(str(COST_MATCH))
_FRACTION_CONFUSION: Final[Fraction] = Fraction(str(COST_CONFUSION))
_FRACTION_PUNCTUATION: Final[Fraction] = Fraction(str(COST_PUNCTUATION))
_FRACTION_DIGIT: Final[Fraction] = Fraction(str(COST_DIGIT))
_FRACTION_SUBSTITUTION: Final[Fraction] = Fraction(str(COST_SUBSTITUTION))
_FRACTION_DELETE: Final[Fraction] = Fraction(str(COST_DELETE))
_FRACTION_INSERT: Final[Fraction] = Fraction(str(COST_INSERT))

OpKind = Literal["match", "substitute", "delete", "insert"]


@dataclass(frozen=True)
class EditOp:
    """One step of the backtracked edit script (§7.3).

    ``expected_index`` / ``recognized_index`` are code-point indices
    into the normalised expected / recognised strings; ``None`` marks
    the side that has no character for this op (``delete`` has no
    recognised character, ``insert`` has no expected character).
    """

    kind: OpKind
    expected_index: int | None
    recognized_index: int | None


@dataclass(frozen=True)
class EditResult:
    """Total weighted distance plus the deterministic op sequence."""

    distance: float
    ops: tuple[EditOp, ...]


def is_digit(ch: str) -> bool:
    """True iff ``ch`` is a Unicode decimal digit (category ``Nd``, §7.4)."""
    return unicodedata.category(ch) == "Nd"


def is_punctuation(ch: str) -> bool:
    """True iff ``ch`` is Unicode punctuation (category ``P``)."""
    return unicodedata.category(ch).startswith("P")


def is_confusable(a: str, b: str) -> bool:
    """True iff ``(a, b)`` is one of the frozen §4.5 confusion pairs."""
    if a == b:
        return False
    return frozenset((a, b)) in CONFUSION_PAIRS


def substitution_cost(a: str, b: str) -> float:
    """Frozen §4.5 cost of replacing normalised char ``a`` with ``b``.

    Precedence (the classes are disjoint except for the identical
    case, so order is documentation, not a judgement call): identical
    → confusion pair → digit-to-digit → punctuation-to-punctuation →
    other.
    """
    if a == b:
        return COST_MATCH
    if is_confusable(a, b):
        return COST_CONFUSION
    if is_digit(a) and is_digit(b):
        return COST_DIGIT
    if is_punctuation(a) and is_punctuation(b):
        return COST_PUNCTUATION
    return COST_SUBSTITUTION


def _substitution_cost_fraction(a: str, b: str) -> Fraction:
    """Exact-decimal twin of :func:`substitution_cost` (same precedence).

    Returns the frozen §4.5 cost as a ``Fraction`` so DP accumulation
    never sees binary float error (see the ``_FRACTION_*`` note above).
    """
    if a == b:
        return _FRACTION_MATCH
    if is_confusable(a, b):
        return _FRACTION_CONFUSION
    if is_digit(a) and is_digit(b):
        return _FRACTION_DIGIT
    if is_punctuation(a) and is_punctuation(b):
        return _FRACTION_PUNCTUATION
    return _FRACTION_SUBSTITUTION


def _weighted_edit_distance_fraction(expected: str, recognized: str) -> Fraction:
    """Minimum §7.3 weighted edit cost, computed in exact arithmetic.

    Same DP as :func:`_dp_table`, but every cell is a ``Fraction`` of
    the exact decimal §4.5 costs, so the result is the cost the spec
    freezes — not a float sum that has drifted by summation order.
    :mod:`textproof.core.align_lines` compares this value against the
    0.70 threshold and the 0.05 margin, so it must be exact.
    """
    return _dp_table_fraction(expected, recognized)[len(expected)][
        len(recognized)
    ]


def _dp_table_fraction(
    expected: str, recognized: str
) -> list[list[Fraction]]:
    """Full §7.3 DP table in exact ``Fraction`` arithmetic.

    Kept whole: backtracking needs every cell.  This is the single
    source of truth for the DP; :func:`_dp_table` is its float view.
    """
    m, n = len(expected), len(recognized)
    table: list[list[Fraction]] = [
        [Fraction(0)] * (n + 1) for _ in range(m + 1)
    ]
    for i in range(1, m + 1):
        table[i][0] = table[i - 1][0] + _FRACTION_DELETE
    for j in range(1, n + 1):
        table[0][j] = table[0][j - 1] + _FRACTION_INSERT
    for i in range(1, m + 1):
        e_ch = expected[i - 1]
        row = table[i]
        prev = table[i - 1]
        for j in range(1, n + 1):
            row[j] = min(
                prev[j] + _FRACTION_DELETE,
                row[j - 1] + _FRACTION_INSERT,
                prev[j - 1]
                + _substitution_cost_fraction(e_ch, recognized[j - 1]),
            )
    return table


def _dp_table(expected: str, recognized: str) -> list[list[float]]:
    """Full §7.3 DP table as floats (float view of the exact table).

    Kept for callers that need the table itself; the values are
    ``float()`` of the exact ``Fraction`` cells, so they agree with
    the exact arithmetic wherever the float is representable.
    """
    return [
        [float(cell) for cell in row]
        for row in _dp_table_fraction(expected, recognized)
    ]


def weighted_edit_distance(expected: str, recognized: str) -> float:
    """Minimum §7.3 weighted edit cost between two normalised strings.

    Computed in exact decimal arithmetic (see ``_FRACTION_*``) and
    converted to ``float`` at the boundary; the returned value is the
    spec's exact cost, not a drifted float sum.
    """
    return float(_weighted_edit_distance_fraction(expected, recognized))


def weighted_edit_ops(expected: str, recognized: str) -> EditResult:
    """Minimum-cost edit script, backtracked with the frozen tie-break.

    At each step the diagonal (match / substitution) is preferred over
    missing (deletion), which is preferred over extra (insertion).
    Equality is tested on the exact ``Fraction`` values the forward DP
    stored, so the backtrack follows a genuinely optimal path — the
    old float ``==`` re-computed the same drifting sum and could not
    correct it (R-01).
    """
    table = _dp_table_fraction(expected, recognized)
    m, n = len(expected), len(recognized)
    ops: list[EditOp] = []
    i, j = m, n
    while i > 0 or j > 0:
        if (
            i > 0
            and j > 0
            and table[i][j]
            == table[i - 1][j - 1]
            + _substitution_cost_fraction(expected[i - 1], recognized[j - 1])
        ):
            kind: OpKind = (
                "match" if expected[i - 1] == recognized[j - 1] else "substitute"
            )
            ops.append(EditOp(kind, i - 1, j - 1))
            i -= 1
            j -= 1
        elif i > 0 and table[i][j] == table[i - 1][j] + _FRACTION_DELETE:
            ops.append(EditOp("delete", i - 1, None))
            i -= 1
        elif j > 0 and table[i][j] == table[i][j - 1] + _FRACTION_INSERT:
            ops.append(EditOp("insert", None, j - 1))
            j -= 1
        else:  # pragma: no cover - unreachable if the table is consistent
            raise AssertionError(
                f"weighted-edit backtrack stuck at ({i}, {j}): "
                "no predecessor reproduces the stored cost"
            )
    ops.reverse()
    return EditResult(distance=float(table[m][n]), ops=tuple(ops))
