"""Golden tests: §4.4 / §7.2 line alignment (PROJECT_BOOK.md)."""

import math
from fractions import Fraction

from textproof.core.align_lines import (
    AMBIGUITY_MARGIN,
    GAP_PENALTY,
    HIGH_COST_PAIR_THRESHOLD,
    align_lines,
    pair_cost,
)


def test_frozen_constants():
    assert GAP_PENALTY == 0.35
    assert AMBIGUITY_MARGIN == 0.05
    assert HIGH_COST_PAIR_THRESHOLD == 0.70


def test_pair_cost_identical_is_zero():
    assert pair_cost("限时优惠", "限时优惠") == 0.0


def test_pair_cost_normalised_by_max_length():
    # d_w = 1 (one deletion), max len 4 -> 0.25.
    assert pair_cost("限时优惠", "限时优") == 0.25


def test_pair_cost_over_threshold_is_forbidden():
    # d_w = 3, max len 3 -> 1.00 > 0.70.
    assert math.isinf(pair_cost("abc", "xyz"))


def test_pair_cost_exactly_070_is_allowed():
    # 7 substitutions out of 10 -> exactly 0.70: "高于 0.70" is strict.
    assert pair_cost("aaaaaaaaaa", "bbbbbbbaaa") == 0.70


def test_pair_cost_080_is_forbidden():
    assert math.isinf(pair_cost("aaaaaaaaaa", "bbbbbbbbaa"))


def test_pair_cost_exactly_070_with_confusion_and_digit_substitutions():
    # R-01 case A: 20 confusion substitutions (0.65) + 12 digit
    # substitutions (1.25) + 8 matches over 40 chars: exact distance
    # 28, exact pair cost 28/40 = 0.70, which "高于 0.70" (strict)
    # still allows.  The old float DP summed the distance to
    # 28.000000000000004, cost 0.7000000000000001, returned inf, and
    # align_lines split the row into MISSING_LINE + EXTRA_LINE.
    expected = "O" * 20 + "8" * 12 + "a" * 8
    recognized = "0" * 20 + "0" * 12 + "a" * 8
    assert pair_cost(expected, recognized) == 0.70
    result = align_lines([expected], [recognized])
    assert [(p.expected_index, p.ocr_index) for p in result.pairs] == [(0, 0)]
    assert result.pairs[0].pair_cost == 0.70
    assert result.total_cost == 0.70
    # Pairing (0.70) ties missing + extra (0.35 + 0.35 = 0.70), so the
    # two best distinct alignments differ by 0 < 0.05: ambiguous.
    assert result.second_best_cost == 0.70
    assert result.ambiguous is True


def test_ambiguity_margin_exactly_005_is_not_ambiguous():
    # R-01 case B: single "O" -> "0": best 0.65 (pair), second-best
    # 0.70 (missing + extra).  The exact gap is 0.05, and "小于 0.05"
    # is strict, so this is NOT ambiguous.  The old float gap was
    # 0.04999999999999993 and wrongly reported ambiguous=True.
    result = align_lines(["O"], ["0"])
    assert result.total_cost == 0.65
    assert result.second_best_cost == 0.70
    assert result.ambiguous is False


def test_gap_penalties_sum_to_exact_decimal():
    # R-01: three gap penalties must total exactly 1.05, not the
    # float sum 1.0499999999999998 the old DP produced.
    result = align_lines([], ["a", "a", "a"])
    assert result.total_cost == 1.05
    assert result.second_best_cost == math.inf
    assert result.ambiguous is False


def test_align_identical_lines():
    result = align_lines(["a", "b"], ["a", "b"])
    assert [(p.expected_index, p.ocr_index) for p in result.pairs] == [(0, 0), (1, 1)]
    assert result.total_cost == 0.0
    assert result.ambiguous is False


def test_align_missing_expected_line():
    result = align_lines(["a", "b"], ["a"])
    assert [(p.expected_index, p.ocr_index) for p in result.pairs] == [(0, 0), (1, None)]
    assert result.total_cost == 0.35
    assert result.ambiguous is False


def test_align_extra_ocr_line():
    result = align_lines(["a"], ["a", "b"])
    assert [(p.expected_index, p.ocr_index) for p in result.pairs] == [(0, 0), (None, 1)]
    assert result.total_cost == 0.35
    assert result.ambiguous is False


def test_align_high_cost_pair_becomes_missing_plus_extra():
    result = align_lines(["abc"], ["xyz"])
    # Chronological order is extra-then-missing: the backtrack decides
    # the *last* step first with priority diagonal > missing > extra,
    # so the last step is the missing line.  The pair *set* (one
    # missing line, one extra line) is what the report consumes.
    assert [(p.expected_index, p.ocr_index) for p in result.pairs] == [
        (None, 0),
        (0, None),
    ]
    assert result.total_cost == 0.70
    assert result.ambiguous is False


