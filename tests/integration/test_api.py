"""Integration tests for the T007 local API (FastAPI, loopback-only).

HTTP-layer note (honest deviation, see API_CONTRACT.md §6): the T007
card says "用 FastAPI TestClient 做 HTTP 层测试", but
``starlette.testclient.TestClient`` requires ``httpx``, which is NOT
in the frozen ``requirements.lock`` and is NOT installed in the T001
venv (``from starlette.testclient import TestClient`` fails with an
"install httpx" error).  Adding httpx would be a new dependency, which
T007 is forbidden to do without the coordinator ("如需新依赖先停下报
协调员").  These tests therefore exercise the real HTTP stack
instead: a real uvicorn server bound to 127.0.0.1 in a background
thread, driven over a real loopback socket with stdlib ``urllib``.
That is strictly stronger evidence for the HTTP surface than
TestClient (real socket, real server, real bind address), and the
loopback-only proof in this file depends on it.

Coverage maps to the six T007 acceptance criteria:

1. health / version — ``test_health`` / ``test_version``.
2. POST /api/v1/check returns textproof.report/v1 — ``test_check_success``.
3. bind fixed to 127.0.0.1 — ``test_bind_host_*``,
   ``test_server_listens_only_on_loopback``, ``test_serve_rejects_*``.
4. in-memory only, no cross-request cache — ``test_stateless_*``,
   ``test_check_does_not_write_files``.
5. error codes for oversize / bad MIME / bad base64 / empty text /
   OCR failure — ``test_check_error_cases`` (parametrised) plus
   ``test_ocr_failure_*``.
6. API == core for the same fixture — ``test_api_matches_core``.

All test images are the frozen S0 synthetic fixtures or synthetic
bytes built in-memory; no real user images, no network.
"""

from __future__ import annotations

import asyncio
import base64
import io
import json
import socket
import struct
import threading
import urllib.error
import urllib.request
import zlib
from pathlib import Path

import pytest
import uvicorn
from PIL import Image

from textproof.api.app import create_app, serve, validate_bind_host
from textproof.api.routes import (
    _MAX_BASE64_CHARS,
    ApiError,
    get_ocr_adapter,
    reset_ocr_adapter,
    run_check,
    set_ocr_adapter,
)
from textproof.core.report import build_report
from textproof.io.image_loader import load_image, validate_expected_text

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURES = REPO_ROOT / "tests" / "fixtures" / "s0"
# The too-many-pixels case intentionally feeds Pillow a 48 MP header;
# its DecompressionBombWarning is expected, not a test failure.
pytestmark = pytest.mark.filterwarnings(
    "ignore:Image size .* exceeds limit.*:Warning"
)
MANIFEST = json.loads((FIXTURES / "manifest.json").read_text(encoding="utf-8"))
EXPECTED_OUTPUT = json.loads(
    (FIXTURES / "expected_output.json").read_text(encoding="utf-8")
)

ZH001 = next(f for f in MANIFEST["fixtures"] if f["id"] == "TP-S0-ZH-001")
ZH002 = next(f for f in MANIFEST["fixtures"] if f["id"] == "TP-S0-ZH-002")


def _fixture_bytes(fixture_id: str) -> bytes:
    record = next(f for f in MANIFEST["fixtures"] if f["id"] == fixture_id)
    return (FIXTURES / record["filename"]).read_bytes()


def _b64(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


def _fake_png(width: int, height: int) -> bytes:
    """A PNG with a valid IHDR but no image data (header-only).

    Pillow's ``Image.open`` reads only the IHDR, so the loader's
    header dimension check fires before any decode is attempted.
    """
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)

    def chunk(tag: bytes, payload: bytes) -> bytes:
        body = tag + payload
        return (
            struct.pack(">I", len(payload))
            + body
            + struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF)
        )

    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) + chunk(b"IEND", b"")


def _animated_webp_bytes() -> bytes:
    buf = io.BytesIO()
    first = Image.new("RGB", (100, 50), "white")
    second = Image.new("RGB", (100, 50), "black")
    first.save(
        buf, format="WEBP", save_all=True, append_images=[second],
        duration=100, loop=0,
    )
    return buf.getvalue()


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


# --- live loopback server (real uvicorn, real socket) --------------------

