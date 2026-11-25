"""Live-OCR S0 metrics for the 300 fixed fixtures (T006).

T006 deliverable (plan §5.2 / T006 card items 4-6; PROJECT_BOOK.md
§8.2-§8.3).

Runs the production pipeline end to end on every fixture PNG:
T002 image loading -> T003 RapidOCR (CPU-only) -> T004 compare ->
§5 report.  For each fixture it records the live OCR text,
confidence, bbox, IoU against the manifest ``target_region_xyxy``,
the production report, the §5 schema verdict and the per-image
wall time.  From those it computes:

* detection recall (§8.3): injected character differences detected /
  injected character differences total, overall and per class
  (substitution / omission / numeric change).  An injected
  difference counts as detected iff the live report contains an
  error of the expected type whose ``expected_span`` COVERS the
  injected span and whose ``expected_fragment`` CONTAINS the injected
  fragment.  Coverage (not exact equality) is required because live
  OCR can misread a neighbouring character as well, widening the
  reported run without hiding the injected difference; the injected
  difference itself must still be present.  Injected character
  counts come from the manifest: one per substitution / numeric
  fixture, one per omission fixture except TP-S0-ZH-003 which
  injects two characters (``"20"``), i.e. 70 + 71 + 60 = 201.
  Recall is a property of the *detection* pipeline, never of the
  fixed-record path.
* clean false-positive rate (§8.3): clean fixtures whose live
  verdict is ``MISMATCH`` / 100 (strict literal reading).  The
  non-``MATCH`` rate (any other verdict) is reported alongside, so a
  ``REVIEW_REQUIRED`` on a clean image cannot hide inside the
  strict number.
* OCR CER (§8.3): ``(S + D + I) / N`` over all 300 fixtures, where
  S/D/I are substitution/deletion/insertion counts of the plain
  (unweighted) character edit distance between the live OCR text
  and the drawn text (both §4.3-normalised), and N is the total
  number of drawn characters.  CER is reported on its own and is
  NEVER used as a substitute for detection recall.
* IoU (§8.1): IoU(live OCR bbox, ``target_region_xyxy``) per fixture
  (single live line expected; if live OCR returns zero or multiple
  lines the fixture is recorded with ``iou: null`` and a note, and
  counts as an IoU failure).  Reported overall and for the 60-image
  blind subset separately, with min / mean / count below 0.80.
* JSON schema legality (§5): every live report validated with
  ``scripts/validate_report_schema.py``; 300/300 required.
* timing: per-image OCR+compare wall time (P50 / P95 / max).  The
  §8.3 runtime threshold (1920x1080, pre-warmed, P95 <= 5s) is NOT
  measured here — the frozen fixtures are 1200x480 — and is marked
  NOT_MEASURED for T011.

The live OCR results are cached as JSONL so ``verify_s0.py`` can
re-run scoring without re-running OCR; pass ``--force`` to re-run.

Usage::

    python scripts/compute_s0_metrics.py --manifest tests/fixtures/s0/manifest.json \
        --blind tests/fixtures/s0/blind_subset.json \
        --out task_handoffs/T006/s0_metrics.json \
        --live-results task_handoffs/T006/live_ocr_results.jsonl [--force]

Exit code 0 iff recall >= 95% overall, each class >= 90%, clean
FPR <= 8%, schema legality 100% and IoU >= 0.80 on every fixture.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import statistics
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))
sys.path.insert(0, str(REPO_ROOT))

from textproof.core.report import build_report  # noqa: E402
from textproof.io.image_loader import load_image  # noqa: E402
from textproof.ocr.rapidocr_adapter import RapidOCRAdapter  # noqa: E402

from scripts.validate_report_schema import validate_report  # noqa: E402

S0_IDS = ["TP-S0-ZH-001", "TP-S0-ZH-002", "TP-S0-NUM-001", "TP-S0-ZH-003"]
CLASS_OF_CATEGORY = {
    "substitution": "substitution",
    "omission": "omission",
    "numeric_change": "numeric_change",
}
EXPECTED_ERROR_TYPE = {
    "substitution": "SUBSTITUTION",
    "omission": "MISSING_CHARACTER",
    "numeric_change": "NUMERIC_CHANGE",
}


def iou(box_a: list[float], box_b: list[float]) -> float:
    """Intersection-over-union of two [x1, y1, x2, y2] boxes."""
    x1 = max(box_a[0], box_b[0])
    y1 = max(box_a[1], box_b[1])
    x2 = min(box_a[2], box_b[2])
    y2 = min(box_a[3], box_b[3])
    inter = max(0.0, x2 - x1) * max(0.0, y2 - y1)
    area_a = max(0.0, box_a[2] - box_a[0]) * max(0.0, box_a[3] - box_a[1])
    area_b = max(0.0, box_b[2] - box_b[0]) * max(0.0, box_b[3] - box_b[1])
    union = area_a + area_b - inter
    return inter / union if union > 0 else 0.0


def levenshtein_ops(a: str, b: str) -> tuple[int, int, int]:
    """Plain (unweighted) edit ops between ``a`` and ``b``.

    Returns (substitutions, deletions, insertions) for the transform
    a -> b.  Used ONLY for OCR CER (§8.3), never for detection recall.
    """
    n, m = len(a), len(b)
    dist = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        dist[i][0] = i
    for j in range(1, m + 1):
        dist[0][j] = j
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            dist[i][j] = min(
                dist[i - 1][j - 1] + (0 if a[i - 1] == b[j - 1] else 1),
                dist[i - 1][j] + 1,
                dist[i][j - 1] + 1)
    subs = dels = inss = 0
    i, j = n, m
    while i > 0 or j > 0:
        if i > 0 and j > 0 and dist[i][j] == dist[i - 1][j - 1] + (
                0 if a[i - 1] == b[j - 1] else 1):
            if a[i - 1] != b[j - 1]:
                subs += 1
            i -= 1
            j -= 1
        elif i > 0 and dist[i][j] == dist[i - 1][j] + 1:
            dels += 1
            i -= 1
        else:
            inss += 1
            j -= 1
    return subs, dels, inss


def _injected_chars(fixture: dict) -> list[dict]:
    """Injected character differences of one fixture, from the manifest.

    One entry per expected error: its type, expected span and expected
    fragment.  Character count = span length (ZH-003's "20" is 2)."""
    out = []
    for err in fixture.get("expected_errors", []):
        span = err["expected_span"]
        out.append({
            "type": err["type"],
            "expected_span": list(span),
            "expected_fragment": err["expected_fragment"],
            "chars": span[1] - span[0],
        })
    return out


def _detected(injected: dict, report_errors: list[dict]) -> bool:
    """True iff the live report contains the injected difference.

    The covering error must have the expected type, an expected_span
    covering the injected span, and an expected_fragment containing
    the injected fragment."""
    for err in report_errors:
        if err["type"] != injected["type"]:
            continue
        span = err["expected_span"]
        if span is None:
            continue
        if span[0] <= injected["expected_span"][0] \
                and span[1] >= injected["expected_span"][1] \
                and injected["expected_fragment"] in err["expected_fragment"]:
            return True
    return False


def run_live(manifest: dict, fixtures_dir: Path,
             live_results_path: Path, force: bool) -> list[dict]:
    """Run live OCR + compare over all fixtures (or reuse the cache)."""
    if live_results_path.exists() and not force:
        cached = [json.loads(line) for line in
                  live_results_path.read_text(encoding="utf-8").splitlines()
                  if line.strip()]
        if len(cached) == len(manifest["fixtures"]) and all(
                c["id"] == f["id"]
                for c, f in zip(cached, manifest["fixtures"])):
            print(f"reusing cached live OCR results: {live_results_path} "
                  f"({len(cached)} records)")
            return cached
        print("cached live results do not match the manifest; re-running OCR")

    adapter = RapidOCRAdapter()
    print(f"ONNX providers: {json.dumps(adapter.providers)}")
    print(f"model route: {json.dumps(adapter.model_info, ensure_ascii=False)}")
    results: list[dict] = []
    for fixture in manifest["fixtures"]:
        t0 = time.perf_counter()
        data = (fixtures_dir / fixture["filename"]).read_bytes()
        image = load_image(data)
        lines = adapter.recognize(image.pil_image)
        report = build_report(image, fixture["expected_text"], lines)
        elapsed = time.perf_counter() - t0
        ocr_text = "\n".join(ln.text for ln in lines)
        ocr_bboxes = [[round(v, 2) for v in ln.bbox_xyxy] for ln in lines]
        iou_value = None
        iou_note = ""
        if len(lines) == 1:
            iou_value = iou(ocr_bboxes[0],
                            [float(v) for v in fixture["target_region_xyxy"]])
        elif len(lines) == 0:
            iou_note = "live OCR returned zero lines"
        else:
            iou_note = f"live OCR returned {len(lines)} lines (expected 1)"
        results.append({
            "id": fixture["id"],
            "category": fixture["category"],
            "sha256": image.sha256_hex(),
            "manifest_sha256": fixture["sha256"],
            "sha_match": image.sha256_hex() == fixture["sha256"],
            "expected_text": fixture["expected_text"],
            "drawn_text": fixture["drawn_text"],
            "ocr_text": ocr_text,
            "ocr_confidence": [round(ln.confidence, 5) for ln in lines],
            "ocr_bboxes": ocr_bboxes,
            "ocr_line_count": len(lines),
            "iou": iou_value,
            "iou_note": iou_note,
            "target_region_xyxy": fixture["target_region_xyxy"],
            "verdict": report["verdict"],
            "errors": report["errors"],
            "warnings": report["warnings"],
            "report": report,
            "seconds": round(elapsed, 4),
        })
    live_results_path.parent.mkdir(parents=True, exist_ok=True)
    with open(live_results_path, "w", encoding="utf-8") as fh:
        for row in results:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"live OCR results written to {live_results_path} "
          f"({len(results)} records)")
    return results