def test_align_cheap_pair_is_paired_not_gapped():
    # Pair cost 0.50 < two gaps (0.70): pair wins.
    result = align_lines(["ab"], ["b"])
    assert [(p.expected_index, p.ocr_index) for p in result.pairs] == [(0, 0)]
    assert result.total_cost == 0.50


def test_align_ambiguous_duplicate_ocr_line():
    # Pair either "a" + extra, or extra + pair: both cost 0.35.
    result = align_lines(["a"], ["a", "a"])
    assert result.total_cost == 0.35
    assert result.second_best_cost == 0.35
    assert result.ambiguous is True


def test_align_ambiguous_duplicate_expected_line():
    result = align_lines(["a", "a"], ["a"])
    assert result.total_cost == 0.35
    assert result.second_best_cost == 0.35
    assert result.ambiguous is True


def test_align_empty_sequences():
    result = align_lines([], [])
    assert result.pairs == ()
    assert result.total_cost == 0.0
    assert result.ambiguous is False


def test_align_expected_only_is_all_missing():
    result = align_lines(["a", "b"], [])
    assert [(p.expected_index, p.ocr_index) for p in result.pairs] == [
        (0, None),
        (1, None),
    ]
    assert result.total_cost == 0.70
    assert result.ambiguous is False


def test_align_ocr_only_is_all_extra():
    result = align_lines([], ["a"])
    assert [(p.expected_index, p.ocr_index) for p in result.pairs] == [(None, 0)]
    assert result.total_cost == 0.35


def test_align_is_deterministic():
    a = align_lines(["a", "x"], ["a", "a", "x"])
    b = align_lines(["a", "x"], ["a", "a", "x"])
    assert a == b


def test_align_multi_line_mixed_case():
    result = align_lines(
        ["第一行", "第二行", "第三行"], ["第一行", "第二行X", "第三行"]
    )
    assert [(p.expected_index, p.ocr_index) for p in result.pairs] == [
        (0, 0),
        (1, 1),
        (2, 2),
    ]
    assert result.ambiguous is False


def _brute_force_two_best(expected, recognized):
    """Enumerate every alignment; return the two smallest *distinct*
    (by pair set) costs.  Independent of the DP: a path is a sequence
    of diagonal / up / left steps, and two paths with the same set of
    diagonal pairs are the same alignment.

    Costs are exact ``Fraction`` values (R-01): a float brute force
    drifts the same way the old production code did — e.g. three gap
    penalties sum to 1.0499999999999998 instead of 1.05 — and would
    disagree with the exact production values on gap-only alignments.
    Returns ``(best, second)`` as Fractions; ``second`` is ``None``
    when no second distinct alignment exists.
    """
    from textproof.core.weighted_edit import _weighted_edit_distance_fraction

    m, n = len(expected), len(recognized)
    gap = Fraction(str(GAP_PENALTY))
    threshold = Fraction(str(HIGH_COST_PAIR_THRESHOLD))
    best_by_pairs: dict[frozenset, Fraction] = {}

    def rec(i, j, pairs, cost):
        if i == m and j == n:
            key = frozenset(pairs)
            if key not in best_by_pairs or cost < best_by_pairs[key]:
                best_by_pairs[key] = cost
            return
        if i < m and j < n:
            d = _weighted_edit_distance_fraction(expected[i], recognized[j])
            c = d / max(len(expected[i]), len(recognized[j]), 1)
            if c <= threshold:
                rec(i + 1, j + 1, pairs + [(i, j)], cost + c)
        if i < m:
            rec(i + 1, j, pairs, cost + gap)
        if j < n:
            rec(i, j + 1, pairs, cost + gap)

    rec(0, 0, [], Fraction(0))
    costs = sorted(best_by_pairs.values())
    second = costs[1] if len(costs) > 1 else None
    return costs[0], second


def test_second_best_matches_brute_force_on_exhaustive_small_cases():
    # Every expected/OCR sequence over {"a", "b"} up to length 3.
    alphabet = ["a", "b"]
    sequences: list[list[str]] = [[]]
    for length in (1, 2, 3):
        for combo in __import__("itertools").product(alphabet, repeat=length):
            sequences.append(list(combo))
    for expected in sequences:
        for recognized in sequences:
            result = align_lines(expected, recognized)
            brute_best, brute_second = _brute_force_two_best(expected, recognized)
            assert result.total_cost == float(brute_best), (expected, recognized)
            if brute_second is None:
                assert math.isinf(result.second_best_cost), (expected, recognized)
            else:
                assert result.second_best_cost == float(brute_second), (
                    expected,
                    recognized,
                )
            assert result.ambiguous == (
                brute_second is not None
                and (brute_second - brute_best)
                < Fraction(str(AMBIGUITY_MARGIN))
            ), (expected, recognized)