@pytest.fixture(scope="module")
def live_server():
    """Start the real API server on 127.0.0.1; yield (base_url, port)."""
    port = _free_port()
    server = uvicorn.Server(
        uvicorn.Config(
            create_app(), host="127.0.0.1", port=port, log_level="error"
        )
    )
    thread = threading.Thread(
        target=asyncio.run, args=(server.serve(),), daemon=True
    )
    thread.start()
    base = f"http://127.0.0.1:{port}"
    deadline = __import__("time").monotonic() + 60
    while True:
        try:
            status, _ = _http("GET", f"{base}/api/v1/health")
            if status == 200:
                break
        except Exception:
            pass
        if __import__("time").monotonic() > deadline:
            raise RuntimeError("live API server did not come up in 60s")
        __import__("time").sleep(0.2)
    yield base, port
    server.should_exit = True
    thread.join(timeout=15)


def _http(method: str, url: str, body: object = None, raw: bytes | None = None,
          headers: dict | None = None) -> tuple[int, bytes]:
    """One stdlib HTTP request; returns (status, raw body bytes).

    HTTP error statuses are returned, not raised, so tests can assert
    on 400/422/500 bodies.
    """
    data = raw
    hdrs = dict(headers or {})
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        hdrs.setdefault("Content-Type", "application/json")
    req = urllib.request.Request(url, data=data, headers=hdrs, method=method)
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            return resp.status, resp.read()
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read()


def _check_payload(fixture_id: str, expected_text: str | None = None,
                   mime: str = "image/png") -> dict:
    record = next(f for f in MANIFEST["fixtures"] if f["id"] == fixture_id)
    return {
        "image_mime": mime,
        "image_base64": _b64(_fixture_bytes(fixture_id)),
        "expected_text": expected_text if expected_text is not None
        else record["expected_text"],
    }


def _iou(box_a, box_b) -> float:
    x1 = max(box_a[0], box_b[0])
    y1 = max(box_a[1], box_b[1])
    x2 = min(box_a[2], box_b[2])
    y2 = min(box_a[3], box_b[3])
    inter = max(0.0, x2 - x1) * max(0.0, y2 - y1)
    area_a = max(0.0, box_a[2] - box_a[0]) * max(0.0, box_a[3] - box_a[1])
    area_b = max(0.0, box_b[2] - box_b[0]) * max(0.0, box_b[3] - box_b[1])
    union = area_a + area_b - inter
    return inter / union if union > 0 else 0.0


# --- acceptance 1: health + version ---------------------------------------

def test_health(live_server):
    base, _ = live_server
    status, raw = _http("GET", f"{base}/api/v1/health")
    assert status == 200
    body = json.loads(raw)
    assert body["status"] == "ok"
    assert body["service"] == "textproof"
    assert body["schema"] == "textproof.report/v1"
    assert body["tool_version"] == "0.1.0"


def test_version(live_server):
    base, _ = live_server
    status, raw = _http("GET", f"{base}/api/v1/version")
    assert status == 200
    body = json.loads(raw)
    assert body["service"] == "textproof"
    assert body["tool_version"] == "0.1.0"
    assert body["schema"] == "textproof.report/v1"
    assert body["spec_version"] == "1.0.0"
    assert body["rapidocr_version"] == "3.10.0"
    assert body["onnxruntime_version"] == "1.32.0"
    assert body["providers"] == ["CPUExecutionProvider"]


def test_version_alias(live_server):
    base, _ = live_server
    status, raw = _http("GET", f"{base}/version")
    assert status == 200
    assert json.loads(raw)["schema"] == "textproof.report/v1"


def test_unknown_route_returns_error_envelope(live_server):
    base, _ = live_server
    status, raw = _http("GET", f"{base}/api/v1/nope")
    assert status == 404
    assert json.loads(raw)["error"]["code"] == "NOT_FOUND"


# --- acceptance 2: POST /check returns textproof.report/v1 ---------------

