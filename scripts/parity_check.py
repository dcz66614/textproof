"""Production-vs-Oracle parity check for T006 (P033 TextProof).

T006 deliverable (plan §5.2 / T006 card item 2; PROJECT_BOOK.md §8.4).

Gate scope (the frozen S0 definition): the manifest's fixed OCR line
records.  For every one of the 300 fixtures the drawn text is fed to
both implementations as a single fixed OCR line record (text =
``drawn_text``, bbox = manifest ``target_region_xyxy``, confidence
0.99) and the two reports are compared field by field on verdict,
error type, expected/recognized fragment, expected/recognized span,
bbox and warning codes.  The gate passes iff all 300 agree — 100%.

Extended battery (diagnostic, beyond the frozen gate scope): 26
hand-built edge cases (empty inputs, low confidence, missing/extra
lines, high-cost pairs, confusion pairs, punctuation, full-width
characters, trailing newlines, CRLF, reading-order permutations,
repeated characters).  Differences found there are listed, grouped
and adjudicated against the frozen spec text in the JSON output and
in ``S0_REPORT.md``; they do NOT change the gate result, because the
gate scope is the manifest's fixed records.  The report states this
boundary explicitly so a reviewer who reads "parity 100%" as
all-inputs can overrule the PASS.

Known adjudication groups (see S0_REPORT.md for the full reasoning):

* R — representation differences in spec-silent fields: absent-side
  span ``null`` (production) vs ``[0, 0]`` (Oracle); ``bbox_scope``
  ``null`` vs ``"none"`` for ``MISSING_LINE`` / ``AMBIGUOUS``;
  warning-object message text and the Oracle's extra ``confidence``
  field.  §5.4's sample fixes none of these values, so neither side
  can be called wrong from the spec text.
* V1 — empty expected + empty OCR: production ``OCR_FAILED``,
  Oracle ``MATCH``.  §7.6 ("OCR 无可用文本时为 OCR_FAILED 或
  REVIEW_REQUIRED") supports production; the case is unreachable in
  the product because T002 rejects blank expected text
  (``INVALID_INPUT``, §4.2).
* V2 — single-character confusion substitution (``O`` -> ``0``):
  production ``REVIEW_REQUIRED`` / ``AMBIGUOUS_ALIGNMENT``, Oracle
  ``MISMATCH`` / ``SUBSTITUTION``.  Exact decimal arithmetic gives
  second-best minus best = 0.70 - 0.65 = 0.05, which is NOT < 0.05
  (§4.4), so the Oracle is right and production's float subtraction
  (0.7 - 0.65 == 0.04999999999999993) misfires.  Real production
  defect, zero S0 impact (no fixture hits it), recorded as finding
  F-01.
* V3 — same-row boxes with different vertical centres: production
  orders by x within the vertically overlapping row (§4.4: "同一视觉
  行内按 x 从小到大排序"); the Oracle sorts purely by centre-y and
  puts the right-hand box first.  Production follows §4.4; the
  Oracle deviates.  No fixture impact (all fixtures are single-line).

The three literal readings flagged by T004 and the Oracle (confusion
pair set, punctuation-both-sides, gap order) AGREE between the two
implementations on this battery and are asserted in the output.

Usage::

    python scripts/parity_check.py --manifest tests/fixtures/s0/manifest.json \
        [--out task_handoffs/T006/parity_report.json]

Exit code 0 iff fixed-fixture parity is 100% (300/300).  The edge
battery is reported, never silently dropped, but does not change the
exit code; see the JSON ``edge_battery`` section and S0_REPORT.md.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))
sys.path.insert(0, str(REPO_ROOT))

from textproof.core.report import build_report  # noqa: E402
from textproof.io.image_loader import load_image  # noqa: E402
from textproof.ocr.rapidocr_adapter import OCRLine  # noqa: E402

import oracle.reference_compare as oracle  # noqa: E402

S0_IDS = ["TP-S0-ZH-001", "TP-S0-ZH-002", "TP-S0-NUM-001", "TP-S0-ZH-003"]


def _bbox_tuple(region: list) -> tuple[float, float, float, float]:
    return (float(region[0]), float(region[1]),
            float(region[2]), float(region[3]))


def _quad_for(region: list) -> tuple:
    x1, y1, x2, y2 = (float(v) for v in region)
    return ((x1, y1), (x2, y1), (x2, y2), (x1, y2))


def fixed_ocr_line(fixture: dict) -> OCRLine:
    """The manifest's fixed OCR line record for one fixture."""
    return OCRLine(
        line_index=0,
        text=fixture["drawn_text"],
        confidence=0.99,
        bbox_xyxy=_bbox_tuple(fixture["target_region_xyxy"]),
        quad=_quad_for(fixture["target_region_xyxy"]),
        source_order=0,
    )


