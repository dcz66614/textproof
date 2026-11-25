"""Golden tests: report assembly (PROJECT_BOOK.md §5.4, §7.6, §8.1).

All four fixed §8.1 S0 samples are covered here with fixed OCR line
records (no OCR engine, no images, no network — T004 completion
definition).  Spans, fragments, bbox rules and verdicts are asserted
literally against §8.1.
"""

import json

from textproof.contracts import ImageInput
from textproof.core.report import (
    LOW_CONFIDENCE_THRESHOLD,
    TOOL_VERSION,
    build_report,
    compare,
)
from textproof.io.image_loader import validate_expected_text
from textproof.ocr.rapidocr_adapter import OCRLine

LINE_BBOX = (120.0, 180.0, 520.0, 252.0)
LINE_QUAD = ((120.0, 180.0), (520.0, 180.0), (520.0, 252.0), (120.0, 252.0))


def make_line(text, line_index=0, confidence=0.98, bbox=LINE_BBOX, y=180.0):
    x1, _, x2, _ = bbox
    height = bbox[3] - bbox[1]
    box = (x1, y, x2, y + height)
    quad = ((x1, y), (x2, y), (x2, y + height), (x1, y + height))
    return OCRLine(
        line_index=line_index,
        text=text,
        confidence=confidence,
        bbox_xyxy=box,
        quad=quad,
        source_order=line_index,
    )


def make_image(data=b"fake-image-bytes"):
    return ImageInput(
        data=data,
        mime="image/png",
        format="PNG",
        width=1200,
        height=480,
        oriented=False,
        pil_image=None,
    )


# ---------------------------------------------------------------------------
# §8.1 fixed S0 samples
# ---------------------------------------------------------------------------


def test_s0_zh_001_missing_character():
    result = compare("限时优惠", [make_line("限时优")])
    assert result.verdict == "MISMATCH"
    assert result.summary == {
        "expected_lines": 1,
        "ocr_lines": 1,
        "error_count": 1,
        "warning_count": 0,
    }
    assert len(result.errors) == 1
    err = result.errors[0]
    assert err["id"] == "E001"
    assert err["type"] == "MISSING_CHARACTER"
    assert err["expected_line_index"] == 0
    assert err["ocr_line_index"] == 0
    assert err["expected_text"] == "限时优惠"
    assert err["recognized_text"] == "限时优"
    assert err["expected_span"] == [3, 4]
    assert err["recognized_span"] == [3, 3]
    assert err["expected_fragment"] == "惠"
    assert err["recognized_fragment"] == ""
    assert err["bbox_xyxy"] == list(LINE_BBOX)
    assert err["bbox_scope"] == "ocr_line"
    assert err["confidence"] == 0.98


def test_s0_zh_002_substitution():
    result = compare("新品上市", [make_line("新口上市")])
    assert result.verdict == "MISMATCH"
    assert len(result.errors) == 1
    err = result.errors[0]
    assert err["type"] == "SUBSTITUTION"
    assert err["expected_fragment"] == "品"
    assert err["recognized_fragment"] == "口"
    assert err["expected_span"] == [1, 2]
    assert err["recognized_span"] == [1, 2]
    assert err["bbox_xyxy"] == list(LINE_BBOX)


def test_s0_num_001_numeric_change():
    result = compare("￥28.80", [make_line("￥28.00")])
    assert result.verdict == "MISMATCH"
    assert len(result.errors) == 1
    err = result.errors[0]
    assert err["type"] == "NUMERIC_CHANGE"
    assert err["expected_fragment"] == "8"
    assert err["recognized_fragment"] == "0"
    assert err["expected_span"] == [4, 5]
    assert err["recognized_span"] == [4, 5]
    assert err["bbox_xyxy"] == list(LINE_BBOX)


def test_s0_zh_003_missing_20():
    result = compare("新客立减20元", [make_line("新客立减元")])
    assert result.verdict == "MISMATCH"
    assert len(result.errors) == 1
    err = result.errors[0]
    assert err["type"] == "MISSING_CHARACTER"
    assert err["expected_fragment"] == "20"
    assert err["recognized_fragment"] == ""
    assert err["expected_span"] == [4, 6]
    assert err["recognized_span"] == [4, 4]
    assert err["bbox_xyxy"] == list(LINE_BBOX)


