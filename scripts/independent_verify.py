"""Independent verification of one fixed S0 case (T006).

PROJECT_BOOK.md §8.4 item 3: an independent re-check from a clean
worktree that re-computes the image hash, opens the original PNG,
reads the expected text, runs live OCR, independently executes the
comparison and checks the output field by field.  This script does
NOT call ``verify_s0.py`` (or ``parity_check.py`` /
``compute_s0_metrics.py`` / ``validate_report_schema.py``); it
re-does the work with its own code path, importing only the
production compare (``textproof.core.report``), the Oracle
(``oracle.reference_compare``), the image loader and the OCR
adapter.

For ``--case`` (default ``TP-S0-ZH-001``) it performs:

1. Load the manifest record and the ``expected_output.json`` record
   for the case; fail if either is missing.
2. Read the original PNG bytes from disk; recompute SHA-256 and
   compare with the manifest; open the PNG with Pillow and check
   format (PNG), dimensions (1200x480) and that the bytes are a
   decodable static image.
3. Fixed-record path: feed the drawn text as a single OCR line
   record (bbox = manifest ``target_region_xyxy``) to BOTH the
   production compare and the Oracle, and check the result STRICTLY
   against ``expected_output.json`` — verdict, error count, error
   type, expected/recognized fragments, expected/recognized spans,
   bbox equal to the OCR line bbox, ``bbox_scope == "ocr_line"``.
4. Live-OCR path: run the RapidOCR adapter on the original PNG and
   print the VERBATIM recognized text, confidence, bbox and the full
   production report JSON.  Check that every expected error is
   PRESENT in the live report (same type, fragment and span) and
   that the live verdict is ``MISMATCH``; list any EXTRA live errors
   verbatim instead of deleting them.  Check IoU(live bbox,
   target_region) >= 0.80 and that the bbox stays inside the image.
5. Print the full Oracle report for the same live OCR lines, and
   check that the Oracle's live verdict and error types agree with
   production's on this case.

TP-S0-NUM-001 live note (see S0_REPORT.md §6(a)): live OCR reads
the drawn ``￥`` (U+FFE5) as ``¥`` (U+00A5), so the live report
contains one extra ``SUBSTITUTION`` in addition to the expected
``NUMERIC_CHANGE``.  The live check is therefore a SUBSET check
(expected errors present), not an exact-equality check; the extra
error is printed verbatim.  Use ``--strict-live`` to require exact
live equality instead (it fails on TP-S0-NUM-001 by design, and
demonstrates the finding).

Usage::

    python scripts/independent_verify.py --case TP-S0-ZH-001
    python scripts/independent_verify.py --case TP-S0-NUM-001 [--strict-live]

Exit code 0 iff the hash matches, the PNG opens, the fixed-record
strict check passes for both implementations, and the live subset
check (or strict check with --strict-live) passes.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))
sys.path.insert(0, str(REPO_ROOT))

from PIL import Image  # noqa: E402

import oracle.reference_compare as oracle  # noqa: E402
from textproof.core.report import build_report  # noqa: E402
from textproof.io.image_loader import load_image  # noqa: E402
from textproof.ocr.rapidocr_adapter import (  # noqa: E402
    OCRLine,
    RapidOCRAdapter,
)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def iou(box_a: list[float], box_b: list[float]) -> float:
    x1 = max(box_a[0], box_b[0])
    y1 = max(box_a[1], box_b[1])
    x2 = min(box_a[2], box_b[2])
    y2 = min(box_a[3], box_b[3])
    inter = max(0.0, x2 - x1) * max(0.0, y2 - y1)
    area_a = max(0.0, box_a[2] - box_a[0]) * max(0.0, box_a[3] - box_a[1])
    area_b = max(0.0, box_b[2] - box_b[0]) * max(0.0, box_b[3] - box_b[1])
    union = area_a + area_b - inter
    return inter / union if union > 0 else 0.0


def _canon_error(error: dict) -> dict:
    return {
        "type": error["type"],
        "expected_fragment": error["expected_fragment"],
        "recognized_fragment": error["recognized_fragment"],
        "expected_span": list(error["expected_span"])
        if error["expected_span"] is not None else None,
        "recognized_span": list(error["recognized_span"])
        if error["recognized_span"] is not None else None,
    }


def _strict_check(report: dict, expected: dict, fixture: dict,
                  impl_name: str, problems: list[str]) -> None:
    if report["verdict"] != expected["verdict"]:
        problems.append(f"[{impl_name}] verdict {report['verdict']} != "
                        f"{expected['verdict']}")
    got = report["errors"]
    want = expected["errors"]
    if len(got) != len(want):
        problems.append(f"[{impl_name}] error count {len(got)} != "
                        f"{len(want)}")
        return
    for got_err, want_err in zip(got, want):
        for field in ("type", "expected_fragment", "recognized_fragment"):
            if got_err[field] != want_err[field]:
                problems.append(
                    f"[{impl_name}] {field} {got_err[field]!r} != "
                    f"{want_err[field]!r}")
        if list(got_err["expected_span"]) != list(want_err["expected_span"]):
            problems.append(
                f"[{impl_name}] expected_span {got_err['expected_span']} != "
                f"{want_err['expected_span']}")
        if list(got_err["recognized_span"]) != list(
                want_err["recognized_span"]):
            problems.append(
                f"[{impl_name}] recognized_span {got_err['recognized_span']} "
                f"!= {want_err['recognized_span']}")
        if got_err["bbox_xyxy"] is None:
            problems.append(f"[{impl_name}] error bbox is null")
        elif [round(float(v), 2) for v in got_err["bbox_xyxy"]] != [
                float(v) for v in fixture["target_region_xyxy"]]:
            problems.append(
                f"[{impl_name}] fixed-path error bbox "
                f"{got_err['bbox_xyxy']} != target_region "
                f"{fixture['target_region_xyxy']}")
        if got_err.get("bbox_scope") != "ocr_line":
            problems.append(
                f"[{impl_name}] bbox_scope {got_err.get('bbox_scope')!r} != "
                "'ocr_line'")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Independent verification of one fixed S0 case (T006).")
    parser.add_argument("--case", default="TP-S0-ZH-001")
    parser.add_argument("--manifest", type=Path, default=None)
    parser.add_argument("--expected-output", type=Path, default=None)
    parser.add_argument("--strict-live", action="store_true",
                        help="Require the live report to equal the fixed "
                        "expected errors exactly (fails on TP-S0-NUM-001).")
    args = parser.parse_args(argv)

    fixtures_dir = REPO_ROOT / "tests" / "fixtures" / "s0"
    manifest_path = args.manifest or fixtures_dir / "manifest.json"
    expected_path = args.expected_output or fixtures_dir / "expected_output.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    expected_output = json.loads(expected_path.read_text(encoding="utf-8"))
    by_id = {f["id"]: f for f in manifest["fixtures"]}
    problems: list[str] = []

    if args.case not in by_id:
        print(f"case {args.case} not in manifest")
        return 2
    fixture = by_id[args.case]
    expected = expected_output["fixtures"].get(args.case)
    if expected is None:
        print(f"case {args.case} not in expected_output.json")
        return 2
    print(f"case: {args.case}")
    print(f"expected_text: {expected['expected_text']!r}")
    print(f"drawn_text: {expected['drawn_text']!r}")

    # 1-2. Hash + open the original PNG.
    png_path = fixtures_dir / fixture["filename"]
    data = png_path.read_bytes()
    actual_sha = sha256_bytes(data)
    print(f"PNG bytes: {len(data)} sha256: {actual_sha}")
    print(f"manifest sha256: {fixture['sha256']}")
    if actual_sha != fixture["sha256"]:
        problems.append("PNG SHA-256 does not match the manifest")
    with Image.open(png_path) as pil:
        print(f"PIL format: {pil.format} size: {pil.size} mode: {pil.mode}")
        if pil.format != "PNG" or list(pil.size) != [1200, 480]:
            problems.append(f"PIL image is {pil.format} {pil.size}, "
                            "expected PNG 1200x480")
        pil.load()

    # 3. Fixed-record path, both implementations, strict check.
    image = load_image(data)
    region = fixture["target_region_xyxy"]
    fixed_line = OCRLine(
        line_index=0, text=fixture["drawn_text"], confidence=0.99,
        bbox_xyxy=(float(region[0]), float(region[1]),
                   float(region[2]), float(region[3])),
        quad=((float(region[0]), float(region[1])),
              (float(region[2]), float(region[1])),
              (float(region[2]), float(region[3])),
              (float(region[0]), float(region[3]))),
        source_order=0)
    prod_fixed = build_report(image, fixture["expected_text"], [fixed_line])
    oracle_fixed = oracle.compare(
        fixture["expected_text"],
        [{"line_index": 0, "text": fixture["drawn_text"], "confidence": 0.99,
          "bbox_xyxy": [float(v) for v in region],
          "quad": [[float(region[0]), float(region[1])],
                   [float(region[2]), float(region[1])],
                   [float(region[2]), float(region[3])],
                   [float(region[0]), float(region[3])]],
          "source_order": 0}],
        image_info={"sha256": image.sha256_hex(), "format": image.format,
                    "width": image.width, "height": image.height})
    _strict_check(prod_fixed, expected, fixture, "production", problems)
    _strict_check(oracle_fixed, expected, fixture, "oracle", problems)
    print(f"fixed-record production: verdict={prod_fixed['verdict']} "
          f"errors={json.dumps(prod_fixed['errors'], ensure_ascii=False)}")
    print(f"fixed-record oracle: verdict={oracle_fixed['verdict']} "
          f"errors={json.dumps(oracle_fixed['errors'], ensure_ascii=False)}")

    # 4-5. Live OCR path.
    adapter = RapidOCRAdapter()
    print(f"ONNX providers: {json.dumps(adapter.providers)}")
    lines = adapter.recognize(image.pil_image)
    print(f"live OCR lines: {len(lines)}")
    for line in lines:
        print(f"  VERBATIM live OCR text: {line.text!r} "
              f"confidence={line.confidence:.5f} "
              f"bbox={[round(v, 2) for v in line.bbox_xyxy]}")
    prod_live = build_report(image, fixture["expected_text"], lines)
    print("VERBATIM live production report:")
    print(json.dumps(prod_live, indent=2, ensure_ascii=False))
    oracle_live = oracle.compare(
        fixture["expected_text"],
        [{"line_index": ln.line_index, "text": ln.text,
          "confidence": ln.confidence,
          "bbox_xyxy": [float(v) for v in ln.bbox_xyxy],
          "quad": [[float(p[0]), float(p[1])] for p in ln.quad],
          "source_order": ln.source_order} for ln in lines],
        image_info={"sha256": image.sha256_hex(), "format": image.format,
                    "width": image.width, "height": image.height})
    print(f"live oracle: verdict={oracle_live['verdict']} "
          f"errors={json.dumps(oracle_live['errors'], ensure_ascii=False)}")
    if oracle_live["verdict"] != prod_live["verdict"]:
        problems.append(
            f"live verdict differs: production {prod_live['verdict']} vs "
            f"oracle {oracle_live['verdict']}")
    if [_canon_error(e) for e in oracle_live["errors"]] != \
            [_canon_error(e) for e in prod_live["errors"]]:
        problems.append("live error lists differ between production and oracle")

    if len(lines) == 1:
        live_iou = iou([float(v) for v in lines[0].bbox_xyxy],
                       [float(v) for v in region])
        print(f"IoU(live bbox, target_region) = {live_iou:.3f} (>= 0.80 required)")
        if live_iou < 0.80:
            problems.append(f"live IoU {live_iou:.3f} < 0.80")
        bbox = lines[0].bbox_xyxy
        if bbox[0] < 0 or bbox[1] < 0 or bbox[2] > 1200 or bbox[3] > 480:
            problems.append(f"live bbox {bbox} outside image bounds")
    elif len(lines) == 0:
        problems.append("live OCR returned zero lines")
    else:
        problems.append(f"live OCR returned {len(lines)} lines, expected 1")

    if prod_live["verdict"] != "MISMATCH":
        problems.append(f"live verdict {prod_live['verdict']} != MISMATCH")
    want_canon = [_canon_error({"type": e["type"],
                                "expected_fragment": e["expected_fragment"],
                                "recognized_fragment": e["recognized_fragment"],
                                "expected_span": e["expected_span"],
                                "recognized_span": e["recognized_span"]})
                  for e in expected["errors"]]
    got_canon = [_canon_error(e) for e in prod_live["errors"]]
    missing = [w for w in want_canon if w not in got_canon]
    extra = [g for g in got_canon if g not in want_canon]
    if missing:
        problems.append(f"live report is missing expected errors: {missing}")
    if args.strict_live:
        if extra:
            problems.append(
                f"strict-live: extra live errors (verbatim): {extra}")
    else:
        if extra:
            print(f"NOTE: extra live errors (recorded verbatim, not deleted): "
                  f"{json.dumps(extra, ensure_ascii=False)}")

    if problems:
        print("INDEPENDENT VERIFICATION: FAIL")
        for problem in problems:
            print(f"  - {problem}")
        return 1
    print("INDEPENDENT VERIFICATION: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
