"""S0 gate runner for P033 TextProof (T006).

Runs every S0 check in one place and prints a per-item PASS/FAIL
table (PROJECT_BOOK.md §8.3-§8.4; IMPLEMENTATION_PLAN.md T006 card):

1. Oracle independence — ``oracle/reference_compare.py`` imports
   only the standard library and never imports ``textproof``
   (source + AST check, re-verified here; the Oracle's own test
   suite asserts the same in a fresh subprocess).
2. Production-Oracle parity on the manifest's fixed OCR line records
   — 300/300 required (see ``scripts/parity_check.py``).
3. The four fixed S0 samples against §8.1 — type, fragments, spans,
   bbox rule and verdict, on the fixed-record path, for BOTH
   implementations (see ``scripts/parity_check.py`` + the checks
   below).
4. 300-sample detection recall >= 95% overall, >= 90% per class
   (live OCR; see ``scripts/compute_s0_metrics.py``).
5. Clean false-positive rate <= 8% (live OCR, strict MISMATCH
   reading of §8.3).
6. JSON schema legality 100% over the 300 live reports (§5; see
   ``scripts/validate_report_schema.py``) with OCR CER reported
   separately, never as a recall substitute.
7. Network 0 / CPU-only — the ONNX providers asserted here are
   exactly ``CPUExecutionProvider``; the network half is proven by
   running THIS script under ``unshare -n`` (no network namespace),
   which is how the S0 evidence run was executed (see S0_REPORT.md
   §7).  This script itself never opens a socket.
8. ``independent_verify.py`` — a separate script, not called from
   here; its result is recorded in S0_REPORT.md, not faked by this
   runner.
9. S0 report completeness — this runner writes the machine-readable
   evidence (metrics, parity, live results, schema log) that
   S0_REPORT.md cites; the report itself is the human record.

TP-S0-NUM-001 live-OCR note: on the fixed-record path the sample
yields exactly one ``NUMERIC_CHANGE`` (the §8.1 expectation).  On
the live-OCR path RapidOCR reads the drawn ``￥`` (U+FFE5) as ``¥``
(U+00A5), adding one ``SUBSTITUTION``; the ``NUMERIC_CHANGE`` itself
is present with the exact §8.1 fragment and span.  The ruling is
recorded verbatim in S0_REPORT.md §6(a): §8.1's "恰好 1 条
NUMERIC_CHANGE" constrains the count of ``NUMERIC_CHANGE`` errors,
and the fixed expectation is defined on the fixed sample; the extra
live error is OCR behaviour, recorded as-is, not deleted.  The
live-path form of this ruling is enforced by
``check_live_num_001`` on the live results below (exactly one
``NUMERIC_CHANGE`` + at most the known ￥->¥ ``SUBSTITUTION``);
the fixed-record path (item 3) still requires exactly 1 error total.

Scope of the printed verdict (R-09): the verdict this script prints
covers ONLY the items it checks itself (manifest integrity, oracle
independence, parity, the four fixed §8.1 samples, live metrics,
CPU-only providers, the live-path TP-S0-NUM-001 assertion, and
evidence output).  It does NOT cover §8.4 item 8
(``independent_verify.py``, a separate script) or the network half
of item 7, which is proven only by running this script under
``unshare -n`` (see S0_REPORT.md §7).  The full §8.4 S0 verdict is
recorded in S0_REPORT.md / S0_MAINCHAT_VERDICT.md, not by this
script's exit code alone.

Usage::

    python scripts/verify_s0.py --manifest tests/fixtures/s0/manifest.json
        [--blind tests/fixtures/s0/blind_subset.json]
        [--expected-output tests/fixtures/s0/expected_output.json]
        [--out-dir task_handoffs/T006] [--force-live]

Exit code 0 iff the script-checked items pass on their defined
scopes (manifest integrity, oracle independence, parity, the four
fixed §8.1 samples, live metrics, CPU-only providers, the live-path
TP-S0-NUM-001 assertion, and evidence output).  The printed verdict
is scoped to those items only; it is NOT the full §8.4 S0 verdict
(item 8 and the network half of item 7 are covered outside this
script — see the scope note above and R-09).
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))
sys.path.insert(0, str(REPO_ROOT))

from scripts.compute_s0_metrics import (  # noqa: E402
    gate_pass as metrics_gate_pass,
)
from scripts.compute_s0_metrics import run_live, score  # noqa: E402
from scripts.parity_check import (  # noqa: E402
    S0_IDS,
    fixed_oracle_record,
    fixed_ocr_line,
    run_edge_battery,
    run_fixed_parity,
)
from scripts.validate_report_schema import validate_report  # noqa: E402

import oracle.reference_compare as oracle  # noqa: E402
from textproof.core.report import build_report  # noqa: E402
from textproof.io.image_loader import load_image  # noqa: E402
from textproof.ocr.rapidocr_adapter import (  # noqa: E402
    ALLOWED_PROVIDERS,
    RapidOCRAdapter,
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def check_oracle_independence() -> tuple[bool, list[str]]:
    """Item 1: the Oracle imports stdlib only, never ``textproof``.

    The check is AST-based: only real ``import`` / ``from ... import``
    statements count.  The literal string ``"textproof.report/v1"``
    (the frozen schema id, §5.1) and prose mentions of the word in
    docstrings/comments are NOT imports and must not fail this check
    (a naive substring test would false-positive on the schema id).
    The Oracle's own test suite asserts the same in a fresh
    subprocess (``tests/oracle/test_reference_compare.py``)."""
    path = REPO_ROOT / "oracle" / "reference_compare.py"
    source = path.read_text(encoding="utf-8")
    problems: list[str] = []
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.split(".")[0] not in {
                        "re", "unicodedata", "fractions", "typing",
                        "__future__"}:
                    problems.append(f"oracle imports non-stdlib: {alias.name}")
        elif isinstance(node, ast.ImportFrom):
            if node.module and node.module.split(".")[0] not in {
                    "re", "unicodedata", "fractions", "typing",
                    "__future__"}:
                problems.append(f"oracle imports from: {node.module}")
    return (not problems, problems)


def check_fixed_s0_samples(manifest: dict, expected_output: dict,
                           fixtures_dir: Path) -> tuple[bool, list[dict]]:
    """Item 3: the four §8.1 samples on the fixed-record path, for
    BOTH implementations, against expected_output.json."""
    by_id = {f["id"]: f for f in manifest["fixtures"]}
    checks: list[dict] = []
    all_ok = True
    for fid in S0_IDS:
        fixture = by_id[fid]
        expected = expected_output["fixtures"][fid]
        data = (fixtures_dir / fixture["filename"]).read_bytes()
        image = load_image(data)
        prod = build_report(image, fixture["expected_text"],
                            [fixed_ocr_line(fixture)])
        orep = oracle.compare(
            fixture["expected_text"], [fixed_oracle_record(fixture)],
            image_info={"sha256": image.sha256_hex(),
                        "format": image.format,
                        "width": image.width, "height": image.height})
        entry: dict = {"id": fid, "checks": {}, "ok": True}
        for impl_name, report in (("production", prod), ("oracle", orep)):
            problems: list[str] = []
            if report["verdict"] != expected["verdict"]:
                problems.append(
                    f"verdict {report['verdict']} != {expected['verdict']}")
            exp_errors = expected["errors"]
            got_errors = report["errors"]
            if len(got_errors) != len(exp_errors):
                problems.append(
                    f"error count {len(got_errors)} != {len(exp_errors)}")
            else:
                for got, want in zip(got_errors, exp_errors):
                    if got["type"] != want["type"]:
                        problems.append(
                            f"type {got['type']} != {want['type']}")
                    if got["expected_fragment"] != want["expected_fragment"]:
                        problems.append(
                            "expected_fragment "
                            f"{got['expected_fragment']!r} != "
                            f"{want['expected_fragment']!r}")
                    if got["recognized_fragment"] != want["recognized_fragment"]:
                        problems.append(
                            "recognized_fragment "
                            f"{got['recognized_fragment']!r} != "
                            f"{want['recognized_fragment']!r}")
                    if list(got["expected_span"]) != list(want["expected_span"]):
                        problems.append(
                            f"expected_span {got['expected_span']} != "
                            f"{want['expected_span']}")
                    if list(got["recognized_span"]) != list(
                            want["recognized_span"]):
                        problems.append(
                            f"recognized_span {got['recognized_span']} != "
                            f"{want['recognized_span']}")
                    if got["bbox_xyxy"] is None:
                        problems.append("error bbox is null (§8.1: bbox "
                                        "must point at the OCR line)")
                    elif list(got["bbox_xyxy"]) != [
                            float(v) for v in fixture["target_region_xyxy"]]:
                        problems.append(
                            "fixed-path error bbox != target_region_xyxy")
                    if got.get("bbox_scope") != "ocr_line":
                        problems.append(
                            f"bbox_scope {got.get('bbox_scope')!r} != "
                            "'ocr_line'")
            entry["checks"][impl_name] = {
                "ok": not problems, "problems": problems,
                "verdict": report["verdict"],
                "error_count": len(got_errors)}
            if problems:
                entry["ok"] = False
        checks.append(entry)
        all_ok = all_ok and entry["ok"]
    return all_ok, checks


def check_live_num_001(s0_live: dict) -> tuple[bool, list[str]]:
    """Live-path TP-S0-NUM-001 assertion (R-11; S0_REPORT.md §6(a)).

    Per-type-count reading of §8.1: the live report for this sample
    must contain exactly one NUMERIC_CHANGE (8 -> 0, span [4, 5])
    and at most one extra error, which must be the known live-OCR
    reading SUBSTITUTION ￥ (U+FFE5) -> ¥ (U+00A5), span [0, 1].
    The extra SUBSTITUTION is allowed, never required: if live OCR
    ever reads ￥ correctly, the single NUMERIC_CHANGE alone passes.

    This checks the LIVE results (``metrics["s0_live"]``, built from
    live OCR) only.  The fixed-record path (item 3,
    ``check_fixed_s0_samples``) still requires exactly 1 error total
    and is unchanged.  No ￥->¥ mapping is added anywhere (§4.3 /
    ``normalize.py`` untouched); the extra error is OCR behaviour
    recorded as-is.
    """
    problems: list[str] = []
    entry = s0_live.get("TP-S0-NUM-001")
    if entry is None:
        return False, ["TP-S0-NUM-001 missing from live results"]
    errors = entry.get("errors") or []
    numeric = [e for e in errors if e.get("type") == "NUMERIC_CHANGE"]
    if len(numeric) != 1:
        problems.append(f"live NUMERIC_CHANGE count {len(numeric)} != 1")
    else:
        num = numeric[0]
        if num.get("expected_fragment") != "8" \
                or num.get("recognized_fragment") != "0":
            problems.append(
                "live NUMERIC_CHANGE fragment "
                f"{num.get('expected_fragment')!r}->"
                f"{num.get('recognized_fragment')!r} != '8'->'0'")
        if list(num.get("expected_span") or []) != [4, 5] \
                or list(num.get("recognized_span") or []) != [4, 5]:
            problems.append(
                "live NUMERIC_CHANGE spans "
                f"{num.get('expected_span')}/"
                f"{num.get('recognized_span')} != [4, 5]/[4, 5]")
    extras = [e for e in errors if e.get("type") != "NUMERIC_CHANGE"]
    if len(extras) > 1:
        problems.append(
            f"live extra error count {len(extras)} > 1: "
            f"{[e.get('type') for e in extras]}")
    for extra in extras:
        if not (
                extra.get("type") == "SUBSTITUTION"
                and extra.get("expected_fragment") == "￥"
                and extra.get("recognized_fragment") == "¥"
                and list(extra.get("expected_span") or []) == [0, 1]
                and list(extra.get("recognized_span") or []) == [0, 1]):
            problems.append(
                "unexpected live extra error: "
                f"{extra.get('type')} "
                f"{extra.get('expected_fragment')!r}->"
                f"{extra.get('recognized_fragment')!r} "
                f"span {extra.get('expected_span')}")
    if entry.get("verdict") != "MISMATCH":
        problems.append(
            f"live verdict {entry.get('verdict')!r} != 'MISMATCH'")
    return (not problems, problems)


def check_manifest_integrity(manifest: dict, fixtures_dir: Path,
                             manifest_path: Path) -> tuple[bool, list[str]]:
    """Recompute every fixture PNG SHA-256 and compare with the manifest."""
    problems: list[str] = []
    for fixture in manifest["fixtures"]:
        path = fixtures_dir / fixture["filename"]
        if not path.is_file():
            problems.append(f"{fixture['id']}: file missing")
            continue
        actual = sha256_file(path)
        if actual != fixture["sha256"]:
            problems.append(f"{fixture['id']}: sha256 {actual} != "
                            f"manifest {fixture['sha256']}")
        if path.stat().st_size != fixture["bytes"]:
            problems.append(f"{fixture['id']}: bytes mismatch")
    return (not problems, problems)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="S0 gate runner (T006).")
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--blind", type=Path, default=None)
    parser.add_argument("--expected-output", type=Path, default=None)
    parser.add_argument("--out-dir", type=Path, default=None)
    parser.add_argument("--force-live", action="store_true",
                        help="Re-run live OCR even if cached results exist.")
    args = parser.parse_args(argv)

    manifest_path = args.manifest
    fixtures_dir = manifest_path.resolve().parent
    blind_path = args.blind or fixtures_dir / "blind_subset.json"
    expected_path = (args.expected_output
                     or fixtures_dir / "expected_output.json")
    out_dir = args.out_dir or (REPO_ROOT / "task_handoffs" / "T006")
    out_dir.mkdir(parents=True, exist_ok=True)

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    expected_output = json.loads(expected_path.read_text(encoding="utf-8"))
    blind = json.loads(blind_path.read_text(encoding="utf-8"))
    blind_ids = {entry["id"] for entry in blind["fixtures"]}

    results: dict[str, dict] = {}

    # Item 1 — Oracle independence.
    ok, problems = check_oracle_independence()
    results["1_oracle_independence"] = {"pass": ok, "problems": problems}
    print(f"[1] oracle independence: {'PASS' if ok else 'FAIL'} {problems}")

    # Manifest integrity (precondition for every other item).
    ok, problems = check_manifest_integrity(manifest, fixtures_dir,
                                            manifest_path)
    results["0_manifest_integrity"] = {"pass": ok, "problems": problems}
    print(f"[0] manifest integrity (300 PNG SHA-256): "
          f"{'PASS' if ok else 'FAIL'} {problems[:5]}")

    # Item 3 — four fixed S0 samples (§8.1), fixed-record path.
    ok, checks = check_fixed_s0_samples(manifest, expected_output,
                                        fixtures_dir)
    results["3_fixed_s0_samples"] = {"pass": ok, "checks": checks}
    for entry in checks:
        print(f"[3] {entry['id']}: {'PASS' if entry['ok'] else 'FAIL'} "
              f"{entry['checks']}")

    # Item 2 — parity on the manifest's fixed OCR line records.
    fixed = run_fixed_parity(manifest, fixtures_dir)
    edge = run_edge_battery()
    results["2_parity"] = {"pass": fixed["mismatched"] == 0,
                           "fixed": fixed, "edge_battery": edge}
    print(f"[2] parity fixed fixtures: {fixed['matched']}/{fixed['total']} "
          f"({'PASS' if fixed['mismatched'] == 0 else 'FAIL'})")
    print(f"[2] edge battery (diagnostic): {edge['matching']}/"
          f"{edge['total']} match; differing: "
          f"{[d['case'] for d in edge['differences']]}")

    # Items 4-6 + IoU + CER — live OCR over all 300 fixtures.
    live_results_path = out_dir / "live_ocr_results.jsonl"
    live = run_live(manifest, fixtures_dir, live_results_path,
                    force=args.force_live)
    metrics = score(live, manifest, blind_ids)
    metrics_ok = metrics_gate_pass(metrics)
    results["4_5_6_metrics"] = {"pass": metrics_ok, "metrics": metrics}
    print(f"[4] recall: {metrics['recall']['recall_pct']:.2f}% "
          f"(per class: " + ", ".join(
              f"{c} {v['recall_pct']:.2f}%" for c, v in
              metrics['recall']['per_class'].items()) + ") "
          f"threshold >=95% / >=90% each: "
          f"{'PASS' if metrics['recall']['recall_pct'] >= 95.0 and all(v['recall_pct'] >= 90.0 for v in metrics['recall']['per_class'].values()) else 'FAIL'}")
    print(f"[5] clean FPR: {metrics['clean']['false_positive_rate_pct']:.2f}% "
          f"({metrics['clean']['mismatch']}/{metrics['clean']['total']}) "
          f"threshold <=8%: "
          f"{'PASS' if metrics['clean']['false_positive_rate_pct'] <= 8.0 else 'FAIL'}")
    print(f"[6] schema legality: {metrics['schema']['legality_pct']:.1f}% "
          f"({'PASS' if metrics['schema']['legality_pct'] == 100.0 else 'FAIL'}); "
          f"CER: {metrics['cer']['cer']:.4f} (reported separately, §8.3)")
    print(f"[I] IoU: min {metrics['iou']['min']:.3f} mean "
          f"{metrics['iou']['mean']:.3f} below 0.80: "
          f"{metrics['iou']['below_0.80']} "
          f"({'PASS' if metrics['iou']['below_0.80'] == 0 else 'FAIL'}); "
          f"blind min {metrics['iou']['blind_subset']['min']:.3f}")

    # Live-path TP-S0-NUM-001 assertion (R-11): exactly one
    # NUMERIC_CHANGE + at most the known ￥->¥ SUBSTITUTION, on the
    # live results only.  The fixed-record path (item 3) is unchanged.
    ok, problems = check_live_num_001(metrics["s0_live"])
    results["3_live_num_001"] = {"pass": ok, "problems": problems}
    print(f"[3L] live TP-S0-NUM-001: {'PASS' if ok else 'FAIL'} {problems}")

    # Item 7 — CPU-only providers (network half: this run is executed
    # under `unshare -n`; see S0_REPORT.md §7 for the evidence).
    adapter = RapidOCRAdapter()
    providers = adapter.providers
    cpu_ok = all(p == list(ALLOWED_PROVIDERS) for p in providers.values())
    results["7_cpu_only"] = {"pass": cpu_ok, "providers": providers,
                             "network": "proven by unshare -n execution; "
                             "see S0_REPORT.md §7"}
    print(f"[7] ONNX providers: {json.dumps(providers)} "
          f"({'PASS' if cpu_ok else 'FAIL'})")

    # Item 9 — machine-readable evidence written.
    (out_dir / "s0_metrics.json").write_text(
        json.dumps(metrics, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8")
    (out_dir / "parity_report.json").write_text(
        json.dumps({"fixed_fixtures": fixed, "edge_battery": edge},
                   indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8")
    schema_log = out_dir / "schema_validation.log"
    bad = metrics["schema"]["invalid_reports"]
    schema_log.write_text(
        f"schema validation over {metrics['schema']['total']} live reports: "
        f"{metrics['schema']['total'] - len(bad)} valid, {len(bad)} invalid\n"
        + "".join(f"{entry['id']}: {entry['violations']}\n"
                  for entry in bad),
        encoding="utf-8")
    results["9_evidence"] = {
        "pass": True,
        "files": ["s0_metrics.json", "parity_report.json",
                  "live_ocr_results.jsonl", "schema_validation.log"]}
    print("[9] evidence written to "
          f"{out_dir} (s0_metrics.json, parity_report.json, "
          "live_ocr_results.jsonl, schema_validation.log)")

    all_pass = all([
        results["0_manifest_integrity"]["pass"],
        results["1_oracle_independence"]["pass"],
        results["2_parity"]["pass"],
        results["3_fixed_s0_samples"]["pass"],
        results["3_live_num_001"]["pass"],
        results["4_5_6_metrics"]["pass"],
        results["7_cpu_only"]["pass"],
        results["9_evidence"]["pass"],
    ])
    print("VERIFY_S0 ITEMS: "
          f"{'PASS' if all_pass else 'FAIL'} (script-checked items only)")
    print(f"S0 VERDICT: {'PASS' if all_pass else 'FAIL'} "
          "(script-checked items only; NOT the full §8.4 verdict — "
          "see NOTE)")
    print("NOTE: this verdict covers only the items checked by this "
          "script (manifest integrity, oracle independence, parity, "
          "the four fixed §8.1 samples, live metrics, CPU-only "
          "providers, the live-path TP-S0-NUM-001 assertion, and "
          "evidence output). It does NOT cover §8.4 item 8 "
          "(independent_verify.py — a separate script, run separately "
          "and recorded in S0_REPORT.md) or the network half of item "
          "7, which is proven only by running this script under "
          "`unshare -n` (see S0_REPORT.md §7). The full §8.4 S0 "
          "verdict is recorded in S0_REPORT.md / "
          "S0_MAINCHAT_VERDICT.md.")
    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
