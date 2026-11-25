"""§4.4 reading order (PROJECT_BOOK.md).

MVP rule, quoted from the spec: OCR boxes are aggregated into visual
rows by the vertical centre of the box and vertical overlap; within
one visual row boxes sort by x ascending; rows sort by y ascending.

Implementation (deterministic, no thresholds invented beyond the
spec's own words):

* A box's vertical interval is ``[y1, y2]`` from ``bbox_xyxy``.
* Boxes are visited in ``(centre_y, x1, source_order)`` order and
  greedily grouped: a box joins the current row iff its vertical
  interval overlaps the row's running interval (the union of the
  intervals of the boxes already in the row); otherwise it starts a
  new row.  "Longitudinal overlap" is the spec's grouping test, so
  interval overlap — not a centre-distance threshold — is used.
* Within a row, boxes sort by ``(x1, y1, source_order)``.
* Rows sort by ``(min y1 of the row, min centre_y, min source_order)``
  — "rows by y ascending", with deterministic tie-breaks.
* The returned lines are new :class:`OCRLine` objects: ``line_index``
  is reassigned 0..n-1 in reading order, ``source_order`` keeps the
  original OCR output order for audit, and text / confidence / bbox /
  quad are carried over unchanged.

This module never touches text content; normalisation is
:mod:`textproof.core.normalize`'s job.
"""

from __future__ import annotations

from typing import Sequence

from textproof.ocr.rapidocr_adapter import OCRLine

__all__ = ["order_lines", "line_vertical_center"]


def line_vertical_center(line: OCRLine) -> float:
    """Vertical centre of an OCR line box, in oriented-image pixels."""
    _, y1, _, y2 = line.bbox_xyxy
    return (y1 + y2) / 2.0


def order_lines(lines: Sequence[OCRLine]) -> list[OCRLine]:
    """Reorder OCR lines into reading order (§4.4) and reindex them.

    Returns new ``OCRLine`` objects in reading order with
    ``line_index`` 0..n-1; ``source_order`` preserves the input order.
    The input sequence is not mutated.
    """
    if not lines:
        return []

    # Visit in (centre_y, x1, source_order) order so grouping is
    # independent of the caller's input order.
    visiting = sorted(
        lines,
        key=lambda ln: (line_vertical_center(ln), ln.bbox_xyxy[0], ln.source_order),
    )

    rows: list[list[OCRLine]] = []
    row_intervals: list[list[float]] = []  # [min y1, max y2] per row
    for ln in visiting:
        _, y1, _, y2 = ln.bbox_xyxy
        if rows:
            lo, hi = row_intervals[-1]
            # Vertical-overlap test against the current (last) row only:
            # rows are visited top-to-bottom, so the current row is the
            # only one a new box can overlap.
            if y1 <= hi and y2 >= lo:
                rows[-1].append(ln)
                row_intervals[-1] = [min(lo, y1), max(hi, y2)]
                continue
        rows.append([ln])
        row_intervals.append([y1, y2])

    ordered: list[OCRLine] = []
    # Rows sort by y ascending (min y1), then min centre, then source order.
    row_order = sorted(
        range(len(rows)),
        key=lambda k: (
            row_intervals[k][0],
            min(line_vertical_center(ln) for ln in rows[k]),
            min(ln.source_order for ln in rows[k]),
        ),
    )
    for k in row_order:
        row = sorted(
            rows[k],
            key=lambda ln: (ln.bbox_xyxy[0], ln.bbox_xyxy[1], ln.source_order),
        )
        ordered.extend(row)

    return [
        OCRLine(
            line_index=i,
            text=ln.text,
            confidence=ln.confidence,
            bbox_xyxy=ln.bbox_xyxy,
            quad=ln.quad,
            source_order=ln.source_order,
        )
        for i, ln in enumerate(ordered)
    ]