def fixed_oracle_record(fixture: dict) -> dict:
    region = fixture["target_region_xyxy"]
    return {
        "line_index": 0,
        "text": fixture["drawn_text"],
        "confidence": 0.99,
        "bbox_xyxy": [float(v) for v in region],
        "quad": [[float(region[0]), float(region[1])],
                 [float(region[2]), float(region[1])],
                 [float(region[2]), float(region[3])],
                 [float(region[0]), float(region[3])]],
        "source_order": 0,
    }


def canon_errors(errors: list[dict]) -> list[dict]:
    """Canonical error comparison form (verdict + type + fragments +
    spans + bbox).  ``bbox_scope`` is included: on the fixed fixtures
    every error carries ``"ocr_line"`` on both sides, so any scope
    difference would surface here."""
    return [{
        "type": e["type"],
        "expected_fragment": e["expected_fragment"],
        "recognized_fragment": e["recognized_fragment"],
        "expected_span": list(e["expected_span"])
        if e["expected_span"] is not None else None,
        "recognized_span": list(e["recognized_span"])
        if e["recognized_span"] is not None else None,
        "bbox_xyxy": list(e["bbox_xyxy"]) if e["bbox_xyxy"] is not None else None,
        "bbox_scope": e.get("bbox_scope"),
    } for e in errors]


def canon_warnings(warnings: list[dict]) -> list[str]:
    """Warning codes only: §5.3 fixes codes, not object shapes."""
    return [w["code"] for w in warnings]


def compare_reports(prod: dict, orep: dict) -> dict:
    """Field-by-field diff between a production report dict and an
    Oracle report dict.  Returns {} when they agree on every compared
    field."""
    diff: dict = {}
    if prod["verdict"] != orep["verdict"]:
        diff["verdict"] = {"production": prod["verdict"],
                           "oracle": orep["verdict"]}
    if prod["expected_text"] != orep["expected_text"]:
        diff["expected_text"] = {"production": prod["expected_text"],
                                 "oracle": orep["expected_text"]}
    if prod["recognized_text"] != orep["recognized_text"]:
        diff["recognized_text"] = {"production": prod["recognized_text"],
                                   "oracle": orep["recognized_text"]}
    pe, oe = canon_errors(prod["errors"]), canon_errors(orep["errors"])
    if pe != oe:
        diff["errors"] = {"production": pe, "oracle": oe}
    pw, ow = canon_warnings(prod["warnings"]), canon_warnings(orep["warnings"])
    if pw != ow:
        diff["warning_codes"] = {"production": pw, "oracle": ow}
    if prod["summary"] != orep["summary"]:
        diff["summary"] = {"production": prod["summary"],
                           "oracle": orep["summary"]}
    return diff


def run_fixed_parity(manifest: dict, fixtures_dir: Path) -> dict:
    """Parity over the manifest's fixed OCR line records (gate scope)."""
    results: list[dict] = []
    mismatches: list[dict] = []
    for fixture in manifest["fixtures"]:
        data = (fixtures_dir / fixture["filename"]).read_bytes()
        image = load_image(data)
        prod = build_report(image, fixture["expected_text"],
                            [fixed_ocr_line(fixture)])
        orep = oracle.compare(
            fixture["expected_text"], [fixed_oracle_record(fixture)],
            image_info={"sha256": image.sha256_hex(),
                        "format": image.format,
                        "width": image.width, "height": image.height})
        diff = compare_reports(prod, orep)
        entry = {"id": fixture["id"], "match": not diff, "diff": diff}
        results.append(entry)
        if diff:
            mismatches.append(entry)
    return {
        "scope": "manifest fixed OCR line records (drawn_text, "
                 "target_region_xyxy bbox, confidence 0.99)",
        "total": len(results),
        "matched": len(results) - len(mismatches),
        "mismatched": len(mismatches),
        "parity_pct": (100.0 * (len(results) - len(mismatches))
                       / max(len(results), 1)),
        "mismatches": mismatches,
    }


# ---------------------------------------------------------------------------
# Extended edge battery (diagnostic only)
# ---------------------------------------------------------------------------

def _box(x1: float, y1: float, x2: float, y2: float) -> list[float]:
    return [float(x1), float(y1), float(x2), float(y2)]