# ---------------------------------------------------------------------------
# Verdicts (§7.6)
# ---------------------------------------------------------------------------


def test_exact_match():
    result = compare("限时优惠", [make_line("限时优惠")])
    assert result.verdict == "MATCH"
    assert result.errors == []
    assert result.warnings == []
    assert result.summary["error_count"] == 0


def test_low_confidence_on_diff_line_forces_review_required():
    assert LOW_CONFIDENCE_THRESHOLD == 0.65
    result = compare("新品上市", [make_line("新口上市", confidence=0.60)])
    assert result.verdict == "REVIEW_REQUIRED"
    assert len(result.errors) == 1
    assert result.errors[0]["type"] == "SUBSTITUTION"
    assert any(w["code"] == "LOW_OCR_CONFIDENCE" for w in result.warnings)
    assert result.warnings[0]["ocr_line_index"] == 0


def test_low_confidence_without_diffs_is_review_required_not_match():
    result = compare("限时优惠", [make_line("限时优惠", confidence=0.64)])
    assert result.verdict == "REVIEW_REQUIRED"
    assert result.errors == []
    assert len(result.warnings) == 1


def test_confidence_exactly_at_threshold_is_not_low():
    result = compare("限时优惠", [make_line("限时优惠", confidence=0.65)])
    assert result.verdict == "MATCH"
    assert result.warnings == []


def test_empty_ocr_is_ocr_failed_with_ocr_empty_warning():
    result = compare("限时优惠", [])
    assert result.verdict == "OCR_FAILED"
    assert result.errors == []
    assert [w["code"] for w in result.warnings] == ["OCR_EMPTY"]


def test_whitespace_only_ocr_is_ocr_failed():
    result = compare("限时优惠", [make_line("   ")])
    assert result.verdict == "OCR_FAILED"


def test_ambiguous_alignment_is_review_required_without_char_errors():
    # Either "a" could be the match; the two best paths tie at 0.35.
    result = compare("a", [make_line("a"), make_line("a", line_index=1, y=280.0)])
    assert result.verdict == "REVIEW_REQUIRED"
    assert len(result.errors) == 1
    err = result.errors[0]
    assert err["type"] == "AMBIGUOUS_ALIGNMENT"
    assert err["expected_line_index"] is None
    assert err["ocr_line_index"] is None
    assert err["bbox_xyxy"] is None
    assert err["expected_span"] is None
    assert err["recognized_span"] is None


# ---------------------------------------------------------------------------
# Line-level errors and coordinates (§4.6, §7.5)
# ---------------------------------------------------------------------------


def test_missing_line_error_has_null_bbox():
    lines = [make_line("第一行")]
    result = compare("第一行\n第二行", lines)
    assert result.verdict == "MISMATCH"
    assert len(result.errors) == 1
    err = result.errors[0]
    assert err["type"] == "MISSING_LINE"
    assert err["expected_line_index"] == 1
    assert err["ocr_line_index"] is None
    assert err["expected_span"] == [0, 3]
    assert err["recognized_span"] is None
    assert err["expected_fragment"] == "第二行"
    assert err["bbox_xyxy"] is None
    assert err["bbox_scope"] is None
    assert err["confidence"] is None


def test_extra_line_error_carries_its_own_line_bbox():
    lines = [make_line("第一行"), make_line("第二行", line_index=1, y=280.0)]
    result = compare("第一行", lines)
    assert result.verdict == "MISMATCH"
    assert len(result.errors) == 1
    err = result.errors[0]
    assert err["type"] == "EXTRA_LINE"
    assert err["expected_line_index"] is None
    assert err["ocr_line_index"] == 1
    assert err["recognized_fragment"] == "第二行"
    assert err["bbox_xyxy"] == [120.0, 280.0, 520.0, 352.0]
    assert err["bbox_scope"] == "ocr_line"


def test_unrelated_lines_are_not_forced_into_char_pairs():
    result = compare("abc", [make_line("xyz")])
    assert result.verdict == "MISMATCH"
    # Gap-run order is extra-then-missing (see test_align_lines);
    # the pair set is one missing line + one extra line.
    assert [e["type"] for e in result.errors] == ["EXTRA_LINE", "MISSING_LINE"]
    assert result.errors[0]["bbox_xyxy"] == list(LINE_BBOX)
    assert result.errors[1]["bbox_xyxy"] is None


