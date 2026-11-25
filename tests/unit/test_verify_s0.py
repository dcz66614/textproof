"""Unit regression tests for the S0 gate runner (T013-FIX-05, R-09/R-10/R-11).

Covers the live-path TP-S0-NUM-001 assertion added by R-11
(``scripts/verify_s0.py::check_live_num_001``) with synthetic live
results — no live OCR run is needed (the full --force-live run takes
~11 minutes and is the coordinator's job after merge).

Per-type-count reading of §8.1 (S0_REPORT.md §6(a) ruling): the live
report must contain exactly one NUMERIC_CHANGE (8 -> 0, span [4, 5])
and at most one extra error, which must be the known live-OCR
reading SUBSTITUTION ￥ (U+FFE5) -> ¥ (U+00A5), span [0, 1].
The extra SUBSTITUTION is allowed, never required.

Also locks R-10: ``gate_pass`` does NOT judge the §8.3 runtime
threshold (1920x1080 P95 <= 5s) — a metrics dict whose 1200x480
timing P95 is far above 5s still passes the gate, because that P95
is not a measurement at the spec size.
"""

from __future__ import annotations

from scripts.compute_s0_metrics import gate_pass
from scripts.verify_s0 import check_live_num_001


def _err(type_, exp_frag, rec_frag, exp_span, rec_span):
    return {"type": type_,
            "expected_fragment": exp_frag,
            "recognized_fragment": rec_frag,
            "expected_span": list(exp_span),
            "recognized_span": list(rec_span)}


def _num_001(errors, verdict="MISMATCH"):
    return {"TP-S0-NUM-001": {"verdict": verdict, "errors": errors}}


def _observed_live_errors():
    """The live-OCR behaviour as actually observed (cached live
    results, S0_REPORT.md §6(a)): one SUBSTITUTION ￥->¥ plus the
    expected NUMERIC_CHANGE 8->0."""
    return [_err("SUBSTITUTION", "￥", "¥", [0, 1], [0, 1]),
            _err("NUMERIC_CHANGE", "8", "0", [4, 5], [4, 5])]


def _numeric_only():
    return [_err("NUMERIC_CHANGE", "8", "0", [4, 5], [4, 5])]


def test_live_num_001_two_errors_pass():
    """R-11: 2 errors (SUBSTITUTION ￥->¥ + NUMERIC_CHANGE) pass."""
    ok, problems = check_live_num_001(_num_001(_observed_live_errors()))
    assert ok, problems
    assert problems == []


def test_live_num_001_single_numeric_only_pass():
    """R-11: the SUBSTITUTION is allowed, not required — a lone
    NUMERIC_CHANGE (live OCR reading ￥ correctly) also passes."""
    ok, problems = check_live_num_001(_num_001(_numeric_only()))
    assert ok, problems


def test_live_num_001_three_errors_fail():
    """R-11: 3 errors fail — a second extra error is not covered by
    the §6(a) ruling."""
    errors = _observed_live_errors() + [
        _err("SUBSTITUTION", "品", "口", [1, 2], [1, 2])]
    ok, problems = check_live_num_001(_num_001(errors))
    assert not ok
    assert problems


def test_live_num_001_two_numeric_fail():
    """R-11: two NUMERIC_CHANGE errors fail — the count must be
    exactly 1."""
    errors = [_numeric_only()[0],
              _err("NUMERIC_CHANGE", "8", "9", [4, 5], [4, 5])]
    ok, problems = check_live_num_001(_num_001(errors))
    assert not ok
    assert problems


def test_live_num_001_wrong_extra_error_fail():
    """R-11: an extra error that is not the known ￥->¥
    SUBSTITUTION fails."""
    errors = [_err("SUBSTITUTION", "品", "口", [1, 2], [1, 2]),
              _numeric_only()[0]]
    ok, problems = check_live_num_001(_num_001(errors))
    assert not ok
    assert problems


def test_live_num_001_wrong_numeric_span_fail():
    """R-11: a NUMERIC_CHANGE with the wrong span fails."""
    errors = [_err("NUMERIC_CHANGE", "8", "0", [4, 6], [4, 6])]
    ok, problems = check_live_num_001(_num_001(errors))
    assert not ok
    assert problems


def test_live_num_001_missing_entry_fail():
    """R-11: fail closed when the sample is absent from live results."""
    ok, problems = check_live_num_001({})
    assert not ok
    assert problems


def test_live_num_001_wrong_verdict_fail():
    """R-11: the live verdict must still be MISMATCH."""
    ok, problems = check_live_num_001(
        _num_001(_observed_live_errors(), verdict="MATCH"))
    assert not ok
    assert problems


def _passing_metrics(p95):
    return {
        "recall": {"recall_pct": 100.0,
                   "per_class": {"substitution": {"recall_pct": 100.0},
                                 "omission": {"recall_pct": 100.0},
                                 "numeric_change": {"recall_pct": 100.0}}},
        "clean": {"false_positive_rate_pct": 0.0},
        "schema": {"legality_pct": 100.0},
        "iou": {"below_0.80": 0},
        "timing_seconds": {"p95": p95},
    }


def test_gate_pass_does_not_judge_timing_p95():
    """R-10: gate_pass ignores the timing P95 — it is report-only.
    A 1200x480 P95 far above 5s must not fail the gate, because that
    P95 is not a measurement at the §8.3 spec size (1920x1080)."""
    assert gate_pass(_passing_metrics(p95=99.0)) is True
    assert gate_pass(_passing_metrics(p95=3.817)) is True
