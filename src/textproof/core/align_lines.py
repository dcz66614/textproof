"""§4.4 / §7.2 line-sequence alignment (PROJECT_BOOK.md).

Global sequence DP over the expected-line sequence ``E`` and the
OCR-line sequence ``O``.  Pair cost is the normalised weighted edit
distance (§7.2)::

    c(i, j) = d_w(e_i, o_j) / max(|e_i|, |o_j|, 1)

with a fixed row gap penalty of **0.35** for inserting / deleting a
line.  A pair whose cost is strictly greater than **0.70** is never
paired: at that cost two gaps (0.35 + 0.35 = 0.70) are cheaper, so the
spec's "prefer missing + extra, do not force a per-character pairing"
(§4.4) is implemented by forbidding such pairs outright.  A pair at
exactly 0.70 is still allowed ("高于 0.70" is strict).

Ambiguity (§4.4, §7.2): if the two best *distinct alignments* differ
by less than **0.05**, the alignment is ambiguous.  "Distinct" is
counted over alignments (the set of paired lines), not over DP
paths: two paths that differ only in the order of consecutive gap
steps (e.g. missing-then-extra vs extra-then-missing for an unpaired
pair) are the *same* alignment, so they must not manufacture
ambiguity — otherwise every forbidden pair (cost > 0.70, resolved as
missing + extra) would be "ambiguous" by construction.

The second-best distinct alignment is computed exactly:

* (a) For each diagonal pair of the best alignment, the best cost
  with that pair forbidden.  Any alignment that drops that pair
  costs at least this much, and this alignment itself differs from
  the best one (it does not pair those two lines).
* (b) For each expected line and OCR line that the best alignment
  leaves unpaired, the cost of forcing that pair — prefix best +
  pair cost + suffix best, from the forward and backward DP tables.
  Any alignment that newly pairs those two lines costs at least this
  much.  Pairs costing more than 0.70 are excluded here too: §4.4
  forbids such pairings outright, so a high-cost pairing is not a
  competing alignment at all.

Every alignment differing from the best one either drops a best
diagonal pair (covered by (a)) or newly pairs two lines the best one
left unpaired (covered by (b): a line paired in the best alignment
cannot be paired a second time).  The second-best cost is the
minimum of all candidates; if there is no candidate at all (e.g. one
sequence is empty), it is infinite and the alignment is unambiguous.

Tie-break for the *chosen* (best) path (§4.4): match / substitution
(diagonal) first, then missing expected line, then extra OCR line.
Backtracking tests predecessors against the exact ``Fraction``
values stored by the forward DP.  Note the consequence for gap runs:
the backtrack decides the *last* step first, so a trailing
missing+extra run is emitted extra-then-missing in chronological
order; the pair *set* — which is what the report consumes — is the
same either way.

Exact arithmetic (R-01): every cost in this module is a
``Fraction`` of the exact decimal §4.5/§7.2 values (0.65, 0.50,
1.25, 0.35, 0.70, 0.05).  Binary floats of those decimals are
inexact, and a float DP accumulates summation-order error — e.g.
20 x 0.65 + 12 x 1.25 sums to 28.000000000000004, flipping both the
0.70 pairing threshold and the 0.05 ambiguity margin.  All
comparisons (threshold, backtrack equality, margin) therefore run
on ``Fraction`` values; the public API still returns ``float``
(``float(Fraction("0.65"))`` is bit-identical to the literal
``0.65``), so callers see no change except corrected decisions.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from fractions import Fraction
from typing import Final, Sequence

from textproof.core.weighted_edit import _weighted_edit_distance_fraction

__all__ = [
    "GAP_PENALTY",
    "AMBIGUITY_MARGIN",
    "HIGH_COST_PAIR_THRESHOLD",
    "AlignedPair",
    "LineAlignment",
    "pair_cost",
    "align_lines",
]

#: Fixed row insert / delete penalty (§4.4, §7.2).
GAP_PENALTY: Final[float] = 0.35
#: Two best alignment paths closer than this are ambiguous (§4.4, §7.2).
AMBIGUITY_MARGIN: Final[float] = 0.05
#: A pair costing more than this is never paired (§4.4).
HIGH_COST_PAIR_THRESHOLD: Final[float] = 0.70

# Exact-decimal twins of the frozen constants above, for all internal
# comparisons (R-01).  Built from the decimal string of each float so
# the two sets cannot drift: Fraction("0.35") == 7/20 exactly, while
# the float 0.35 is not.
_GAP_PENALTY: Final[Fraction] = Fraction(str(GAP_PENALTY))
_AMBIGUITY_MARGIN: Final[Fraction] = Fraction(str(AMBIGUITY_MARGIN))
_HIGH_COST_PAIR_THRESHOLD: Final[Fraction] = Fraction(
    str(HIGH_COST_PAIR_THRESHOLD)
)

_INF: Final[float] = math.inf


@dataclass(frozen=True)
class AlignedPair:
    """One step of the chosen line alignment.

    ``expected_index`` / ``ocr_index`` are ``None`` for an unpaired
    line (missing expected line / extra OCR line).  ``pair_cost`` is
    the §7.2 normalised cost for a paired step, ``None`` for a gap.
    """

    expected_index: int | None
    ocr_index: int | None
    pair_cost: float | None


@dataclass(frozen=True)
class LineAlignment:
    """Result of :func:`align_lines` (best path + ambiguity verdict)."""

    pairs: tuple[AlignedPair, ...]
    total_cost: float
    second_best_cost: float
    ambiguous: bool


def _pair_cost_fraction(
    expected_line: str, recognized_line: str
) -> Fraction | None:
    """§7.2 normalised pair cost as an exact ``Fraction``.

    Returns ``None`` when the exact cost exceeds
    :data:`HIGH_COST_PAIR_THRESHOLD` (forbidden pair).  The comparison
    is exact: a pair costing exactly 0.70 (e.g. 28/40) is allowed,
    where the old float division returned 0.7000000000000001 and
    wrongly forbade it (R-01 case A).
    """
    distance = _weighted_edit_distance_fraction(expected_line, recognized_line)
    cost = distance / max(len(expected_line), len(recognized_line), 1)
    if cost > _HIGH_COST_PAIR_THRESHOLD:
        return None
    return cost


def pair_cost(expected_line: str, recognized_line: str) -> float:
    """§7.2 normalised pair cost ``d_w / max(|e|, |o|, 1)``.

    Returns ``math.inf`` when the cost exceeds
    :data:`HIGH_COST_PAIR_THRESHOLD` (forbidden pair); callers that
    need the raw value should call ``weighted_edit_distance`` directly.
    The ``inf`` sentinel is what the DP uses to refuse the pairing.
    The threshold test itself is exact (see :func:`_pair_cost_fraction`).
    """
    cost = _pair_cost_fraction(expected_line, recognized_line)
    if cost is None:
        return _INF
    return float(cost)


def _pair_cost_matrix(
    expected_lines: Sequence[str], recognized_lines: Sequence[str]
) -> list[list[Fraction | None]]:
    """Exact pair costs; ``None`` marks a forbidden pair (> 0.70)."""
    return [
        [_pair_cost_fraction(e, o) for o in recognized_lines]
        for e in expected_lines
    ]


def _best_table(
    costs: list[list[Fraction | None]],
    m: int,
    n: int,
    forbidden: frozenset[tuple[int, int]] = frozenset(),
) -> list[list[Fraction]]:
    """Forward best-cost DP; ``forbidden`` diag cells are never paired.

    Every cell is reachable via gap steps, so the table is always
    finite — no infinity sentinel is needed inside it.  All arithmetic
    is exact ``Fraction`` arithmetic (R-01).
    """
    best: list[list[Fraction]] = [
        [Fraction(0)] * (n + 1) for _ in range(m + 1)
    ]
    best[0][0] = Fraction(0)
    for i in range(m + 1):
        for j in range(n + 1):
            if i == 0 and j == 0:
                continue
            candidates: list[Fraction] = []
            if (
                i > 0
                and j > 0
                and (i - 1, j - 1) not in forbidden
                and costs[i - 1][j - 1] is not None
            ):
                candidates.append(
                    best[i - 1][j - 1] + costs[i - 1][j - 1]  # type: ignore[operator]
                )
            if i > 0:
                candidates.append(best[i - 1][j] + _GAP_PENALTY)
            if j > 0:
                candidates.append(best[i][j - 1] + _GAP_PENALTY)
            best[i][j] = min(candidates)
    return best


def _suffix_best_table(
    costs: list[list[Fraction | None]], m: int, n: int
) -> list[list[Fraction]]:
    """Backward best-cost DP: ``suffix[i][j]`` aligns ``E[i:]`` to ``O[j:]``.

    Always finite (gap steps reach every cell); exact ``Fraction``
    arithmetic (R-01).
    """
    suffix: list[list[Fraction]] = [
        [Fraction(0)] * (n + 1) for _ in range(m + 1)
    ]
    suffix[m][n] = Fraction(0)
    for i in range(m, -1, -1):
        for j in range(n, -1, -1):
            if i == m and j == n:
                continue
            candidates: list[Fraction] = []
            if i < m and j < n and costs[i][j] is not None:
                candidates.append(
                    costs[i][j] + suffix[i + 1][j + 1]  # type: ignore[operator]
                )
            if i < m:
                candidates.append(_GAP_PENALTY + suffix[i + 1][j])
            if j < n:
                candidates.append(_GAP_PENALTY + suffix[i][j + 1])
            suffix[i][j] = min(candidates)
    return suffix


def align_lines(
    expected_lines: Sequence[str], recognized_lines: Sequence[str]
) -> LineAlignment:
    """Align normalised expected lines to normalised OCR lines (§7.2).

    ``expected_lines`` / ``recognized_lines`` must already be §4.3
    normalised (see :mod:`textproof.core.normalize`); this module does
    no text normalisation of its own.
    """
    expected = list(expected_lines)
    recognized = list(recognized_lines)
    m, n = len(expected), len(recognized)
    costs = _pair_cost_matrix(expected, recognized)

    # --- best-cost DP (for backtracking the chosen path) -------------
    best = _best_table(costs, m, n)

    # --- backtrack the best path: diagonal → missing → extra --------
    # Exact Fraction equality: the old float ``==`` re-computed a
    # drifting sum and could not correct it (R-01).
    pairs: list[AlignedPair] = []
    i, j = m, n
    while i > 0 or j > 0:
        if (
            i > 0
            and j > 0
            and costs[i - 1][j - 1] is not None
            and best[i][j]
            == best[i - 1][j - 1] + costs[i - 1][j - 1]  # type: ignore[operator]
        ):
            pairs.append(
                AlignedPair(i - 1, j - 1, float(costs[i - 1][j - 1]))  # type: ignore[arg-type]
            )
            i -= 1
            j -= 1
        elif i > 0 and best[i][j] == best[i - 1][j] + _GAP_PENALTY:
            pairs.append(AlignedPair(i - 1, None, None))
            i -= 1
        elif j > 0 and best[i][j] == best[i][j - 1] + _GAP_PENALTY:
            pairs.append(AlignedPair(None, j - 1, None))
            j -= 1
        else:  # pragma: no cover - unreachable if the table is consistent
            raise AssertionError(
                f"line-alignment backtrack stuck at ({i}, {j}): "
                "no predecessor reproduces the stored cost"
            )
    pairs.reverse()

    total = best[m][n]

    # --- second-best *distinct alignment* (see module docstring) ----
    # ``None`` means "no competing alignment exists" (infinite cost).
    second: Fraction | None = None
    # (a) Drop one diagonal pair of the best alignment.
    for pair in pairs:
        if pair.expected_index is not None and pair.ocr_index is not None:
            alt = _best_table(
                costs, m, n, frozenset({(pair.expected_index, pair.ocr_index)})
            )
            if second is None or alt[m][n] < second:
                second = alt[m][n]
    # (b) Newly pair two lines the best alignment left unpaired.
    paired_expected = {
        p.expected_index for p in pairs if p.expected_index is not None
    }
    paired_ocr = {p.ocr_index for p in pairs if p.ocr_index is not None}
    if len(paired_expected) < m and len(paired_ocr) < n:
        suffix = _suffix_best_table(costs, m, n)
        for ei in range(m):
            if ei in paired_expected:
                continue
            for oj in range(n):
                if oj in paired_ocr or costs[ei][oj] is None:
                    continue
                forced = (
                    best[ei][oj] + costs[ei][oj] + suffix[ei + 1][oj + 1]  # type: ignore[operator]
                )
                if second is None or forced < second:
                    second = forced

    # Exact margin test (R-01 case B): a gap of exactly 0.05 is NOT
    # ambiguous ("小于 0.05" is strict); the old float gap
    # 0.04999999999999993 wrongly fell below it.
    ambiguous = second is not None and (second - total) < _AMBIGUITY_MARGIN

    return LineAlignment(
        pairs=tuple(pairs),
        total_cost=float(total),
        second_best_cost=float(second) if second is not None else _INF,
        ambiguous=ambiguous,
    )