def test_check_success(live_server):
    """TP-S0-ZH-001 via the API: the frozen §8.1 fixed case, live OCR."""
    base, _ = live_server
    status, raw = _http(
        "POST", f"{base}/api/v1/check", body=_check_payload("TP-S0-ZH-001")
    )
    assert status == 200, raw[:500]
    report = json.loads(raw)
    assert report["schema"] == "textproof.report/v1"
    assert report["tool_version"] == "0.1.0"
    assert report["verdict"] == "MISMATCH"
    assert report["image"]["sha256"] == ZH001["sha256"]
    assert report["image"]["format"] == "PNG"
    assert report["image"]["width"] == 1200
    assert report["image"]["height"] == 480
    assert report["expected_text"] == "限时优惠"
    assert report["recognized_text"] == "限时优"
    assert len(report["errors"]) == 1
    err = report["errors"][0]
    assert err["type"] == "MISSING_CHARACTER"
    assert err["expected_fragment"] == "惠"
    assert err["recognized_fragment"] == ""
    assert err["expected_span"] == [3, 4]
    assert err["recognized_span"] == [3, 3]
    assert err["bbox_scope"] == "ocr_line"
    assert err["bbox_xyxy"] == report["ocr_lines"][0]["bbox_xyxy"]
    assert _iou(err["bbox_xyxy"], ZH001["target_region_xyxy"]) >= 0.80
    assert report["summary"] == {
        "expected_lines": 1, "ocr_lines": 1,
        "error_count": 1, "warning_count": 0,
    }
    # The response carries no image bytes.
    assert "image_base64" not in raw.decode("utf-8")


# --- acceptance 6: API == core for the same fixture -----------------------

def test_api_matches_core(live_server):
    """API report and direct core build_report are dict-identical."""
    base, _ = live_server
    payload = _check_payload("TP-S0-ZH-001")
    status, raw = _http("POST", f"{base}/api/v1/check", body=payload)
    assert status == 200, raw[:500]
    api_report = json.loads(raw)

    png = _fixture_bytes("TP-S0-ZH-001")
    image = load_image(png)
    expected = validate_expected_text(ZH001["expected_text"])
    adapter = get_ocr_adapter()
    direct = build_report(image, expected, adapter.recognize(image.pil_image))
    assert api_report == direct


# --- acceptance 3: loopback-only binding ----------------------------------

@pytest.mark.parametrize(
    "host",
    ["0.0.0.0", "198.19.0.2", "8.8.8.8", "localhost", "::1", "", "  ",
     "example.com", "127.0.0.2", "0"],
)
def test_bind_host_rejects_non_loopback(host):
    with pytest.raises(ValueError):
        validate_bind_host(host)


def test_bind_host_accepts_only_127_0_0_1():
    assert validate_bind_host("127.0.0.1") == "127.0.0.1"


@pytest.mark.parametrize("host", ["0.0.0.0", "198.19.0.2", "localhost"])
def test_serve_rejects_non_loopback_host(host):
    """serve() must raise before uvicorn ever binds."""
    with pytest.raises(ValueError):
        serve(host=host, port=18799)


def test_server_listens_only_on_loopback(live_server):
    """The live server's LISTEN socket is 127.0.0.1 only (/proc/net/tcp).

    A plain ``connect_ex`` to the machine's non-loopback IP is NOT a
    valid probe on this VM: outbound TCP is intercepted by the egress
    proxy (a connect to 198.19.0.2:port returns 0 via 198.19.0.1:3128
    even for a port nothing listens on).  Reading the kernel's own
    listening-socket table is proxy-independent: the server's port
    must appear in LISTEN state (0A) bound to 127.0.0.1 (0100007F)
    and to no other local address.
    """
    base, port = live_server
    # Loopback connects.
    with socket.create_connection(("127.0.0.1", port), timeout=5):
        pass
    port_hex = f"{port:04X}"
    listeners = []
    for line in Path("/proc/net/tcp").read_text().splitlines()[1:]:
        parts = line.split()
        local_addr, state = parts[1], parts[3]
        ip_hex, port_part = local_addr.split(":")
        if port_part.upper() == port_hex and state == "0A":
            listeners.append(ip_hex)
    assert listeners, f"no LISTEN socket found for port {port}"
    assert listeners == ["0100007F"], (
        f"server listens on {listeners}, expected only 127.0.0.1 (0100007F)"
    )