def test_ocr_lines_are_reported_in_reading_order():
    lines = [
        make_line("第二行", line_index=1, y=280.0),
        make_line("第一行", line_index=0, y=180.0),
    ]
    result = compare("第一行\n第二行", lines)
    assert result.verdict == "MATCH"
    assert [ln["line_index"] for ln in result.ocr_lines] == [0, 1]
    assert [ln["text"] for ln in result.ocr_lines] == ["第一行", "第二行"]
    assert result.recognized_text == "第一行\n第二行"


# ---------------------------------------------------------------------------
# Normalisation end-to-end (§4.3) and raw-text retention (§4.3.6)
# ---------------------------------------------------------------------------


def test_fullwidth_expected_matches_halfwidth_ocr():
    result = compare("ＡＢＣ", [make_line("ABC")])
    assert result.verdict == "MATCH"
    assert result.errors == []


def test_case_difference_is_a_mismatch():
    result = compare("Hello", [make_line("hello")])
    assert result.verdict == "MISMATCH"
    assert len(result.errors) == 1
    assert result.errors[0]["type"] == "SUBSTITUTION"
    assert result.errors[0]["expected_span"] == [0, 1]


def test_nfc_expected_matches_composed_ocr():
    result = compare("e" + chr(0x301), [make_line(chr(0xE9))])
    assert result.verdict == "MATCH"


def test_report_keeps_raw_text_but_spans_index_normalised_text():
    result = compare("ＡＢＣ", [make_line("ABD")])
    assert result.expected_text == "ＡＢＣ"  # raw user text retained
    assert len(result.errors) == 1
    err = result.errors[0]
    assert err["expected_text"] == "ABC"  # normalised line text
    assert err["expected_span"] == [2, 3]
    assert err["expected_fragment"] == "C"


def test_compare_accepts_t002_expected_text_input():
    expected = validate_expected_text("限时优惠")
    result = compare(expected, [make_line("限时优")])
    assert result.verdict == "MISMATCH"
    assert result.errors[0]["type"] == "MISSING_CHARACTER"


# ---------------------------------------------------------------------------
# Full report (§5.4) and determinism
# ---------------------------------------------------------------------------


def test_build_report_shape_and_image_block():
    report = build_report(make_image(), "限时优惠", [make_line("限时优")])
    assert report["schema"] == "textproof.report/v1"
    assert report["tool_version"] == TOOL_VERSION == "0.1.0"
    assert report["verdict"] == "MISMATCH"
    assert report["image"]["format"] == "PNG"
    assert report["image"]["width"] == 1200
    assert report["image"]["height"] == 480
    assert report["image"]["coordinate_system"] == "oriented_image_px_top_left"
    import hashlib

    assert report["image"]["sha256"] == hashlib.sha256(b"fake-image-bytes").hexdigest()
    assert report["expected_text"] == "限时优惠"
    assert report["recognized_text"] == "限时优"
    assert report["ocr_lines"][0]["text"] == "限时优"
    assert report["ocr_lines"][0]["bbox_xyxy"] == list(LINE_BBOX)
    assert report["ocr_lines"][0]["quad"] == [list(p) for p in LINE_QUAD]
    assert len(report["errors"]) == 1
    assert report["warnings"] == []
    json.dumps(report)  # must be JSON-serialisable as-is


def test_same_input_produces_identical_json_semantics():
    kwargs = {"expected": "新客立减20元", "ocr_lines": [make_line("新客立减元")]}
    first = compare(**kwargs)
    second = compare(**kwargs)
    assert first == second
    assert json.dumps(first.__dict__, sort_keys=True) == json.dumps(
        second.__dict__, sort_keys=True
    )
    report_a = build_report(make_image(), "新品上市", [make_line("新口上市")])
    report_b = build_report(make_image(), "新品上市", [make_line("新口上市")])
    assert json.dumps(report_a, sort_keys=True) == json.dumps(report_b, sort_keys=True)


def test_error_ids_are_sequential_in_alignment_order():
    result = compare("aXbYc", [make_line("aPbQc")])
    assert [e["id"] for e in result.errors] == ["E001", "E002"]
    assert [e["expected_span"] for e in result.errors] == [[1, 2], [3, 4]]
