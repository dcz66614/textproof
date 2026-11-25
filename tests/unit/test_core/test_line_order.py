"""Golden tests: §4.4 reading order (PROJECT_BOOK.md)."""

from textproof.core.line_order import line_vertical_center, order_lines
from textproof.ocr.rapidocr_adapter import OCRLine


def make_line(text, x1, y1, x2, y2, source_order, confidence=0.98):
    return OCRLine(
        line_index=source_order,
        text=text,
        confidence=confidence,
        bbox_xyxy=(x1, y1, x2, y2),
        quad=((x1, y1), (x2, y1), (x2, y2), (x1, y2)),
        source_order=source_order,
    )


def test_empty_input_returns_empty():
    assert order_lines([]) == []


def test_single_line_keeps_index_zero_and_source_order():
    out = order_lines([make_line("a", 0, 0, 10, 10, 0)])
    assert len(out) == 1
    assert out[0].line_index == 0
    assert out[0].source_order == 0
    assert out[0].text == "a"


def test_rows_sorted_by_y_ascending():
    lines = [
        make_line("bottom", 0, 100, 50, 120, 2),
        make_line("top", 0, 0, 50, 20, 0),
        make_line("middle", 0, 50, 50, 70, 1),
    ]
    assert [ln.text for ln in order_lines(lines)] == ["top", "middle", "bottom"]


def test_same_row_sorted_by_x_ascending():
    lines = [
        make_line("right", 200, 0, 250, 20, 1),
        make_line("left", 0, 0, 50, 20, 0),
        make_line("mid", 100, 0, 150, 20, 2),
    ]
    assert [ln.text for ln in order_lines(lines)] == ["left", "mid", "right"]


def test_vertically_overlapping_boxes_group_into_one_row():
    # A [0,20] and B [5,25] overlap vertically -> one visual row,
    # ordered by x; C [100,120] is a second row.
    lines = [
        make_line("C", 0, 100, 50, 120, 2),
        make_line("B", 100, 5, 150, 25, 1),
        make_line("A", 0, 0, 50, 20, 0),
    ]
    assert [ln.text for ln in order_lines(lines)] == ["A", "B", "C"]


def test_non_overlapping_rows_stay_separate():
    lines = [
        make_line("row2", 0, 50, 50, 70, 1),
        make_line("row1", 0, 0, 50, 20, 0),
    ]
    assert [ln.text for ln in order_lines(lines)] == ["row1", "row2"]


def test_line_index_reassigned_in_reading_order_source_order_kept():
    lines = [
        make_line("second", 0, 50, 50, 70, 5),
        make_line("first", 0, 0, 50, 20, 3),
    ]
    out = order_lines(lines)
    assert [(ln.text, ln.line_index, ln.source_order) for ln in out] == [
        ("first", 0, 3),
        ("second", 1, 5),
    ]


def test_input_order_does_not_change_output():
    lines = [
        make_line("a", 0, 0, 50, 20, 0),
        make_line("b", 100, 0, 150, 20, 1),
        make_line("c", 0, 50, 50, 70, 2),
    ]
    assert order_lines(lines) == order_lines(list(reversed(lines)))


def test_input_sequence_is_not_mutated():
    lines = [
        make_line("b", 0, 50, 50, 70, 1),
        make_line("a", 0, 0, 50, 20, 0),
    ]
    before = list(lines)
    order_lines(lines)
    assert lines == before


def test_vertical_center():
    line = make_line("x", 10, 20, 30, 60, 0)
    assert line_vertical_center(line) == 40.0