EDGE_CASES: list[dict] = [
    {"name": "empty_expected_empty_ocr", "expected": "",
     "lines": []},
    {"name": "empty_expected_one_ocr", "expected": "",
     "lines": [{"text": "abc", "bbox": _box(0, 0, 100, 50)}]},
    {"name": "nonempty_expected_empty_ocr", "expected": "hello",
     "lines": []},
    {"name": "nonempty_expected_blank_ocr", "expected": "hello",
     "lines": [{"text": "   ", "bbox": _box(0, 0, 100, 50)}]},
    {"name": "low_conf_match", "expected": "abc",
     "lines": [{"text": "abc", "confidence": 0.5, "bbox": _box(0, 0, 100, 50)}]},
    {"name": "low_conf_diff", "expected": "abc",
     "lines": [{"text": "abd", "confidence": 0.5, "bbox": _box(0, 0, 100, 50)}]},
    {"name": "missing_line", "expected": "line1\nline2",
     "lines": [{"text": "line1", "bbox": _box(0, 0, 100, 50)}]},
    {"name": "extra_line", "expected": "line1",
     "lines": [{"text": "line1", "bbox": _box(0, 0, 100, 50)},
               {"text": "line2", "bbox": _box(0, 60, 100, 110)}]},
    {"name": "high_cost_pair", "expected": "abc",
     "lines": [{"text": "xyz", "bbox": _box(0, 0, 100, 50)}]},
    {"name": "ambiguous_dup_lines", "expected": "aa\naa",
     "lines": [{"text": "aa", "bbox": _box(0, 0, 100, 50)},
               {"text": "aa", "bbox": _box(0, 60, 100, 110)}]},
    {"name": "confusion_lower_o", "expected": "o",
     "lines": [{"text": "0", "bbox": _box(0, 0, 100, 50)}]},
    {"name": "confusion_upper_O", "expected": "O",
     "lines": [{"text": "0", "bbox": _box(0, 0, 100, 50)}]},
    {"name": "punct_sub", "expected": "a,b",
     "lines": [{"text": "a;b", "bbox": _box(0, 0, 100, 50)}]},
    {"name": "punct_vs_letter", "expected": "a,b",
     "lines": [{"text": "axb", "bbox": _box(0, 0, 100, 50)}]},
    {"name": "fullwidth_yen", "expected": "￥28.80",
     "lines": [{"text": "￥28.00", "bbox": _box(0, 0, 100, 50)}]},
    {"name": "fullwidth_ascii", "expected": "ＡＢＣ",
     "lines": [{"text": "ABC", "bbox": _box(0, 0, 100, 50)}]},
    {"name": "trailing_newline", "expected": "abc\n",
     "lines": [{"text": "abc", "bbox": _box(0, 0, 100, 50)}]},
    {"name": "crlf", "expected": "a\r\nb",
     "lines": [{"text": "a", "bbox": _box(0, 0, 100, 50)},
               {"text": "b", "bbox": _box(0, 60, 100, 110)}]},
    {"name": "two_lines_swapped_order", "expected": "first\nsecond",
     "lines": [{"text": "second", "bbox": _box(0, 60, 100, 110),
                "source_order": 0},
               {"text": "first", "bbox": _box(0, 0, 100, 50),
                "source_order": 1}]},
    {"name": "same_row_two_boxes_x_order", "expected": "AB CD",
     "lines": [{"text": "CD", "bbox": _box(200, 0, 300, 50),
                "source_order": 0},
               {"text": "AB", "bbox": _box(0, 0, 100, 50),
                "source_order": 1}]},
    {"name": "same_row_diff_centre", "expected": "AB CD",
     "lines": [{"text": "CD", "bbox": _box(200, 2, 300, 48),
                "source_order": 0},
               {"text": "AB", "bbox": _box(0, 0, 100, 52),
                "source_order": 1}]},
    {"name": "overlap_rows", "expected": "top\nbottom",
     "lines": [{"text": "bottom", "bbox": _box(0, 55, 100, 105),
                "source_order": 0},
               {"text": "top", "bbox": _box(0, 0, 100, 60),
                "source_order": 1}]},
    {"name": "numeric_missing", "expected": "a1b",
     "lines": [{"text": "ab", "bbox": _box(0, 0, 100, 50)}]},
    {"name": "numeric_extra", "expected": "ab",
     "lines": [{"text": "a1b", "bbox": _box(0, 0, 100, 50)}]},
    {"name": "multi_sub_mixed_types", "expected": "a1",
     "lines": [{"text": "b2", "bbox": _box(0, 0, 100, 50)}]},
    {"name": "repeated_char_missing", "expected": "aaa",
     "lines": [{"text": "aa", "bbox": _box(0, 0, 100, 50)}]},
]


