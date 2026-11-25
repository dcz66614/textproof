"""T008 real-browser end-to-end tests (headless Chrome via CDP).

Acceptance 1–3 and 6 (runtime half) are proven here against the real
server and the real UI in a real browser:

1. upload / edit expected text / check / re-check / download JSON /
   clear all work through real mouse clicks and a real file input;
2. preview, OCR line boxes and the error list stay linked;
3. selecting an error highlights its OCR line box; a missing whole
   line shows "无可定位 OCR 框";
4. OCR_FAILED is rendered as "待确认", never as a confirmed error
   (stub engine, last test in this module — it swaps the process-wide
   adapter and restores it afterwards);
6. clear revokes the preview object URL (fetching the old blob URL
   rejects), empties in-memory state, and the storage trap proves no
   persistent browser store was ever touched.

The browser's own network log is asserted same-origin-only and
written to the evidence directory (external-request interception
log).  Screenshots are real renders of the synthetic S0 fixtures.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import pytest

from cdp import navigate_fresh
from textproof.api.routes import reset_ocr_adapter, set_ocr_adapter
from textproof.ocr.rapidocr_adapter import OCRAdapterError

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURES = REPO_ROOT / "tests" / "fixtures" / "s0"
MANIFEST = json.loads((FIXTURES / "manifest.json").read_text(encoding="utf-8"))

FIRST_CHECK_TIMEOUT = 300.0  # first /check also loads the OCR models
CHECK_TIMEOUT = 180.0


def _record(fixture_id: str) -> dict:
    return next(f for f in MANIFEST["fixtures"] if f["id"] == fixture_id)


def _upload_and_check(page, base, fixture_id, expected_text,
                      timeout=CHECK_TIMEOUT):
    """Upload a fixture, set expected text, click check, wait for a
    verdict other than '尚未核对'.  Returns the verdict text."""
    navigate_fresh(page, base)
    page.set_file_input("#file-input", str(FIXTURES / _record(fixture_id)["filename"]))
    page.set_textarea("#expected-text", expected_text)
    page.wait_for(
        "document.querySelector('#btn-check').disabled === false",
        timeout=30, desc="check button to enable after upload",
    )
    # FileReader (base64) and the preview <img> load asynchronously;
    # give them a beat before the click so the POST has its payload.
    time.sleep(1.0)
    page.click("#btn-check")
    page.wait_for(
        "document.querySelector('#verdict').textContent.indexOf('尚未核对') === -1",
        timeout=timeout, desc="verdict to appear after check",
    )
    return page.evaluate("document.querySelector('#verdict').textContent")


def _assert_no_storage_access(page):
    """Runtime half of acceptance 6: the trap saw no storage access,
    and the store itself is empty.  The trap is read BEFORE any
    direct localStorage read (that read would trip the trap itself)."""
    accessed = page.evaluate("window.__tpStorageAccess")
    assert accessed == [], f"page touched browser storage: {accessed}"
    assert page.evaluate("localStorage.length") == 0


def _assert_same_origin_network(page, base, start_index):
    """Acceptance 5 (runtime half): every request the page issued
    went to the local server origin — nothing external was fetched."""
    page.cdp.drain_events()
    requests = page.network_requests()[start_index:]
    assert requests, "no network requests were observed at all"
    for req in requests:
        url = req["url"]
        # Same-origin http(s) requests, plus blob: URLs created from
        # that origin (the image preview object URL) and data: URLs:
        # none of these leaves the machine.
        ok = (
            url.startswith(base + "/")
            or url.startswith("blob:" + base + "/")
            or url.startswith("data:")
        )
        assert ok, f"non-same-origin request observed: {req}"
    return requests


def test_full_flow_mismatch_and_highlight(page, live_server, evidence_dir):
    """Acceptance 1+2+3: TP-S0-ZH-001 (drawn '限时优' vs expected
    '限时优惠') -> MISMATCH; clicking the error highlights its box."""
    start = len(page.cdp.events)
    verdict = _upload_and_check(page, live_server, "TP-S0-ZH-001", "限时优惠",
                                timeout=FIRST_CHECK_TIMEOUT)
    assert "检测到差异" in verdict, f"unexpected verdict: {verdict!r}"

    # OCR line boxes are overlaid on the preview.
    n_boxes = page.evaluate(
        "document.querySelectorAll('.ocr-box').length")
    assert n_boxes >= 1, "no OCR line boxes rendered on the preview"
    errors = page.evaluate(
        "document.querySelector('#error-list').textContent")
    assert "MISSING_CHARACTER" in errors, f"error list: {errors!r}"
    assert "惠" in errors

    # Click the first error item with a real mouse click.
    page.click("#error-list .error-item")
    page.wait_for(
        "document.querySelector('.ocr-box.selected') !== null",
        timeout=10, desc="OCR box to highlight on error selection",
    )
    detail = page.evaluate(
        "document.querySelector('#error-detail').textContent")
    assert "坐标（OCR 行框）" in detail, f"error detail: {detail!r}"
    assert "无可定位 OCR 框" not in detail  # this error HAS a box

    page.screenshot(evidence_dir / "ui_mismatch_highlight.png")
    _assert_no_storage_access(page)
    requests = _assert_same_origin_network(page, live_server, start)
    (evidence_dir / "network_requests.json").write_text(
        json.dumps(requests, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def test_missing_line_shows_no_locatable_box(page, live_server, evidence_dir):
    """Acceptance 3 (missing-line half): clean image + an extra
    expected line -> MISSING_LINE with bbox null -> the UI must say
    '无可定位 OCR 框' and highlight no box."""
    _upload_and_check(page, live_server, "TP-CLN-001",
                      "全场优惠10元\n第二行缺失文字")
    errors = page.evaluate(
        "document.querySelector('#error-list').textContent")
    assert "MISSING_LINE" in errors, f"error list: {errors!r}"
    page.click("#error-list .error-item")
    page.wait_for(
        "document.querySelector('#error-detail').textContent"
        ".indexOf('无可定位 OCR 框') !== -1",
        timeout=10, desc="missing-line detail to appear",
    )
    detail = page.evaluate(
        "document.querySelector('#error-detail').textContent")
    assert "无可定位 OCR 框" in detail
    assert page.evaluate(
        "document.querySelector('.ocr-box.selected')") is None
    page.screenshot(evidence_dir / "ui_missing_line.png")
    _assert_no_storage_access(page)


def test_recheck_after_editing_expected_text(page, live_server):
    """Acceptance 1 (re-check): MISMATCH first, then edit the
    expected text to the drawn text and re-check -> MATCH."""
    verdict = _upload_and_check(page, live_server, "TP-S0-ZH-001", "限时优惠")
    assert "检测到差异" in verdict
    page.set_textarea("#expected-text", "限时优")
    page.wait_for(
        "document.querySelector('#btn-recheck').disabled === false",
        timeout=10, desc="re-check button to enable",
    )
    page.click("#btn-recheck")
    # Wait for the second check to finish: the status names the check
    # count.  (Do NOT wait on "一致" — the old MISMATCH verdict
    # contains "不一致", which contains "一致" as a substring.)
    page.wait_for(
        "document.querySelector('#status').textContent.indexOf('第 2 次') !== -1",
        timeout=CHECK_TIMEOUT, desc="second check to complete",
    )
    verdict = page.evaluate(
        "document.querySelector('#verdict').textContent")
    assert "未检测到差异" in verdict, f"verdict after re-check: {verdict!r}"
    status = page.evaluate("document.querySelector('#status').textContent")
    assert "第 2 次" in status, f"status after re-check: {status!r}"
    assert page.evaluate(
        "document.querySelector('#error-list').textContent"
        ".indexOf('未检测到差异') !== -1")


def test_download_json_report(page, live_server, evidence_dir):
    """Acceptance 1 (download): the downloaded file is the full
    textproof.report/v1 JSON for the check just run."""
    download_dir = evidence_dir / "downloads"
    for old in download_dir.glob("textproof-report.json"):
        old.unlink()
    verdict = _upload_and_check(page, live_server, "TP-S0-ZH-001", "限时优惠")
    assert "检测到差异" in verdict
    page.wait_for(
        "document.querySelector('#btn-download').disabled === false",
        timeout=10, desc="download button to enable",
    )
    page.click("#btn-download")
    target = download_dir / "textproof-report.json"
    deadline = time.monotonic() + 30
    while not target.exists():
        if time.monotonic() > deadline:
            raise AssertionError("downloaded JSON did not appear in 30s")
        time.sleep(0.25)
    report = json.loads(target.read_text(encoding="utf-8"))
    assert report["schema"] == "textproof.report/v1"
    assert report["verdict"] == "MISMATCH"
    assert report["errors"], "downloaded report has no errors"
    assert report["expected_text"] == "限时优惠"
    # The on-page raw JSON is the same report.
    shown = json.loads(page.evaluate(
        "document.querySelector('#report-json').textContent"))
    assert shown == report


def test_copy_summary(page, live_server):
    """Acceptance 1 (copy): clicking copy reports a status; the
    summary wording never claims a proven image error."""
    _upload_and_check(page, live_server, "TP-S0-ZH-001", "限时优惠")
    page.click("#btn-copy")
    page.wait_for(
        "document.querySelector('#copy-status').textContent.length > 0",
        timeout=10, desc="copy status to appear",
    )
    status = page.evaluate(
        "document.querySelector('#copy-status').textContent")
    assert status in (
        "报告摘要已复制。",
        "复制失败，请手动选中原始 JSON 报告。",
    ), f"unexpected copy status: {status!r}"


def test_clear_revokes_object_url_and_resets(page, live_server):
    """Acceptance 6 (runtime half): clear revokes the preview object
    URL, drops in-memory state, empties the UI, writes no storage."""
    _upload_and_check(page, live_server, "TP-S0-ZH-001", "限时优惠")
    old_url = page.evaluate(
        "document.querySelector('#preview-img').src")
    assert old_url.startswith("blob:"), f"preview src: {old_url!r}"
    page.click("#btn-clear")
    page.wait_for(
        "document.querySelector('#verdict').textContent === '尚未核对'",
        timeout=10, desc="verdict to reset after clear",
    )
    assert page.evaluate(
        "document.querySelector('#preview-img').hidden") is True
    assert page.evaluate(
        "document.querySelector('#preview-img').getAttribute('src')") is None
    assert page.evaluate(
        "document.querySelector('#file-input').value") == ""
    assert page.evaluate(
        "document.querySelector('#expected-text').value") == ""
    assert "暂无错误清单" in page.evaluate(
        "document.querySelector('#error-list').textContent")
    assert page.evaluate(
        "document.querySelector('#report-json').textContent") == "尚未生成报告。"
    assert page.evaluate(
        "document.querySelector('#btn-check').disabled") is True
    assert page.evaluate(
        "document.querySelector('#btn-download').disabled") is True
    # The revoked blob URL must no longer resolve.
    fetched = page.evaluate(
        f"fetch({json.dumps(old_url)}).then(() => 'OK')"
        ".catch((e) => 'REJECTED:' + e.name)",
        await_promise=True,
    )
    assert str(fetched).startswith("REJECTED"), (
        f"old preview object URL still resolves after clear: {fetched!r}")
    _assert_no_storage_access(page)


def test_preview_overlay_matches_image_geometry(page, live_server, tmp_path):
    """Overlay geometry: for a narrow portrait image the box layer
    must sit exactly on the displayed image, not on the full preview
    column (the .preview-stage shrink-wrap)."""
    from PIL import Image

    portrait = tmp_path / "portrait.png"
    Image.new("RGB", (400, 800), "white").save(portrait)
    navigate_fresh(page, live_server)
    page.set_file_input("#file-input", str(portrait))
    page.wait_for(
        "document.querySelector('#preview-img').naturalWidth === 400",
        timeout=30, desc="portrait preview to load",
    )
    rects = page.evaluate(
        "(function(){"
        "var s=document.querySelector('#preview-stage').getBoundingClientRect();"
        "var i=document.querySelector('#preview-img').getBoundingClientRect();"
        "return {stage:[s.left,s.top,s.width,s.height],"
        "img:[i.left,i.top,i.width,i.height]};})()"
    )
    for a, b in zip(rects["stage"], rects["img"]):
        assert abs(a - b) <= 1.0, f"stage rect {rects['stage']} != img rect {rects['img']}"


class _FailingAdapter:
    """Stub OCR engine that always fails (exercises OCR_FAILED)."""

    def recognize(self, pil_image):
        raise OCRAdapterError("stub engine failure for T008 E2E")


def test_ocr_failed_is_labelled_pending_not_error(page, live_server):
    """Acceptance 4 (OCR_FAILED half): an engine failure is shown as
    'OCR 失败（待确认）', lists no confirmed errors, and never claims
    the image is wrong.  Runs last: it swaps the process-wide OCR
    adapter and restores it in `finally`."""
    set_ocr_adapter(_FailingAdapter())
    try:
        verdict = _upload_and_check(page, live_server, "TP-S0-ZH-001",
                                    "限时优惠")
    finally:
        reset_ocr_adapter()
    assert "OCR 失败" in verdict, f"unexpected verdict: {verdict!r}"
    assert "待确认" in verdict
    error_list = page.evaluate(
        "document.querySelector('#error-list').textContent")
    assert "E001" not in error_list
    assert "未列出确定错误" in error_list
    warnings = page.evaluate(
        "document.querySelector('#warning-list').textContent")
    assert "待确认" in warnings