def test_no_cors_header(live_server):
    """No Access-Control-Allow-Origin is ever emitted (no CORS)."""
    base, _ = live_server
    req = urllib.request.Request(
        f"{base}/api/v1/health",
        headers={"Origin": "https://example.com"},
        method="GET",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        assert resp.headers.get("Access-Control-Allow-Origin") is None


# --- acceptance 4: in-memory only, no cross-request state -----------------

def test_stateless_no_cross_request_leak(live_server):
    """Two different fixtures in sequence: no data leaks between them."""
    base, _ = live_server
    status1, raw1 = _http(
        "POST", f"{base}/api/v1/check", body=_check_payload("TP-S0-ZH-001")
    )
    status2, raw2 = _http(
        "POST", f"{base}/api/v1/check", body=_check_payload("TP-S0-ZH-002")
    )
    assert status1 == 200 and status2 == 200
    first, second = json.loads(raw1), json.loads(raw2)
    assert first["image"]["sha256"] == ZH001["sha256"]
    assert second["image"]["sha256"] == ZH002["sha256"]
    assert second["expected_text"] == "新品上市"
    assert second["recognized_text"] == "新口上市"
    assert "限时优惠" not in raw2.decode("utf-8")
    assert "限时优" not in raw2.decode("utf-8")


def test_check_does_not_write_files(live_server, tmp_path):
    """A check leaves no new files under src/ or tests/ (memory only)."""
    base, _ = live_server
    watched = [REPO_ROOT / "src", REPO_ROOT / "tests"]

    def _snapshot():
        return {
            p for root in watched for p in Path(root).rglob("*") if p.is_file()
        }

    before = _snapshot()
    status, _ = _http(
        "POST", f"{base}/api/v1/check", body=_check_payload("TP-S0-ZH-001")
    )
    assert status == 200
    assert _snapshot() == before


# --- acceptance 5: error codes --------------------------------------------

PNG_B64 = _b64(_fixture_bytes("TP-S0-ZH-001"))

ERROR_CASES = [
    # (label, payload, expected HTTP status, expected error code)
    ("unsupported_mime", {"image_mime": "image/gif", "image_base64": PNG_B64,
                          "expected_text": "限时优惠"},
     400, "INVALID_IMAGE_MIME"),
    ("mime_mismatch", {"image_mime": "image/jpeg", "image_base64": PNG_B64,
                       "expected_text": "限时优惠"},
     400, "INVALID_IMAGE_MIME"),
    ("invalid_base64", {"image_mime": "image/png",
                        "image_base64": "!!!not-base64!!!",
                        "expected_text": "限时优惠"},
     400, "INVALID_BASE64"),
    ("empty_base64", {"image_mime": "image/png", "image_base64": "",
                      "expected_text": "限时优惠"},
     400, "INVALID_BASE64"),
    ("non_image_bytes", {"image_mime": "image/png",
                         "image_base64": _b64(b"hello world, not an image"),
                         "expected_text": "限时优惠"},
     400, "INVALID_IMAGE_FORMAT"),
    ("corrupt_png", {"image_mime": "image/png",
                     "image_base64": _b64(b"\x89PNG\r\n\x1a\n" + b"\x00" * 64),
                     "expected_text": "限时优惠"},
     400, "INVALID_IMAGE"),
    ("animated_webp", {"image_mime": "image/webp",
                       "image_base64": _b64(_animated_webp_bytes()),
                       "expected_text": "限时优惠"},
     400, "ANIMATED_IMAGE_NOT_SUPPORTED"),
    ("dimension_exceeded", {"image_mime": "image/png",
                            "image_base64": _b64(_fake_png(9000, 10)),
                            "expected_text": "限时优惠"},
     400, "IMAGE_DIMENSION_EXCEEDED"),
    ("too_many_pixels", {"image_mime": "image/png",
                         "image_base64": _b64(_fake_png(8000, 6000)),
                         "expected_text": "限时优惠"},
     400, "IMAGE_TOO_MANY_PIXELS"),
    ("image_too_large", {"image_mime": "image/png",
                         "image_base64": "A" * (_MAX_BASE64_CHARS + 4),
                         "expected_text": "限时优惠"},
     400, "IMAGE_TOO_LARGE"),
    ("expected_text_empty", {"image_mime": "image/png",
                             "image_base64": PNG_B64, "expected_text": ""},
     400, "EXPECTED_TEXT_EMPTY"),
    ("expected_text_blank", {"image_mime": "image/png",
                             "image_base64": PNG_B64, "expected_text": "   "},
     400, "EXPECTED_TEXT_EMPTY"),
    ("expected_text_too_long", {"image_mime": "image/png",
                                "image_base64": PNG_B64,
                                "expected_text": "x" * 5001},
     400, "EXPECTED_TEXT_TOO_LONG"),
    ("expected_text_too_many_lines", {"image_mime": "image/png",
                                      "image_base64": PNG_B64,
                                      "expected_text": "\n".join(["a"] * 101)},
     400, "EXPECTED_TEXT_TOO_MANY_LINES"),
]


@pytest.mark.parametrize(
    "label,payload,status,code", ERROR_CASES,
    ids=[c[0] for c in ERROR_CASES],
)
def test_check_error_cases(live_server, label, payload, status, code):
    base, _ = live_server
    got_status, raw = _http("POST", f"{base}/api/v1/check", body=payload)
    assert got_status == status, f"{label}: {raw[:300]}"
    body = json.loads(raw)
    assert body["error"]["code"] == code, f"{label}: {body}"
    assert "schema" not in body  # an error is not a report


@pytest.mark.parametrize(
    "label,payload,status,code",
    [
        ("missing_expected_text",
         {"image_mime": "image/png", "image_base64": PNG_B64},
         422, "INVALID_REQUEST"),
        ("missing_image", {"image_mime": "image/png",
                           "expected_text": "限时优惠"},
         422, "INVALID_REQUEST"),
        ("wrong_type_base64",
         {"image_mime": "image/png", "image_base64": 123,
          "expected_text": "限时优惠"},
         422, "INVALID_REQUEST"),
        ("unknown_field",
         {"image_mime": "image/png", "image_base64": PNG_B64,
          "expected_text": "限时优惠", "surprise": True},
         422, "INVALID_REQUEST"),
    ],
    ids=["missing_expected_text", "missing_image", "wrong_type_base64",
         "unknown_field"],
)
def test_check_request_validation(live_server, label, payload, status, code):
    base, _ = live_server
    got_status, raw = _http("POST", f"{base}/api/v1/check", body=payload)
    assert got_status == status, f"{label}: {raw[:300]}"
    assert json.loads(raw)["error"]["code"] == code


def test_check_malformed_json(live_server):
    base, _ = live_server
    status, raw = _http(
        "POST", f"{base}/api/v1/check", raw=b"{not json",
        headers={"Content-Type": "application/json"},
    )
    assert status == 422
    assert json.loads(raw)["error"]["code"] == "INVALID_REQUEST"


class _FailingAdapter:
    """Stub OCR engine that always raises (exercises OCR_FAILED)."""

    def recognize(self, image):
        raise RuntimeError("simulated engine failure")


def test_ocr_failure_direct():
    with pytest.raises(ApiError) as excinfo:
        run_check(
            image_mime="image/png", image_base64=PNG_B64,
            expected_text="限时优惠", adapter=_FailingAdapter(),
        )
    assert excinfo.value.code == "OCR_FAILED"
    assert excinfo.value.status == 500


def test_ocr_failure_via_http(live_server):
    base, _ = live_server
    set_ocr_adapter(_FailingAdapter())
    try:
        status, raw = _http(
            "POST", f"{base}/api/v1/check",
            body=_check_payload("TP-S0-ZH-001"),
        )
    finally:
        reset_ocr_adapter()
    assert status == 500, raw[:300]
    body = json.loads(raw)
    assert body["error"]["code"] == "OCR_FAILED"
    assert "schema" not in body


def test_run_check_error_mapping_direct():
    """run_check maps every T002 reason to its distinct API code."""
    cases = [
        (dict(image_mime="image/gif", image_base64=PNG_B64,
              expected_text="x"), "INVALID_IMAGE_MIME"),
        (dict(image_mime="image/png", image_base64="%%%",
              expected_text="x"), "INVALID_BASE64"),
        (dict(image_mime="image/png", image_base64=PNG_B64,
              expected_text="x" * 5001), "EXPECTED_TEXT_TOO_LONG"),
    ]
    for kwargs, code in cases:
        with pytest.raises(ApiError) as excinfo:
            run_check(**kwargs)
        assert excinfo.value.code == code