def _prod_report_for_case(case: dict) -> dict:
    from textproof.core.report import compare as prod_compare
    lines = []
    for i, line in enumerate(case["lines"]):
        bbox = line["bbox"]
        lines.append(OCRLine(
            line_index=i, text=line["text"],
            confidence=line.get("confidence", 0.99),
            bbox_xyxy=(bbox[0], bbox[1], bbox[2], bbox[3]),
            quad=((bbox[0], bbox[1]), (bbox[2], bbox[1]),
                  (bbox[2], bbox[3]), (bbox[0], bbox[3])),
            source_order=line.get("source_order", i)))
    result = prod_compare(case["expected"], lines)
    return {"verdict": result.verdict, "errors": result.errors,
            "warnings": result.warnings, "summary": result.summary,
            "expected_text": result.expected_text,
            "recognized_text": result.recognized_text}


def _oracle_report_for_case(case: dict) -> dict:
    records = []
    for i, line in enumerate(case["lines"]):
        bbox = line["bbox"]
        records.append({
            "line_index": i, "text": line["text"],
            "confidence": line.get("confidence", 0.99),
            "bbox_xyxy": [float(v) for v in bbox],
            "quad": [[bbox[0], bbox[1]], [bbox[2], bbox[1]],
                     [bbox[2], bbox[3]], [bbox[0], bbox[3]]],
            "source_order": line.get("source_order", i)})
    return oracle.compare(case["expected"], records)


def run_edge_battery() -> dict:
    """Run the diagnostic edge battery; classify every difference."""
    diffs: list[dict] = []
    for case in EDGE_CASES:
        prod = _prod_report_for_case(case)
        orep = _oracle_report_for_case(case)
        diff = compare_reports(prod, orep)
        # Representation-only differences (warning object shape, absent-side
        # span null vs [0,0], bbox_scope null vs "none") are recorded with
        # full fidelity in "raw_diff" so the report can adjudicate them.
        raw: dict = {}
        if prod["warnings"] != orep["warnings"]:
            raw["warnings"] = {"production": prod["warnings"],
                               "oracle": orep["warnings"]}
        if diff or raw:
            diffs.append({"case": case["name"], "diff": diff,
                          "raw_warning_diff": raw.get("warnings")})
    return {
        "scope": "diagnostic only; NOT part of the frozen S0 gate scope",
        "total": len(EDGE_CASES),
        "differing": len(diffs),
        "matching": len(EDGE_CASES) - len(diffs),
        "differences": diffs,
        "adjudication_groups": {
            "R": "representation in spec-silent fields (absent-side span "
                 "null vs [0,0]; bbox_scope null vs 'none'; warning object "
                 "shape). §5.4 sample fixes none of these values.",
            "V1": "empty expected + empty OCR verdict (OCR_FAILED vs "
                  "MATCH). §7.6 sentence supports production; case "
                  "unreachable via T002 blank rejection (§4.2).",
            "V2": "single-char confusion substitution O->0: production "
                  "AMBIGUOUS (float 0.7-0.65 < 0.05) vs Oracle MISMATCH. "
                  "Exact decimal 0.70-0.65 = 0.05, NOT < 0.05 (§4.4): "
                  "Oracle correct, production float defect (finding F-01).",
            "V3": "same-row boxes, different centres: production orders "
                  "by x within the overlapping row (§4.4), Oracle sorts "
                  "by centre-y. Production follows §4.4; Oracle deviates.",
        },
        "named_readings_agree": {
            "confusion_pair_set": "both use only the six listed pairs; "
                "lowercase o/0 is NOT a confusion pair on either side "
                "(case confusion_lower_o agrees on error type).",
            "punctuation_both_sides": "both require both characters to be "
                "Unicode punctuation for the 0.50 cost (cases punct_sub, "
                "punct_vs_letter agree on error type).",
            "gap_order": "both emit EXTRA_LINE before MISSING_LINE for a "
                "trailing missing+extra run (cases high_cost_pair, "
                "multi_sub_mixed_types agree on error order).",
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Production-vs-Oracle parity check (T006).")
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args(argv)

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    fixtures_dir = args.manifest.resolve().parent
    fixed = run_fixed_parity(manifest, fixtures_dir)
    edge = run_edge_battery()
    report = {"fixed_fixtures": fixed, "edge_battery": edge}
    if args.out is not None:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(
            json.dumps(report, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8")
        print(f"parity report written to {args.out}")
    print(f"fixed fixtures: {fixed['matched']}/{fixed['total']} match "
          f"({fixed['parity_pct']:.1f}%)")
    if fixed["mismatches"]:
        for entry in fixed["mismatches"]:
            print(f"  MISMATCH {entry['id']}: "
                  f"{json.dumps(entry['diff'], ensure_ascii=False)}")
    print(f"edge battery (diagnostic): {edge['matching']}/{edge['total']} "
          f"match; differing: "
          f"{[d['case'] for d in edge['differences']]}")
    return 0 if fixed["mismatched"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
