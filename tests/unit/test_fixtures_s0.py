"""Tests for the T005 fixed S0 fixtures (PROJECT_BOOK.md SS8.1/SS8.2).

These tests check the *fixture set itself* -- counts, uniqueness,
manifest/expected-output/blind-subset consistency, reproducibility,
and agreement between each fixture's recorded expected report and
the frozen T004 compare core fed with the drawn text as a fixed OCR
line record (the same style as T004's SS8.1 golden tests).

They do NOT run the OCR engine and do NOT touch the blind subset for
tuning: the blind list is only checked for size, membership and hashes.
Live-OCR behaviour (recall, IoU against real detector boxes, CER) is
T006 / S0 territory; see TASK_RESULT.md for the one known live-OCR
divergence (drawn U+FFE5 read back as U+00A5 on TP-S0-NUM-001).
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURES_DIR = REPO_ROOT / "tests" / "fixtures" / "s0"
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import generate_fixtures as gen  # noqa: E402

from textproof.core.report import compare  # noqa: E402
from textproof.ocr.rapidocr_adapter import OCRLine  # noqa: E402


@pytest.fixture(scope="module")
def manifest():
    return json.loads((FIXTURES_DIR / "manifest.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def by_id(manifest):
    return {f["id"]: f for f in manifest["fixtures"]}


def test_manifest_counts_and_uniqueness(manifest):
    assert manifest["schema"] == gen.SCHEMA_MANIFEST
    assert manifest["counts"] == {
        "total": 300, "clean": 100, "substitution": 70,
        "omission": 70, "numeric_change": 60, "blind_subset": 60,
    }
    fixtures = manifest["fixtures"]
    assert len(fixtures) == 300
    assert len({f["id"] for f in fixtures}) == 300
    assert len({f["sha256"] for f in fixtures}) == 300
    assert len({f["expected_text"] for f in fixtures}) == 300
    assert len({f["drawn_text"] for f in fixtures}) == 300
    from collections import Counter
    assert Counter(f["category"] for f in fixtures) == {
        "clean": 100, "substitution": 70, "omission": 70, "numeric_change": 60,
    }
    for f in fixtures:
        assert (f["width"], f["height"]) == (1200, 480)
        assert f["format"] == "PNG"
        region = f["target_region_xyxy"]
        assert len(region) == 4
        assert 0 <= region[0] < region[2] <= 1200
        assert 0 <= region[1] < region[3] <= 480
        assert region == gen.target_region_for(f["ink_bbox_xyxy"])
        path = FIXTURES_DIR / f["filename"]
        assert path.is_file()
        assert hashlib.sha256(path.read_bytes()).hexdigest() == f["sha256"]


def test_verify_manifest_passes():
    failures = gen.verify_manifest(FIXTURES_DIR / "manifest.json")
    assert failures == []


def test_s0_four_samples_exact(by_id):
    expectations = {
        "TP-S0-ZH-001": ("限时优惠", "限时优", "MISSING_CHARACTER", "惠", "", [3, 4], [3, 3], 1),
        "TP-S0-ZH-002": ("新品上市", "新口上市", "SUBSTITUTION", "品", "口", [1, 2], [1, 2], 1),
        "TP-S0-NUM-001": ("￥28.80", "￥28.00", "NUMERIC_CHANGE", "8", "0", [4, 5], [4, 5], 1),
        "TP-S0-ZH-003": ("新客立减20元", "新客立减元", "MISSING_CHARACTER", "20", "", [4, 6], [4, 4], 1),
    }
    for fid, (exp, drawn, etype, efrag, rfrag, espan, rspan, nerr) in expectations.items():
        f = by_id[fid]
        assert f["expected_text"] == exp
        assert f["drawn_text"] == drawn
        assert f["expected_verdict"] == "MISMATCH"
        assert len(f["expected_errors"]) >= nerr
        e0 = f["expected_errors"][0]
        assert e0["type"] == etype
        assert e0["expected_fragment"] == efrag
        assert e0["recognized_fragment"] == rfrag
        assert e0["expected_span"] == espan
        assert e0["recognized_span"] == rspan
        assert e0["bbox_scope"] == "ocr_line"


def test_expected_output_mirrors_manifest(manifest, by_id):
    expected_output = json.loads(
        (FIXTURES_DIR / "expected_output.json").read_text(encoding="utf-8"))
    assert expected_output["schema"] == gen.SCHEMA_EXPECTED
    assert set(expected_output["fixtures"]) == set(by_id)
    for fid, entry in expected_output["fixtures"].items():
        f = by_id[fid]
        assert entry["expected_text"] == f["expected_text"]
        assert entry["drawn_text"] == f["drawn_text"]
        assert entry["verdict"] == f["expected_verdict"]
        assert entry["errors"] == f["expected_errors"]
        assert entry["summary"]["error_count"] == len(f["expected_errors"])


def test_blind_subset(manifest, by_id):
    blind = json.loads((FIXTURES_DIR / "blind_subset.json").read_text(encoding="utf-8"))
    assert blind["schema"] == gen.SCHEMA_BLIND
    entries = blind["fixtures"]
    assert len(entries) == 60
    assert len({e["id"] for e in entries}) == 60
    from collections import Counter
    assert Counter(by_id[e["id"]]["category"] for e in entries) == {
        "clean": 20, "substitution": 14, "omission": 14, "numeric_change": 12,
    }
    for e in entries:
        assert by_id[e["id"]]["sha256"] == e["sha256"]


def _ocr_line_for(fixture):
    x1, y1, x2, y2 = (float(v) for v in fixture["target_region_xyxy"])
    return OCRLine(
        line_index=0,
        text=fixture["drawn_text"],
        confidence=0.98,
        bbox_xyxy=(x1, y1, x2, y2),
        quad=((x1, y1), (x2, y1), (x2, y2), (x1, y2)),
        source_order=0,
    )


def test_expected_reports_match_t004_compare(manifest):
    """Every recorded expected report equals T004 compare on the drawn text.

    This is the fixture/contract consistency check: if a mutation's
    recorded span or fragment disagreed with the frozen compare core,
    the fixture would be wrong, not the core.
    """
    mismatches = []
    for f in manifest["fixtures"]:
        result = compare(f["expected_text"], [_ocr_line_for(f)])
        got = [(e["type"], e["expected_fragment"], e["recognized_fragment"],
                e["expected_span"], e["recognized_span"]) for e in result.errors]
        want = [(e["type"], e["expected_fragment"], e["recognized_fragment"],
                 e["expected_span"], e["recognized_span"])
                for e in f["expected_errors"]]
        if result.verdict != f["expected_verdict"] or got != want:
            mismatches.append(f["id"])
    assert mismatches == []


def test_two_generations_are_byte_identical(tmp_path):
    """Completion definition (T005): two consecutive generations agree."""
    dir_a = tmp_path / "gen_a"
    dir_b = tmp_path / "gen_b"
    for d in (dir_a, dir_b):
        (d / "fonts").mkdir(parents=True)
        for name in ("NotoSansSC[wght].ttf", "OFL.txt"):
            (d / "fonts" / name).write_bytes(
                (FIXTURES_DIR / "fonts" / name).read_bytes())
    sha_a = [f["sha256"] for f in gen.generate(dir_a)["fixtures"]]
    sha_b = [f["sha256"] for f in gen.generate(dir_b)["fixtures"]]
    assert sha_a == sha_b
    assert len(sha_a) == 300
    manifest = json.loads((FIXTURES_DIR / "manifest.json").read_text(encoding="utf-8"))
    assert sha_a == [f["sha256"] for f in manifest["fixtures"]]
