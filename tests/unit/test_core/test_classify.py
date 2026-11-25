"""Golden tests: error classification (§4.5, §7.4, §7.5)."""

from textproof.core.classify import (
    classify_substitution,
    diffs_for_aligned_pair,
    extra_line_difference,
    missing_line_difference,
)

BBOX = (120.0, 180.0, 520.0, 252.0)


def test_digit_to_digit_is_numeric_change():
    assert classify_substitution("8", "0") == "NUMERIC_CHANGE"
    assert classify_substitution("2", "0") == "NUMERIC_CHANGE"


def test_confusion_pair_is_substitution_not_numeric():
    # O->0 mixes letter and digit: not digit-to-digit.
    assert classify_substitution("O", "0") == "SUBSTITUTION"
    assert classify_substitution("S", "5") == "SUBSTITUTION"


def test_other_substitution():
    assert classify_substitution("品", "口") == "SUBSTITUTION"
    assert classify_substitution(",", ".") == "SUBSTITUTION"


def test_substitution_diff_fields():
    diffs = diffs_for_aligned_pair("新品上市", "新口上市", 0, 0, BBOX, 0.98)
    assert len(diffs) == 1
    diff = diffs[0]
    assert diff.type == "SUBSTITUTION"
    assert diff.expected_span == (1, 2)
    assert diff.recognized_span == (1, 2)
    assert diff.expected_fragment == "品"
    assert diff.recognized_fragment == "口"
    assert diff.bbox_xyxy == BBOX  # containing OCR *line* box
    assert diff.confidence == 0.98


def test_numeric_change_diff():
    diffs = diffs_for_aligned_pair("￥28.80", "￥28.00", 0, 0, BBOX, 0.97)
    assert len(diffs) == 1
    assert diffs[0].type == "NUMERIC_CHANGE"
    assert diffs[0].expected_span == (4, 5)
    assert diffs[0].recognized_span == (4, 5)
    assert diffs[0].expected_fragment == "8"
    assert diffs[0].recognized_fragment == "0"


def test_adjacent_missing_digits_merge_into_one_fragment_20():
    # §8.1 TP-S0-ZH-003: exactly one MISSING_CHARACTER, fragment "20".
    diffs = diffs_for_aligned_pair("新客立减20元", "新客立减元", 0, 0, BBOX, 0.98)
    assert len(diffs) == 1
    assert diffs[0].type == "MISSING_CHARACTER"
    assert diffs[0].expected_fragment == "20"
    assert diffs[0].recognized_fragment == ""
    assert diffs[0].expected_span == (4, 6)
    assert diffs[0].recognized_span == (4, 4)


def test_missing_digit_is_missing_character_not_numeric_change():
    diffs = diffs_for_aligned_pair("a1b", "ab", 0, 0, BBOX, 0.98)
    assert len(diffs) == 1
    assert diffs[0].type == "MISSING_CHARACTER"
    assert diffs[0].expected_fragment == "1"


def test_extra_digit_is_extra_character_not_numeric_change():
    diffs = diffs_for_aligned_pair("ab", "a1b", 0, 0, BBOX, 0.98)
    assert len(diffs) == 1
    assert diffs[0].type == "EXTRA_CHARACTER"
    assert diffs[0].recognized_fragment == "1"


def test_confusion_pair_is_still_reported_as_a_difference():
    diffs = diffs_for_aligned_pair("O", "0", 0, 0, BBOX, 0.98)
    assert len(diffs) == 1
    assert diffs[0].type == "SUBSTITUTION"
    assert diffs[0].expected_fragment == "O"
    assert diffs[0].recognized_fragment == "0"


def test_adjacent_same_type_substitutions_merge():
    diffs = diffs_for_aligned_pair("ab", "cd", 0, 0, BBOX, 0.98)
    assert len(diffs) == 1
    assert diffs[0].type == "SUBSTITUTION"
    assert diffs[0].expected_fragment == "ab"
    assert diffs[0].recognized_fragment == "cd"
    assert diffs[0].expected_span == (0, 2)


def test_type_change_splits_the_run():
    # Letter substitution then digit substitution: different types.
    diffs = diffs_for_aligned_pair("a8", "b9", 0, 0, BBOX, 0.98)
    assert [d.type for d in diffs] == ["SUBSTITUTION", "NUMERIC_CHANGE"]
    assert diffs[0].expected_fragment == "a"
    assert diffs[1].expected_fragment == "8"


def test_match_between_diffs_breaks_the_run():
    diffs = diffs_for_aligned_pair("aXb", "cXd", 0, 0, BBOX, 0.98)
    assert len(diffs) == 2
    assert diffs[0].expected_span == (0, 1)
    assert diffs[1].expected_span == (2, 3)


def test_identical_pair_has_no_diffs():
    assert diffs_for_aligned_pair("限时优惠", "限时优惠", 0, 0, BBOX, 0.98) == []


def test_missing_line_has_null_bbox_and_whole_line_span():
    diff = missing_line_difference("第二行", 1)
    assert diff.type == "MISSING_LINE"
    assert diff.expected_line_index == 1
    assert diff.ocr_line_index is None
    assert diff.expected_span == (0, 3)
    assert diff.recognized_span is None
    assert diff.expected_fragment == "第二行"
    assert diff.bbox_xyxy is None
    assert diff.confidence is None


def test_extra_line_carries_its_own_line_bbox():
    diff = extra_line_difference("第二行", 1, BBOX, 0.96)
    assert diff.type == "EXTRA_LINE"
    assert diff.expected_line_index is None
    assert diff.ocr_line_index == 1
    assert diff.expected_span is None
    assert diff.recognized_span == (0, 3)
    assert diff.recognized_fragment == "第二行"
    assert diff.bbox_xyxy == BBOX
    assert diff.confidence == 0.96
