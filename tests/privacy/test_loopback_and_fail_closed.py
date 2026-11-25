"""T010 acceptance 7: loopback-only listening + fail-closed inputs.

* Loopback: ``validate_bind_host`` / ``serve`` reject every
  non-``127.0.0.1`` host before binding, and the live server's
  LISTEN socket is ``127.0.0.1`` only, read from the kernel table
  ``/proc/net/tcp`` — NOT from ``connect_ex`` (egress-proxy
  false-positive, see T007).
* Fail-closed inputs: the T002/T007 limits are re-asserted here at
  the HTTP + CLI level for the privacy scope (oversize, bad base64,
  corrupt/truncated, animated WebP, dimension / pixel caps, bad
  MIME, empty / over-long expected text), plus the extension test:
  a PNG renamed to ``.jpg`` is still read as PNG (magic bytes win),
  while a declared MIME that disagrees with the bytes is rejected.
* Shell / arbitrary-path writes: no ``shell=True`` / ``os.system`` /
  ``eval`` / ``exec`` in ``src/``; :func:`load_image` takes bytes
  only, so no request can name a file path.
* Export warning (§9 bullet 7): the UI must warn that the JSON
  export may contain sensitive text (T010 finding F-T010-01: the
  warning was missing from the shipped UI and was added by this
  task — see PRIVACY_TEST_REPORT.md).
"""

from __future__ import annotations

import base64
import inspect
import io
import json
import socket
import struct
import urllib.request
import zlib
from pathlib import Path

import pytest
from PIL import Image

# The too-many-pixels case feeds Pillow a 48 MP header; its
# DecompressionBombWarning is expected, not a test failure.
pytestmark = pytest.mark.filterwarnings(
    "ignore:Image size .* exceeds limit.*:Warning"
)

from t010_privacy_helpers import (
    REPO_ROOT,
    _http,
    fixture_b64,
    fixture_bytes,
)

from textproof.api.app import serve, validate_bind_host
from textproof.api.routes import _MAX_BASE64_CHARS
from textproof.cli import main as cli_main
from textproof.io.image_loader import detect_format, load_image


def _fake_png(width: int, height: int) -> bytes:
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)

    def chunk(tag: bytes, payload: bytes) -> bytes:
        body = tag + payload
        return (struct.pack(">I", len(payload)) + body
                + struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF))

    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
            + chunk(b"IEND", b""))


def _animated_webp_bytes() -> bytes:
    buf = io.BytesIO()
    first = Image.new("RGB", (100, 50), "white")
    second = Image.new("RGB", (100, 50), "black")
    first.save(buf, format="WEBP", save_all=True,
               append_images=[second], duration=100, loop=0)
    return buf.getvalue()


PNG_B64 = fixture_b64("TP-S0-ZH-001")


@pytest.mark.parametrize("host", [
    "0.0.0.0", "198.19.0.2", "8.8.8.8", "localhost", "::1", "",
    "  ", "example.com", "127.0.0.2", "0",
])
def test_bind_host_rejects_non_loopback(host):
    with pytest.raises(ValueError):
        validate_bind_host(host)


def test_bind_host_accepts_only_127_0_0_1():
    assert validate_bind_host("127.0.0.1") == "127.0.0.1"


@pytest.mark.parametrize("host", ["0.0.0.0", "198.19.0.2", "localhost"])
def test_serve_rejects_non_loopback_host(host):
    with pytest.raises(ValueError):
        serve(host=host, port=18799)


def test_server_listens_only_on_loopback(live_server):
    """LISTEN sockets for the server port, from /proc/net/tcp."""
    base = live_server
    port = int(base.rsplit(":", 1)[1])
    with socket.create_connection(("127.0.0.1", port), timeout=5):
        pass
    port_hex = f"{port:04X}"
    listeners = []
    for line in Path("/proc/net/tcp").read_text().splitlines()[1:]:
        parts = line.split()
        ip_hex, port_part = parts[1].split(":")
        if port_part.upper() == port_hex and parts[3] == "0A":
            listeners.append(ip_hex)
    assert listeners, f"no LISTEN socket found for port {port}"
    assert listeners == ["0100007F"], (
        f"server listens on {listeners}, expected only 127.0.0.1")


def test_no_cors_header(live_server):
    req = urllib.request.Request(
        f"{live_server}/api/v1/health",
        headers={"Origin": "https://example.com"}, method="GET")
    with urllib.request.urlopen(req, timeout=30) as resp:
        assert resp.headers.get("Access-Control-Allow-Origin") is None


# --- fail-closed inputs (HTTP level) --------------------------------------