def score(results: list[dict], manifest: dict,
          blind_ids: set[str]) -> dict:
    """Score live results into the §8.3 metrics."""
    by_id = {f["id"]: f for f in manifest["fixtures"]}
    injected_total = 0
    detected_total = 0
    per_class: dict[str, dict[str, int]] = {
        cls: {"injected": 0, "detected": 0} for cls in CLASS_OF_CATEGORY}
    clean_total = clean_mismatch = clean_non_match = 0
    cer_subs = cer_dels = cer_inss = cer_n = 0
    ious: list[float] = []
    blind_ious: list[float] = []
    iou_failures: list[dict] = []
    schema_bad: list[dict] = []
    missed: list[dict] = []
    s0_live: dict[str, dict] = {}
    times: list[float] = []
    for row in results:
        fixture = by_id[row["id"]]
        times.append(row["seconds"])
        violations = validate_report(row["report"])
        if violations:
            schema_bad.append({"id": row["id"], "violations": violations})
        if row["iou"] is not None:
            ious.append(row["iou"])
            if row["id"] in blind_ids:
                blind_ious.append(row["iou"])
            if row["iou"] < 0.80:
                iou_failures.append({"id": row["id"], "iou": row["iou"]})
        else:
            iou_failures.append({"id": row["id"], "iou": None,
                                 "note": row["iou_note"]})
        subs, dels, inss = levenshtein_ops(
            _normalised(row["drawn_text"]), _normalised(row["ocr_text"]))
        cer_subs += subs
        cer_dels += dels
        cer_inss += inss
        cer_n += len(_normalised(row["drawn_text"]))
        if fixture["category"] == "clean":
            clean_total += 1
            if row["verdict"] == "MISMATCH":
                clean_mismatch += 1
            if row["verdict"] != "MATCH":
                clean_non_match += 1
        else:
            cls = CLASS_OF_CATEGORY[fixture["category"]]
            for injected in _injected_chars(fixture):
                per_class[cls]["injected"] += injected["chars"]
                injected_total += injected["chars"]
                if _detected(injected, row["errors"]):
                    per_class[cls]["detected"] += injected["chars"]
                    detected_total += injected["chars"]
                else:
                    missed.append({"id": row["id"], "category": cls,
                                   "injected": injected,
                                   "live_errors": row["errors"],
                                   "ocr_text": row["ocr_text"]})
        if row["id"] in S0_IDS:
            s0_live[row["id"]] = {
                "expected_text": row["expected_text"],
                "drawn_text": row["drawn_text"],
                "ocr_text": row["ocr_text"],
                "ocr_confidence": row["ocr_confidence"],
                "ocr_bboxes": row["ocr_bboxes"],
                "iou": row["iou"],
                "verdict": row["verdict"],
                "errors": row["errors"],
                "warnings": row["warnings"],
            }

    def _recall(detected: int, total: int) -> float | None:
        return (100.0 * detected / total) if total else None

    per_class_out = {
        cls: {"injected_chars": v["injected"],
              "detected_chars": v["detected"],
              "recall_pct": _recall(v["detected"], v["injected"])}
        for cls, v in per_class.items()}
    recall = _recall(detected_total, injected_total)
    fpr = 100.0 * clean_mismatch / clean_total if clean_total else None
    cer = (cer_subs + cer_dels + cer_inss) / cer_n if cer_n else None
    metrics = {
        "fixtures": len(results),
        "recall": {"injected_chars": injected_total,
                   "detected_chars": detected_total,
                   "recall_pct": recall,
                   "per_class": per_class_out,
                   "missed": missed},
        "clean": {"total": clean_total, "mismatch": clean_mismatch,
                  "false_positive_rate_pct": fpr,
                  "non_match": clean_non_match,
                  "non_match_rate_pct": (100.0 * clean_non_match / clean_total
                                         if clean_total else None)},
        "cer": {"substitutions": cer_subs, "deletions": cer_dels,
                "insertions": cer_inss, "n_chars": cer_n,
                "cer": cer},
        "iou": {"count": len(ious),
                "min": min(ious) if ious else None,
                "mean": statistics.fmean(ious) if ious else None,
                "below_0.80": len(iou_failures),
                "failures": iou_failures,
                "blind_subset": {
                    "count": len(blind_ious),
                    "min": min(blind_ious) if blind_ious else None,
                    "mean": statistics.fmean(blind_ious) if blind_ious else None,
                    "below_0.80": sum(1 for v in blind_ious if v < 0.80)}},
        "schema": {"total": len(results),
                   "invalid": len(schema_bad),
                   "legality_pct": 100.0 * (len(results) - len(schema_bad))
                   / max(len(results), 1),
                   "invalid_reports": schema_bad},
        "timing_seconds": {
            "p50": statistics.median(times) if times else None,
            "p95": _percentile(times, 95) if times else None,
            "max": max(times) if times else None,
            "note": "1200x480 fixtures, OCR+compare per image, single "
                    "warmed adapter. The §8.3 runtime threshold is defined "
                    "for 1920x1080 pre-warmed P95 <= 5s and is NOT_MEASURED "
                    "in S0; T011 owns the performance report."},
        "s0_live": s0_live,
    }
    return metrics


