"""Golden tests: §4.5 / §7.3 weighted edit distance (PROJECT_BOOK.md).

Every frozen weight is asserted by literal value, and the §7.3
backtrack tie-break is asserted on a case with two optimal scripts.
"""

from textproof.core.weighted_edit import (
    COST_CONFUSION,
    COST_DIGIT,
    COST_PUNCTUATION,
    COST_SUBSTITUTION,
    is_confusable,
    is_digit,
    is_punctuation,
    substitution_cost,
    weighted_edit_distance,
    weighted_edit_ops,
)


def test_frozen_cost_constants():
    assert COST_CONFUSION == 0.65
    assert COST_PUNCTUATION == 0.50
    assert COST_DIGIT == 1.25
    assert COST_SUBSTITUTION == 1.00


def test_identical_char_costs_zero():
    assert substitution_cost("a", "a") == 0.0
    assert substitution_cost("中", "中") == 0.0
    assert weighted_edit_distance("限时优惠", "限时优惠") == 0.0


def test_confusion_pairs_cost_065():
    for a, b in [("O", "0"), ("I", "1"), ("I", "l"), ("1", "l"), ("S", "5"), ("B", "8")]:
        assert is_confusable(a, b), (a, b)
        assert is_confusable(b, a), (b, a)
        assert substitution_cost(a, b) == 0.65, (a, b)


def test_lowercase_o_vs_zero_is_not_a_listed_confusion_pair():
    # §4.5 lists capital O only, and §4.3 is case-sensitive.
    assert not is_confusable("o", "0")
    assert substitution_cost("o", "0") == 1.00


def test_punctuation_substitution_costs_050():
    assert is_punctuation(",") and is_punctuation(".")
    assert is_punctuation("，") and is_punctuation("。")
    assert substitution_cost(",", ".") == 0.50
    assert substitution_cost("，", "。") == 0.50


def test_punctuation_vs_letter_is_other_substitution():
    assert not is_punctuation("a")
    assert substitution_cost(",", "a") == 1.00


def test_digit_to_digit_substitution_costs_125():
    assert is_digit("8") and is_digit("0")
    assert substitution_cost("8", "0") == 1.25
    assert substitution_cost("2", "0") == 1.25


def test_other_substitution_costs_100():
    assert substitution_cost("a", "b") == 1.00
    assert substitution_cost("品", "口") == 1.00
    assert substitution_cost("H", "h") == 1.00  # case-sensitive: not a match


def test_missing_and_extra_cost_100_each():
    assert weighted_edit_distance("abc", "ab") == 1.00
    assert weighted_edit_distance("ab", "abc") == 1.00
    assert weighted_edit_distance("", "abc") == 3.00
    assert weighted_edit_distance("abc", "") == 3.00


def test_classic_kitten_sitting_is_300():
    # k->s (1.00) + e->i (1.00) + insert g (1.00); rest matches.
    assert weighted_edit_distance("kitten", "sitting") == 3.00


def test_confusion_pair_still_costs_and_still_diffs():
    # Lower cost (0.65) must not erase the difference: distance > 0
    # and the op is a substitution, not a match.
    result = weighted_edit_ops("O", "0")
    assert result.distance == 0.65
    assert [(op.kind, op.expected_index, op.recognized_index) for op in result.ops] == [
        ("substitute", 0, 0)
    ]


def test_backtrack_prefers_diagonal_on_tie():
    # "ab" -> "ba": diagonal/diagonal = 2.00, delete+match+insert = 2.00.
    # The frozen tie-break (diagonal first) picks two substitutions.
    result = weighted_edit_ops("ab", "ba")
    assert result.distance == 2.00
    assert [op.kind for op in result.ops] == ["substitute", "substitute"]


def test_backtrack_delete_then_match():
    result = weighted_edit_ops("ab", "b")
    assert result.distance == 1.00
    assert [op.kind for op in result.ops] == ["delete", "match"]
    assert result.ops[0].expected_index == 0


def test_backtrack_insert_then_match():
    result = weighted_edit_ops("b", "ab")
    assert result.distance == 1.00
    assert [op.kind for op in result.ops] == ["insert", "match"]


def test_s0_missing_character_ops():
    result = weighted_edit_ops("限时优惠", "限时优")
    assert result.distance == 1.00
    assert [op.kind for op in result.ops] == ["match", "match", "match", "delete"]


def test_weighted_edit_distance_exact_decimal_accumulation():
    # R-01: 20 confusion substitutions (0.65) + 12 digit substitutions
    # (1.25) must total exactly 28.0.  The old float DP summed this to
    # 28.000000000000004, which flipped the 0.70 pair-cost threshold
    # in align_lines (case A).  The ops backtrack must still follow
    # the optimal all-diagonal path over the long accumulation.
    expected = "O" * 20 + "8" * 12
    recognized = "0" * 20 + "0" * 12
    assert weighted_edit_distance(expected, recognized) == 28.0
    result = weighted_edit_ops(expected, recognized)
    assert result.distance == 28.0
    assert [op.kind for op in result.ops] == ["substitute"] * 32
    assert [(op.expected_index, op.recognized_index) for op in result.ops] == [
        (i, i) for i in range(32)
    ]


def test_repeated_runs_give_identical_ops():
    a = weighted_edit_ops("ab", "ba")
    b = weighted_edit_ops("ab", "ba")
    assert a == b