ERROR_CASES = [
    ("unsupported_mime",
     {"image_mime": "image/gif", "image_base64": PNG_B64,
      "expected_text": "限时优惠"}, 400, "INVALID_IMAGE_MIME"),
    ("mime_mismatch",
     {"image_mime": "image/jpeg", "image_base64": PNG_B64,
      "expected_text": "限时优惠"}, 400, "INVALID_IMAGE_MIME"),
    ("invalid_base64",
     {"image_mime": "image/png", "image_base64": "!!!not-base64!!!",
      "expected_text": "限时优惠"}, 400, "INVALID_BASE64"),
    ("empty_base64",
     {"image_mime": "image/png", "image_base64": "",
      "expected_text": "限时优惠"}, 400, "INVALID_BASE64"),
    ("non_image_bytes",
     {"image_mime": "image/png",
      "image_base64": base64.b64encode(b"hello world, not an image")
      .decode("ascii"), "expected_text": "限时优惠"},
     400, "INVALID_IMAGE_FORMAT"),
    ("corrupt_png",
     {"image_mime": "image/png",
      "image_base64": base64.b64encode(b"\x89PNG\r\n\x1a\n" + b"\x00" * 64)
      .decode("ascii"), "expected_text": "限时优惠"},
     400, "INVALID_IMAGE"),
    ("animated_webp",
     {"image_mime": "image/webp",
      "image_base64": base64.b64encode(_animated_webp_bytes())
      .decode("ascii"), "expected_text": "限时优惠"},
     400, "ANIMATED_IMAGE_NOT_SUPPORTED"),
    ("dimension_exceeded",
     {"image_mime": "image/png",
      "image_base64": base64.b64encode(_fake_png(9000, 10))
      .decode("ascii"), "expected_text": "限时优惠"},
     400, "IMAGE_DIMENSION_EXCEEDED"),
    ("too_many_pixels",
     {"image_mime": "image/png",
      "image_base64": base64.b64encode(_fake_png(8000, 6000))
      .decode("ascii"), "expected_text": "限时优惠"},
     400, "IMAGE_TOO_MANY_PIXELS"),
    ("image_too_large",
     {"image_mime": "image/png",
      "image_base64": "A" * (_MAX_BASE64_CHARS + 4),
      "expected_text": "限时优惠"}, 400, "IMAGE_TOO_LARGE"),
    ("expected_text_empty",
     {"image_mime": "image/png", "image_base64": PNG_B64,
      "expected_text": ""}, 400, "EXPECTED_TEXT_EMPTY"),
    ("expected_text_too_long",
     {"image_mime": "image/png", "image_base64": PNG_B64,
      "expected_text": "x" * 5001}, 400, "EXPECTED_TEXT_TOO_LONG"),
    ("expected_text_too_many_lines",
     {"image_mime": "image/png", "image_base64": PNG_B64,
      "expected_text": "\n".join(["a"] * 101)},
     400, "EXPECTED_TEXT_TOO_MANY_LINES"),
]


@pytest.mark.parametrize(
    "label,payload,status,code", ERROR_CASES,
    ids=[c[0] for c in ERROR_CASES],
)
def test_check_error_cases_fail_closed(
    live_server, label, payload, status, code
):
    got_status, raw = _http(
        "POST", f"{live_server}/api/v1/check", body=payload)
    assert got_status == status, f"{label}: {raw[:300]}"
    body = json.loads(raw)
    assert body["error"]["code"] == code, f"{label}: {body}"
    assert "schema" not in body  # an error is not a report


def test_extension_is_ignored_magic_bytes_win(tmp_path, capsys):
    """A PNG file named .jpg is read as PNG; MIME comes from bytes."""
    misnamed = tmp_path / "photo.jpg"  # PNG bytes, JPEG extension
    misnamed.write_bytes(fixture_bytes("TP-S0-ZH-001"))
    expected = tmp_path / "expected.txt"
    expected.write_text("限时优惠", encoding="utf-8")
    assert detect_format(misnamed.read_bytes()) == "PNG"
    exit_code = cli_main([
        "check", "--image", str(misnamed),
        "--expected-file", str(expected)])
    assert exit_code in (1, 2)
    report = json.loads(capsys.readouterr().out)
    assert report["image"]["format"] == "PNG"


def test_image_loader_takes_bytes_only_no_path_parameter():
    """No request can name a file path: load_image(bytes) only."""
    params = list(inspect.signature(load_image).parameters)
    assert params == ["data"], f"load_image signature changed: {params}"
    params = list(inspect.signature(detect_format).parameters)
    assert params == ["data"]


def test_no_shell_or_eval_in_sources():
    for token in ("shell=True", "os.system", "eval(", "exec(",
                  "commands.getoutput", "popen("):
        hits = []
        for path in REPO_ROOT.glob("src/**/*.py"):
            for lineno, line in enumerate(
                    path.read_text(encoding="utf-8").splitlines(), 1):
                if token in line.split("#", 1)[0]:
                    hits.append(f"{path.relative_to(REPO_ROOT)}:{lineno}")
        assert hits == [], f"token {token!r} found in: {hits}"


def test_export_warning_present_in_ui(live_server):
    """§9: the UI warns the JSON export may contain sensitive text."""
    html = (REPO_ROOT / "src" / "textproof" / "ui" / "index.html") \
        .read_text(encoding="utf-8")
    assert "可能包含敏感文字" in html
    status, raw = _http("GET", f"{live_server}/")
    assert status == 200
    assert "可能包含敏感文字" in raw.decode("utf-8"), (
        "export warning missing from the served UI")
