"""S0 gate tests (T006; PROJECT_BOOK.md §8.1-§8.4).

Fast, deterministic checks that run inside the normal ``pytest -q``
acceptance command:

* the four fixed §8.1 samples on the fixed-record path, for BOTH the
  production compare and the Oracle, against
  ``expected_output.json`` (type, fragments, spans, verdict, bbox);
* production-Oracle parity over all 300 manifest fixed OCR line
  records (verdict + errors + warning codes + summary);
* the Oracle's independence (stdlib only, no ``textproof`` import)
  in a fresh subprocess;
* ONNX Runtime providers are exactly ``CPUExecutionProvider``;
* the four fixed-record production reports pass the §5 schema
  validator;
* TP-S0-NUM-001 live OCR is recorded VERBATIM: RapidOCR reads the
  drawn ``￥`` (U+FFE5) as ``¥`` (U+00A5), so the live report has
  one extra ``SUBSTITUTION`` next to the expected ``NUMERIC_CHANGE``
  (see S0_REPORT.md §6(a) for the ruling; this test locks the
  observed behaviour in so it cannot be silently dropped).

The full 300-image live-OCR metrics run is NOT in pytest; it lives
in ``scripts/verify_s0.py`` / ``scripts/compute_s0_metrics.py``
(live OCR over 300 images takes minutes and belongs to the gate
runner, not the unit suite).
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURES_DIR = REPO_ROOT / "tests" / "fixtures" / "s0"

import oracle.reference_compare as oracle  # noqa: E402
from scripts.parity_check import (  # noqa: E402
    S0_IDS,
    compare_reports,
    fixed_oracle_record,
    fixed_ocr_line,
)
from scripts.validate_report_schema import validate_report  # noqa: E402
from textproof.core.report import build_report  # noqa: E402
from textproof.io.image_loader import load_image  # noqa: E402


@pytest.fixture(scope="module")
def manifest() -> dict:
    return json.loads((FIXTURES_DIR / "manifest.json").read_text(
        encoding="utf-8"))


@pytest.fixture(scope="module")
def expected_output() -> dict:
    return json.loads((FIXTURES_DIR / "expected_output.json").read_text(
        encoding="utf-8"))


def _prod_fixed_report(manifest_entry: dict) -> dict:
    data = (FIXTURES_DIR / manifest_entry["filename"]).read_bytes()
    image = load_image(data)
    return build_report(image, manifest_entry["expected_text"],
                        [fixed_ocr_line(manifest_entry)])


def _oracle_fixed_report(manifest_entry: dict) -> dict:
    data = (FIXTURES_DIR / manifest_entry["filename"]).read_bytes()
    image = load_image(data)
    return oracle.compare(
        manifest_entry["expected_text"],
        [fixed_oracle_record(manifest_entry)],
        image_info={"sha256": image.sha256_hex(),
                    "format": image.format,
                    "width": image.width, "height": image.height})


@pytest.mark.parametrize("case_id", S0_IDS)
def test_fixed_s0_sample_matches_book_section_8_1(
        manifest, expected_output, case_id):
    """§8.1, fixed-record path: type, fragments, spans, verdict, bbox."""
    entry = next(f for f in manifest["fixtures"] if f["id"] == case_id)
    want = expected_output["fixtures"][case_id]
    for report in (_prod_fixed_report(entry), _oracle_fixed_report(entry)):
        assert report["verdict"] == want["verdict"]
        assert len(report["errors"]) == len(want["errors"])
        for got, wanted in zip(report["errors"], want["errors"]):
            assert got["type"] == wanted["type"]
            assert got["expected_fragment"] == wanted["expected_fragment"]
            assert got["recognized_fragment"] == wanted["recognized_fragment"]
            assert list(got["expected_span"]) == list(wanted["expected_span"])
            assert list(got["recognized_span"]) == list(
                wanted["recognized_span"])
            assert got["bbox_xyxy"] is not None
            assert [float(v) for v in got["bbox_xyxy"]] == [
                float(v) for v in entry["target_region_xyxy"]]
            assert got["bbox_scope"] == "ocr_line"


def test_production_oracle_parity_on_all_fixed_records(manifest):
    """T006 item 2: 300/300 fixed-record parity (verdict + errors +
    warning codes + summary)."""
    mismatches = []
    for entry in manifest["fixtures"]:
        diff = compare_reports(_prod_fixed_report(entry),
                               _oracle_fixed_report(entry))
        if diff:
            mismatches.append((entry["id"], diff))
    assert mismatches == []


def test_oracle_does_not_import_production_code():
    """T006 item 1, in a fresh subprocess (no shared sys.modules)."""
    code = (
        "import sys; sys.path.insert(0, r'%s'); "
        "import oracle.reference_compare; "
        "assert 'textproof' not in sys.modules, sorted(sys.modules); "
        "import ast; tree = ast.parse(open(r'%s/oracle/reference_compare.py').read()); "
        "imports = [n.names[0].name for n in ast.walk(tree) if isinstance(n, ast.Import)]; "
        "imports += [n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)]; "
        "assert all(m.split('.')[0] in {'re', 'unicodedata', 'fractions', 'typing', '__future__'} for m in imports), imports; "
        "print('oracle independent OK')" % (REPO_ROOT, REPO_ROOT)
    )
    result = subprocess.run([sys.executable, "-c", code],
                            capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stdout + result.stderr


def test_onnx_providers_cpu_only():
    """T006 item 7 (provider half): exactly CPUExecutionProvider."""
    from textproof.ocr.rapidocr_adapter import ALLOWED_PROVIDERS, RapidOCRAdapter
    adapter = RapidOCRAdapter()
    for name, providers in adapter.providers.items():
        assert providers == list(ALLOWED_PROVIDERS), (name, providers)


@pytest.mark.parametrize("case_id", S0_IDS)
def test_fixed_s0_reports_pass_section_5_schema(manifest, case_id):
    """T006 item 6 (fixed-path reports): §5 schema validation, 0 violations."""
    entry = next(f for f in manifest["fixtures"] if f["id"] == case_id)
    violations = validate_report(_prod_fixed_report(entry))
    assert violations == []


def test_num_001_live_ocr_yen_reading_recorded_verbatim(manifest):
    """TP-S0-NUM-001 live OCR reads drawn ￥ (U+FFE5) as ¥ (U+00A5).

    Locks the observed behaviour in: exactly one NUMERIC_CHANGE
    (8 -> 0, span [4, 5]) plus one extra SUBSTITUTION (￥ -> ¥,
    span [0, 1]); verdict MISMATCH.  See S0_REPORT.md §6(a)."""
    from textproof.ocr.rapidocr_adapter import RapidOCRAdapter
    entry = next(f for f in manifest["fixtures"]
                 if f["id"] == "TP-S0-NUM-001")
    data = (FIXTURES_DIR / entry["filename"]).read_bytes()
    image = load_image(data)
    lines = RapidOCRAdapter().recognize(image.pil_image)
    assert len(lines) == 1
    assert lines[0].text == "¥28.00"
    report = build_report(image, entry["expected_text"], lines)
    assert report["verdict"] == "MISMATCH"
    assert [(e["type"], e["expected_fragment"], e["recognized_fragment"],
             list(e["expected_span"])) for e in report["errors"]] == [
        ("SUBSTITUTION", "￥", "¥", [0, 1]),
        ("NUMERIC_CHANGE", "8", "0", [4, 5]),
    ]