def _percentile(values: list[float], pct: float) -> float:
    ordered = sorted(values)
    if not ordered:
        return 0.0
    rank = (pct / 100.0) * (len(ordered) - 1)
    lo = int(rank)
    hi = min(lo + 1, len(ordered) - 1)
    frac = rank - lo
    return ordered[lo] * (1 - frac) + ordered[hi] * frac


def _normalised(text: str) -> str:
    from textproof.core.normalize import normalize_text
    return normalize_text(text)


def gate_pass(metrics: dict) -> bool:
    """True iff every §8.3 hard threshold in scope is met.

    NOTE (R-10): the §8.3 runtime threshold (1920x1080, pre-warmed,
    P95 <= 5s) is deliberately NOT judged here.  The 300 fixtures are
    1200x480, so a P95 computed on them is not a measurement at the
    spec size — putting a <=5s check on the 1200x480 P95 would test
    the wrong thing.  That threshold is judged by the T011
    performance report (measured P95 3.817s, PASS); see S0_REPORT.md
    §5.  The timing P95 recorded in metrics["timing_seconds"] is
    report-only.
    """
    recall = metrics["recall"]["recall_pct"]
    if recall is None or recall < 95.0:
        return False
    for cls, values in metrics["recall"]["per_class"].items():
        if values["recall_pct"] is None or values["recall_pct"] < 90.0:
            return False
    if metrics["clean"]["false_positive_rate_pct"] is None \
            or metrics["clean"]["false_positive_rate_pct"] > 8.0:
        return False
    if metrics["schema"]["legality_pct"] != 100.0:
        return False
    if metrics["iou"]["below_0.80"] != 0:
        return False
    return True


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Live-OCR S0 metrics over the 300 fixtures (T006).")
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--blind", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--live-results", type=Path, required=True)
    parser.add_argument("--force", action="store_true",
                        help="Re-run live OCR even if a cache exists.")
    args = parser.parse_args(argv)

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    blind = json.loads(args.blind.read_text(encoding="utf-8"))
    blind_ids = {entry["id"] for entry in blind["fixtures"]}
    fixtures_dir = args.manifest.resolve().parent
    results = run_live(manifest, fixtures_dir, args.live_results, args.force)
    metrics = score(results, manifest, blind_ids)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(metrics, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8")
    print(f"metrics written to {args.out}")
    print(f"recall: {metrics['recall']['detected_chars']}/"
          f"{metrics['recall']['injected_chars']} = "
          f"{metrics['recall']['recall_pct']:.2f}% "
          f"(per class: " + ", ".join(
              f"{c} {v['recall_pct']:.2f}%" for c, v in
              metrics['recall']['per_class'].items()) + ")")
    print(f"clean FPR: {metrics['clean']['mismatch']}/"
          f"{metrics['clean']['total']} = "
          f"{metrics['clean']['false_positive_rate_pct']:.2f}% "
          f"(non-MATCH {metrics['clean']['non_match']})")
    print(f"CER: {metrics['cer']['cer']:.4f} "
          f"(S={metrics['cer']['substitutions']} "
          f"D={metrics['cer']['deletions']} I={metrics['cer']['insertions']} "
          f"N={metrics['cer']['n_chars']})")
    print(f"IoU: min {metrics['iou']['min']:.3f} mean "
          f"{metrics['iou']['mean']:.3f} below 0.80: "
          f"{metrics['iou']['below_0.80']}; blind min "
          f"{metrics['iou']['blind_subset']['min']:.3f}")
    print(f"schema legality: {metrics['schema']['legality_pct']:.1f}% "
          f"({metrics['schema']['invalid']} invalid)")
    print(f"timing P95: {metrics['timing_seconds']['p95']:.3f}s "
          f"max {metrics['timing_seconds']['max']:.3f}s")
    if metrics["recall"]["missed"]:
        print(f"missed injected differences: {len(metrics['recall']['missed'])}")
        for miss in metrics["recall"]["missed"]:
            print(f"  {miss['id']} {miss['injected']}")
    return 0 if gate_pass(metrics) else 1


if __name__ == "__main__":
    sys.exit(main())
