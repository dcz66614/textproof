"""Self-tests for the independent reference oracle (T006).

These tests use only the frozen specification, the S0 fixture manifest
and its expected-output file.  They never import the production
implementation (``textproof.core``) — see ``test_oracle_is_independent``.

Golden inputs are built from the manifest: for each S0 fixture the OCR
side is a single fixed line record carrying the fixture's drawn text,
with the line box taken from the manifest's ``target_region_xyxy``
(the task's stated construction, not a real OCR run).
"""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from oracle.reference_compare import (  # noqa: E402
    compare,
    normalize_text,
    pair_cost,
    split_normalized_lines,
    substitution_cost,
    weighted_edit_distance,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = REPO_ROOT / "tests" / "fixtures" / "s0" / "manifest.json"
EXPECTED_PATH = REPO_ROOT / "tests" / "fixtures" / "s0" / "expected_output.json"

S0_IDS = ["TP-S0-ZH-001", "TP-S0-ZH-002", "TP-S0-NUM-001", "TP-S0-ZH-003"]


@pytest.fixture(scope="module")
def manifest():
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def expected_output():
    return json.loads(EXPECTED_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def s0_entries(manifest):
    by_id = {entry["id"]: entry for entry in manifest["fixtures"]}
    return {fid: by_id[fid] for fid in S0_IDS}


def make_line(text, bbox, confidence=0.98, line_index=0, source_order=0):
    x1, y1, x2, y2 = bbox
    return {
        "line_index": line_index,
        "text": text,
        "confidence": confidence,
        "bbox_xyxy": list(bbox),
        "quad": [[x1, y1], [x2, y1], [x2, y2], [x1, y2]],
        "source_order": source_order,
    }


def image_info_for(entry):
    return {
        "sha256": entry["sha256"],
        "format": entry["format"],
        "width": entry["width"],
        "height": entry["height"],
    }


def compare_s0(entry):
    """One fixed OCR line carrying the drawn text, boxed at target_region."""
    line = make_line(entry["drawn_text"], entry["target_region_xyxy"])
    return compare(entry["expected_text"], [line],
                   image_info=image_info_for(entry))


# ---------------------------------------------------------------------------
# Independence (hard requirement of T006)
# ---------------------------------------------------------------------------

def test_oracle_is_independent():
    source = (REPO_ROOT / "oracle" / "reference_compare.py").read_text(
        encoding="utf-8")
    assert "import textproof" not in source
    assert "textproof.core" not in source
    import ast
    tree = ast.parse(source)
    stdlib = sys.stdlib_module_names
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] in stdlib, alias.name
        elif isinstance(node, ast.ImportFrom):
            assert (node.module or "").split(".")[0] in stdlib, node.module
    # The decisive check runs in a fresh interpreter: importing only the
    # oracle must not pull in the production package at all.  (Checking
    # sys.modules in-process would be order-dependent: other test modules
    # in a full-suite run import textproof.core first.)
    import subprocess
    code = (
        "import sys; sys.path.insert(0, %r); "
        "import oracle.reference_compare; "
        "assert 'textproof' not in sys.modules, 'oracle imports textproof'; "
        "assert 'textproof.core' not in sys.modules; "
        "print('oracle-standalone-ok')" % str(REPO_ROOT)
    )
    proc = subprocess.run([sys.executable, "-c", code],
                          capture_output=True, text=True, timeout=60)
    assert proc.returncode == 0, proc.stderr
    assert "oracle-standalone-ok" in proc.stdout


# ---------------------------------------------------------------------------
# §8.1 golden tests (the four fixed S0 samples)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("fixture_id", S0_IDS)
def test_s0_golden_matches_manifest_and_expected_output(
        fixture_id, s0_entries, expected_output):
    entry = s0_entries[fixture_id]
    expected = expected_output["fixtures"][fixture_id]
    # The two frozen files must agree with each other first.
    assert entry["expected_verdict"] == expected["verdict"]
    assert entry["expected_errors"] == expected["errors"]
    assert entry["expected_text"] == expected["expected_text"]
    assert entry["drawn_text"] == expected["drawn_text"]

    report = compare_s0(entry)

    assert report["schema"] == "textproof.report/v1"
    assert report["verdict"] == expected["verdict"]
    assert report["expected_text"] == entry["expected_text"]
    assert report["recognized_text"] == entry["drawn_text"]
    assert report["image"]["sha256"] == entry["sha256"]
    assert report["image"]["format"] == "PNG"
    assert report["image"]["width"] == 1200
    assert report["image"]["height"] == 480
    assert report["image"]["coordinate_system"] == "oriented_image_px_top_left"
    assert report["summary"] == expected["summary"]
    assert len(report["errors"]) == len(expected["errors"])
    for got, want in zip(report["errors"], expected["errors"]):
        assert got["type"] == want["type"]
        assert got["expected_fragment"] == want["expected_fragment"]
        assert got["recognized_fragment"] == want["recognized_fragment"]
        assert got["expected_span"] == want["expected_span"]
        assert got["recognized_span"] == want["recognized_span"]
        assert got["bbox_scope"] == want["bbox_scope"]
        # The error box is the OCR line box, which the test supplies as
        # the manifest target region.
        assert got["bbox_xyxy"] == list(entry["target_region_xyxy"])
        assert got["confidence"] == 0.98


def test_s0_zh_001_exactly_one_missing_character(s0_entries):
    report = compare_s0(s0_entries["TP-S0-ZH-001"])
    assert [e["type"] for e in report["errors"]] == ["MISSING_CHARACTER"]
    error = report["errors"][0]
    assert error["id"] == "E001"
    assert error["expected_fragment"] == "惠"
    assert error["recognized_fragment"] == ""
    assert error["expected_span"] == [3, 4]
    assert error["recognized_span"] == [3, 3]
    assert error["expected_line_index"] == 0
    assert error["ocr_line_index"] == 0


def test_s0_zh_002_exactly_one_substitution(s0_entries):
    report = compare_s0(s0_entries["TP-S0-ZH-002"])
    assert [e["type"] for e in report["errors"]] == ["SUBSTITUTION"]
    error = report["errors"][0]
    assert error["expected_fragment"] == "品"
    assert error["recognized_fragment"] == "口"
    assert error["expected_span"] == [1, 2]
    assert error["recognized_span"] == [1, 2]


def test_s0_num_001_exactly_one_numeric_change(s0_entries):
    report = compare_s0(s0_entries["TP-S0-NUM-001"])
    assert [e["type"] for e in report["errors"]] == ["NUMERIC_CHANGE"]
    error = report["errors"][0]
    assert error["expected_fragment"] == "8"
    assert error["recognized_fragment"] == "0"
    assert error["expected_span"] == [4, 5]
    assert error["recognized_span"] == [4, 5]


def test_s0_zh_003_missing_fragment_20(s0_entries):
    report = compare_s0(s0_entries["TP-S0-ZH-003"])
    missing = [e for e in report["errors"] if e["type"] == "MISSING_CHARACTER"]
    assert len(missing) >= 1
    # Consecutive missing characters merge into one record (§8.1 expects
    # fragment "20" as a single error).
    assert len(report["errors"]) == 1
    assert missing[0]["expected_fragment"] == "20"
    assert missing[0]["recognized_fragment"] == ""
    assert missing[0]["expected_span"] == [4, 6]
    assert missing[0]["recognized_span"] == [4, 4]


# ---------------------------------------------------------------------------
# §8.2 census: all 300 fixed fixtures, drawn text as the OCR line
# ---------------------------------------------------------------------------

def test_all_300_fixtures_verdict_and_error_types(manifest, expected_output):
    """Pure-compare census (no OCR run): each fixture's drawn text is fed
    as one fixed OCR line boxed at its target region.  Verdict and the
    multiset of error types must match expected_output for every fixture.
    Spans are deliberately NOT asserted here: with repeated characters a
    minimal alignment can sit at an equivalent position (e.g. which of
    two identical characters is "the" missing one)."""
    by_id = {entry["id"]: entry for entry in manifest["fixtures"]}
    assert len(by_id) == 300
    assert len(expected_output["fixtures"]) == 300
    mismatches = []
    for fixture_id, want in expected_output["fixtures"].items():
        entry = by_id[fixture_id]
        line = make_line(entry["drawn_text"], entry["target_region_xyxy"])
        report = compare(entry["expected_text"], [line],
                         image_info=image_info_for(entry))
        got_types = sorted(e["type"] for e in report["errors"])
        want_types = sorted(e["type"] for e in want["errors"])
        if report["verdict"] != want["verdict"] or got_types != want_types:
            mismatches.append(
                f"{fixture_id}: verdict got {report['verdict']} want "
                f"{want['verdict']}; types got {got_types} want {want_types}")
        if report["summary"]["error_count"] != len(want["errors"]):
            mismatches.append(
                f"{fixture_id}: error_count got "
                f"{report['summary']['error_count']} want {len(want['errors'])}")
    assert mismatches == []


# ---------------------------------------------------------------------------
# §4.3 normalisation
# ---------------------------------------------------------------------------

def test_normalize_fullwidth_ascii_and_space():
    assert normalize_text("ＡＢＣ１２３　ｘ") == "ABC123 x"
    line = make_line("ABC123 x", [0, 0, 100, 20])
    report = compare("ＡＢＣ１２３　ｘ", [line])
    assert report["verdict"] == "MATCH"
    assert report["errors"] == []


def test_normalize_nfc_newlines_and_whitespace():
    # e + combining acute -> precomposed e-acute; CRLF/CR -> LF; runs fold.
    assert normalize_text("café\r\n  a   b\tc ") == "café\na b c"
    assert normalize_text("a\rb") == "a\nb"
    assert split_normalized_lines("a\nb\nc") == ["a", "b", "c"]


def test_normalize_case_sensitive_and_punctuation_kept():
    # Long enough lines that the pairing survives the 0.70 rule (§4.4):
    # a 3-of-3 different short line would be missing+extra instead.
    line = make_line("xxabcyy", [0, 0, 100, 20])
    report = compare("xxABCyy", [line])
    assert report["verdict"] == "MISMATCH"
    # The three consecutive substitutions merge into one record.
    assert len(report["errors"]) == 1
    assert report["errors"][0]["type"] == "SUBSTITUTION"
    assert report["errors"][0]["expected_fragment"] == "ABC"
    assert report["errors"][0]["recognized_fragment"] == "abc"
    assert report["errors"][0]["expected_span"] == [2, 5]
    line2 = make_line("a", [0, 0, 100, 20])
    report2 = compare("a.", [line2])
    assert [e["type"] for e in report2["errors"]] == ["MISSING_CHARACTER"]
    assert report2["errors"][0]["expected_fragment"] == "."


def test_normalize_fullwidth_yen_not_mapped():
    # U+FFE5 is not an ASCII character, so it is left alone (§4.3 lists
    # full-width ASCII only).  Both sides map identically, so a matching
    # pair still matches; a half-width yen against a full-width yen differs.
    assert normalize_text("￥28.00") == "￥28.00"
    line = make_line("¥28.00", [0, 0, 100, 20])
    report = compare("￥28.00", [line])
    assert report["verdict"] == "MISMATCH"
    assert report["errors"][0]["type"] == "SUBSTITUTION"


def test_normalize_trailing_newline_is_a_trailing_empty_line():
    # Literal LF-separated segments (see module docstring, decision 2).
    assert split_normalized_lines("a\n") == ["a", ""]
    assert split_normalized_lines("") == [""]


# ---------------------------------------------------------------------------
# §4.5 weights and §7.4 classification
# ---------------------------------------------------------------------------

def test_weights():
    assert substitution_cost("O", "0") == 0.65
    assert substitution_cost("0", "O") == 0.65
    assert substitution_cost("I", "l") == 0.65
    assert substitution_cost("S", "5") == 0.65
    assert substitution_cost("B", "8") == 0.65
    assert substitution_cost("。", ".") == 0.50
    assert substitution_cost("，", ",") == 0.50
    assert substitution_cost("8", "0") == 1.25
    assert substitution_cost("a", "b") == 1.00
    assert substitution_cost("a", "a") == 0.0
    # Lowercase lookalikes are NOT in the spec's named confusion pairs.
    assert substitution_cost("o", "0") == 1.00
    assert substitution_cost("s", "5") == 1.00
    # Punctuation against a non-punctuation character is an ordinary swap.
    assert substitution_cost(".", "a") == 1.00
    # Non-decimal numerics (e.g. superscript two, category No) are not Nd.
    assert substitution_cost("²", "3") == 1.00


def test_weighted_edit_distance_values():
    assert weighted_edit_distance("abc", "abc") == 0.0
    assert weighted_edit_distance("8", "0") == 1.25
    assert weighted_edit_distance("a", "") == 1.00
    assert weighted_edit_distance("", "a") == 1.00
    assert weighted_edit_distance("O", "0") == 0.65
    assert weighted_edit_distance("。", ".") == 0.50


def test_confusion_pair_still_produces_an_error():
    # The lower confusion cost only affects alignment choice (§4.5):
    # different characters must still produce a difference record.
    line = make_line("O", [0, 0, 100, 20])
    report = compare("0", [line])
    assert [e["type"] for e in report["errors"]] == ["SUBSTITUTION"]
    assert report["errors"][0]["expected_fragment"] == "0"
    assert report["errors"][0]["recognized_fragment"] == "O"


def test_digit_substitution_is_numeric_change_not_substitution():
    line = make_line("28.00", [0, 0, 100, 20])
    report = compare("28.80", [line])
    assert [e["type"] for e in report["errors"]] == ["NUMERIC_CHANGE"]


def test_digit_missing_and_extra_stay_missing_extra():
    line = make_line("28.0", [0, 0, 100, 20])
    report = compare("28.80", [line])
    assert [e["type"] for e in report["errors"]] == ["MISSING_CHARACTER"]
    assert report["errors"][0]["expected_fragment"] == "8"
    line2 = make_line("28.800", [0, 0, 100, 20])
    report2 = compare("28.80", [line2])
    assert [e["type"] for e in report2["errors"]] == ["EXTRA_CHARACTER"]
    assert report2["errors"][0]["recognized_fragment"] == "0"


def test_mixed_substitution_run_splits_by_classified_type():
    # Padding keeps the pair cost (2.25 / 6 = 0.375) under the 0.70 rule.
    line = make_line("xxb0yy", [0, 0, 100, 20])
    report = compare("xxa8yy", [line])
    assert [(e["type"], e["expected_fragment"], e["recognized_fragment"])
            for e in report["errors"]] == [
        ("SUBSTITUTION", "a", "b"),
        ("NUMERIC_CHANGE", "8", "0"),
    ]


def test_consecutive_same_type_substitutions_merge():
    # Padding keeps the pair cost (2.00 / 6 = 0.333) under the 0.70 rule.
    line = make_line("xxcdyy", [0, 0, 100, 20])
    report = compare("xxabyy", [line])
    assert len(report["errors"]) == 1
    assert report["errors"][0]["type"] == "SUBSTITUTION"
    assert report["errors"][0]["expected_fragment"] == "ab"
    assert report["errors"][0]["recognized_fragment"] == "cd"
    assert report["errors"][0]["expected_span"] == [2, 4]
    assert report["errors"][0]["recognized_span"] == [2, 4]


# ---------------------------------------------------------------------------
# §4.4 / §7.2 line alignment, gap, high-cost pairs, ambiguity
# ---------------------------------------------------------------------------

def test_pair_cost_normalisation_and_high_cost_rule():
    assert pair_cost("ab", "ab") == 0.0
    assert pair_cost("abcd", "abce") == pytest.approx(0.25)
    # Cost above 0.70 must not force a character pairing: the lines are
    # reported as a missing expected line plus an extra OCR line.
    line = make_line("wxyz", [0, 0, 100, 20])
    report = compare("abcd", [line])
    assert sorted(e["type"] for e in report["errors"]) == [
        "EXTRA_LINE", "MISSING_LINE"]
    assert report["verdict"] == "MISMATCH"


def test_missing_line_bbox_is_null():
    line = make_line("第一行", [10, 10, 200, 40])
    report = compare("第一行\n第二行", [line])
    assert report["verdict"] == "MISMATCH"
    missing = [e for e in report["errors"] if e["type"] == "MISSING_LINE"]
    assert len(missing) == 1
    assert missing[0]["expected_line_index"] == 1
    assert missing[0]["ocr_line_index"] is None
    assert missing[0]["bbox_xyxy"] is None
    assert missing[0]["bbox_scope"] == "none"
    assert missing[0]["expected_fragment"] == "第二行"
    assert missing[0]["expected_span"] == [0, 3]
    assert missing[0]["recognized_span"] == [0, 0]
    assert missing[0]["confidence"] is None


def test_extra_line_keeps_ocr_bbox():
    bbox = [10, 50, 200, 80]
    lines = [make_line("第一行", [10, 10, 200, 40]),
             make_line("多余行", bbox)]
    report = compare("第一行", lines)
    extra = [e for e in report["errors"] if e["type"] == "EXTRA_LINE"]
    assert len(extra) == 1
    assert extra[0]["ocr_line_index"] == 1
    assert extra[0]["bbox_xyxy"] == bbox
    assert extra[0]["bbox_scope"] == "ocr_line"
    assert extra[0]["recognized_fragment"] == "多余行"
    assert extra[0]["recognized_span"] == [0, 3]


def test_reading_order_re_sorts_by_bbox():
    # Input order is deliberately not reading order: the box at y=100 is
    # given first, the box at y=10 second; reading order puts y=10 first.
    lower = make_line("第二行", [10, 100, 200, 130], line_index=1, source_order=1)
    upper = make_line("第一行", [10, 10, 200, 40], line_index=0, source_order=0)
    report = compare("第一行\n第二行", [lower, upper])
    assert report["verdict"] == "MATCH"
    assert [ln["text"] for ln in report["ocr_lines"]] == ["第一行", "第二行"]
    assert [ln["line_index"] for ln in report["ocr_lines"]] == [0, 1]


def test_reading_order_same_row_by_x():
    right = make_line("右", [300, 10, 400, 40], line_index=1, source_order=1)
    left = make_line("左", [10, 10, 100, 40], line_index=0, source_order=0)
    report = compare("左右", [right, left])
    # Two one-character lines on the same row pair with two expected lines
    # only if the expected text is two lines; here the single expected
    # line cannot pair with both, so this checks ordering, not pairing:
    assert report["ocr_lines"][0]["text"] == "左"
    assert report["ocr_lines"][1]["text"] == "右"


def test_ambiguous_duplicate_lines():
    # Two identical expected lines, one OCR line: either pairing costs
    # the same (0.35), so the best/second-best gap is 0 -> ambiguous.
    line = make_line("相同", [0, 0, 100, 20])
    report = compare("相同\n相同", [line])
    assert report["verdict"] == "REVIEW_REQUIRED"
    assert [e["type"] for e in report["errors"]] == ["AMBIGUOUS_ALIGNMENT"]
    assert report["errors"][0]["bbox_xyxy"] is None
    assert report["summary"]["error_count"] == 1


def test_ambiguity_boundary_not_ambiguous_at_exactly_margin():
    # Pair cost 0.65 vs delete+insert 0.70: gap exactly 0.05 is NOT
    # "less than 0.05", so the pairing stands.
    expected = "a" * 20
    recognized = "b" * 13 + "a" * 7
    assert pair_cost(expected, recognized) == pytest.approx(0.65)
    line = make_line(recognized, [0, 0, 100, 20])
    report = compare(expected, [line])
    assert report["verdict"] == "MISMATCH"
    assert all(e["type"] != "AMBIGUOUS_ALIGNMENT" for e in report["errors"])
    assert len(report["errors"]) == 1
    assert report["errors"][0]["type"] == "SUBSTITUTION"


def test_ambiguity_boundary_ambiguous_at_equal_cost():
    # Pair cost 0.70 equals delete+insert 0.70: gap 0 -> ambiguous.
    expected = "a" * 20
    recognized = "b" * 14 + "a" * 6
    assert pair_cost(expected, recognized) == pytest.approx(0.70)
    line = make_line(recognized, [0, 0, 100, 20])
    report = compare(expected, [line])
    assert report["verdict"] == "REVIEW_REQUIRED"
    assert [e["type"] for e in report["errors"]] == ["AMBIGUOUS_ALIGNMENT"]


def test_clear_match_is_not_ambiguous():
    line = make_line("完全一致", [0, 0, 100, 20])
    report = compare("完全一致", [line])
    assert report["verdict"] == "MATCH"
    assert report["errors"] == []
    assert report["warnings"] == []


def test_multiline_error_line_indices():
    lines = [make_line("第一行", [10, 10, 200, 40]),
             make_line("第二行X", [10, 50, 200, 80])]
    report = compare("第一行\n第二行", lines)
    assert report["verdict"] == "MISMATCH"
    assert len(report["errors"]) == 1
    error = report["errors"][0]
    assert error["type"] == "EXTRA_CHARACTER"
    assert error["expected_line_index"] == 1
    assert error["ocr_line_index"] == 1
    assert error["recognized_fragment"] == "X"


def test_object_style_ocr_lines_accepted():
    class Line:
        def __init__(self):
            self.line_index = 0
            self.text = "限时优"
            self.confidence = 0.98
            self.bbox_xyxy = (120, 180, 520, 252)
            self.quad = ((120, 180), (520, 180), (520, 252), (120, 252))
            self.source_order = 0

    report = compare("限时优惠", [Line()])
    assert report["verdict"] == "MISMATCH"
    assert report["errors"][0]["type"] == "MISSING_CHARACTER"
    assert report["errors"][0]["bbox_xyxy"] == [120, 180, 520, 252]
    assert report["errors"][0]["expected_fragment"] == "惠"


# ---------------------------------------------------------------------------
# §7.5 coordinates, §7.6 confidence and verdict
# ---------------------------------------------------------------------------

def test_char_error_bbox_is_the_ocr_line_box():
    bbox = [120, 180, 520, 252]
    line = make_line("新口上市", bbox)
    report = compare("新品上市", [line])
    assert report["errors"][0]["bbox_xyxy"] == bbox
    assert report["errors"][0]["bbox_scope"] == "ocr_line"


def test_low_confidence_warning_and_verdict_escalation():
    line = make_line("新口上市", [0, 0, 100, 20], confidence=0.5)
    report = compare("新品上市", [line])
    assert any(w["code"] == "LOW_OCR_CONFIDENCE" for w in report["warnings"])
    assert report["warnings"][0]["ocr_line_index"] == 0
    assert report["warnings"][0]["confidence"] == 0.5
    assert report["summary"]["warning_count"] == 1
    assert report["verdict"] == "REVIEW_REQUIRED"
    # The difference itself is still reported.
    assert [e["type"] for e in report["errors"]] == ["SUBSTITUTION"]


def test_low_confidence_without_errors_still_requires_review():
    line = make_line("一致", [0, 0, 100, 20], confidence=0.4)
    report = compare("一致", [line])
    assert report["errors"] == []
    assert report["verdict"] == "REVIEW_REQUIRED"
    assert report["warnings"][0]["code"] == "LOW_OCR_CONFIDENCE"


def test_confidence_threshold_is_strictly_below():
    line = make_line("一致", [0, 0, 100, 20], confidence=0.65)
    report = compare("一致", [line])
    assert report["warnings"] == []
    assert report["verdict"] == "MATCH"
    line2 = make_line("一致", [0, 0, 100, 20], confidence=0.64)
    report2 = compare("一致", [line2])
    assert len(report2["warnings"]) == 1
    assert report2["verdict"] == "REVIEW_REQUIRED"


def test_low_confidence_on_only_one_of_two_lines():
    lines = [make_line("第一行", [10, 10, 200, 40], confidence=0.98),
             make_line("第二行", [10, 50, 200, 80], confidence=0.3)]
    report = compare("第一行\n第二行", lines)
    assert len(report["warnings"]) == 1
    assert report["warnings"][0]["ocr_line_index"] == 1
    assert report["verdict"] == "REVIEW_REQUIRED"


def test_ocr_failed_when_no_usable_ocr():
    report = compare("限时优惠", [])
    assert report["verdict"] == "OCR_FAILED"
    assert report["errors"] == []
    assert [w["code"] for w in report["warnings"]] == ["OCR_EMPTY"]
    assert report["summary"] == {
        "expected_lines": 1, "ocr_lines": 0,
        "error_count": 0, "warning_count": 1,
    }
    assert report["recognized_text"] == ""


def test_ocr_blank_lines_are_not_usable_text():
    line = make_line("   ", [0, 0, 100, 20], confidence=0.99)
    report = compare("限时优惠", [line])
    assert report["verdict"] == "OCR_FAILED"
    assert [w["code"] for w in report["warnings"]] == ["OCR_EMPTY"]


def test_empty_expected_and_empty_ocr_is_match():
    report = compare("", [])
    assert report["verdict"] == "MATCH"
    assert report["errors"] == []
    assert report["warnings"] == []


def test_report_top_level_keeps_raw_texts():
    line = make_line("ＡＢＣ", [0, 0, 100, 20])
    report = compare("ＡＢＣ", [line])
    assert report["expected_text"] == "ＡＢＣ"
    assert report["recognized_text"] == "ＡＢＣ"
    assert report["verdict"] == "MATCH"


def test_image_info_defaults_to_nulls():
    line = make_line("一致", [0, 0, 100, 20])
    report = compare("一致", [line])
    assert report["image"] == {
        "sha256": None, "format": None, "width": None, "height": None,
        "coordinate_system": "oriented_image_px_top_left",
    }
    assert report["tool_version"] == "0.1.0"
