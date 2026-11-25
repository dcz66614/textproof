"""Capture T007 handoff evidence (one-off, not part of the product).

Starts the real API server (subprocess, 127.0.0.1, free port), records
one successful /check request+response and one request+response per
error code into task_handoffs/T007/fixtures/, and records the
loopback-listening proof (ss + /proc/net/tcp) into
task_handoffs/T007/loopback_proof.txt.

OCR_FAILED is captured through an in-process server thread with a
stub engine injected via routes.set_ocr_adapter (the subprocess
server cannot be monkey-patched); the HTTP envelope is identical.

Run:  .venv/bin/python task_handoffs/T007/capture_fixtures.py
"""

from __future__ import annotations

import asyncio
import base64
import io
import json
import socket
import struct
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
import zlib
from pathlib import Path

WORKTREE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(WORKTREE / "src"))
OUT = WORKTREE / "task_handoffs" / "T007" / "fixtures"
OUT.mkdir(parents=True, exist_ok=True)
FIXTURES = WORKTREE / "tests" / "fixtures" / "s0"
VENV_PY = "/home/hatch/workspace/p033-textproof/.venv/bin/python"


def _http(method, url, body=None, raw=None):
    data = raw
    headers = {}
    if body is not None:
        data = json.dumps(body).encode()
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            return resp.status, resp.read()
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read()


def _b64(data: bytes) -> str:
    return base64.b64encode(data).decode()


def _fake_png(w, h):
    ihdr = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)

    def chunk(tag, payload):
        body = tag + payload
        return struct.pack(">I", len(payload)) + body + struct.pack(
            ">I", zlib.crc32(body) & 0xFFFFFFFF
        )

    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) + chunk(b"IEND", b"")


def _animated_webp():
    from PIL import Image

    buf = io.BytesIO()
    Image.new("RGB", (100, 50), "white").save(
        buf, format="WEBP", save_all=True,
        append_images=[Image.new("RGB", (100, 50), "black")],
        duration=100, loop=0,
    )
    return buf.getvalue()


def _free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _save(name, request, status, response_raw):
    try:
        response = json.loads(response_raw)
    except Exception:
        response = {"<non-json>": response_raw[:500].decode("utf-8", "replace")}
    # Never store the 35 MB oversize payload verbatim.
    req = dict(request) if isinstance(request, dict) else request
    if isinstance(req, dict) and len(str(req.get("image_base64", ""))) > 100000:
        req = dict(req)
        req["image_base64"] = (
            f"<omitted: {len(req['image_base64'])} 'A' chars, "
            "exceeds 25 MiB decoded limit>"
        )
    (OUT / name).write_text(
        json.dumps(
            {"request": req, "response_status": status, "response": response},
            ensure_ascii=False, indent=2,
        ),
        encoding="utf-8",
    )
    print(f"wrote {name} status={status}")


def main():
    manifest = json.loads((FIXTURES / "manifest.json").read_text())
    zh001 = next(f for f in manifest["fixtures"] if f["id"] == "TP-S0-ZH-001")
    png = (FIXTURES / zh001["filename"]).read_bytes()
    png_b64 = _b64(png)
    port = _free_port()
    env = {"PYTHONPATH": str(WORKTREE / "src"), "PATH": "/usr/bin:/bin"}
    proc = subprocess.Popen(
        [VENV_PY, "-m", "textproof.api.app", "--port", str(port)],
        cwd=str(WORKTREE), env=env,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
    )
    base = f"http://127.0.0.1:{port}"
    try:
        for _ in range(100):
            try:
                s, _ = _http("GET", f"{base}/api/v1/health")
                if s == 200:
                    break
            except Exception:
                pass
            time.sleep(0.3)
        else:
            raise RuntimeError("server did not start")

        # Loopback proof while the server is alive.
        import shutil

        proof = [f"# loopback proof — server on 127.0.0.1:{port}",
                 f"# date: {time.strftime('%Y-%m-%d %H:%M:%S %Z')}"]
        ss = shutil.which("ss")
        if ss:
            proof.append(f"\n$ ss -tln\n{subprocess.run([ss, '-tln'], capture_output=True, text=True).stdout}")
        tcp_lines = [ln for ln in Path("/proc/net/tcp").read_text().splitlines()
                     if f":{port:04X}" in ln.upper()]
        proof.append(f"\n$ grep :{port:04X} /proc/net/tcp (LISTEN=0A)\n" + "\n".join(tcp_lines))
        with socket.create_connection(("127.0.0.1", port), timeout=5) as c:
            proof.append(f"\nconnect 127.0.0.1:{port}: OK (local {c.getsockname()})")
        proof.append(
            "\nNOTE: connect_ex to the non-loopback IP is NOT used as proof "
            "on this VM: outbound TCP is intercepted by the egress proxy "
            "(198.19.0.1:3128) and returns success even for unlistened ports. "
            "The /proc/net/tcp + ss LISTEN table above is the proof: the port "
            "listens on 127.0.0.1 only.")
        (WORKTREE / "task_handoffs" / "T007" / "loopback_proof.txt").write_text(
            "\n".join(proof), encoding="utf-8")
        print("wrote loopback_proof.txt")

        s, raw = _http("GET", f"{base}/api/v1/health")
        (OUT / "health_response.json").write_text(
            json.dumps({"status": s, "response": json.loads(raw)},
                       ensure_ascii=False, indent=2), encoding="utf-8")
        s, raw = _http("GET", f"{base}/api/v1/version")
        (OUT / "version_response.json").write_text(
            json.dumps({"status": s, "response": json.loads(raw)},
                       ensure_ascii=False, indent=2), encoding="utf-8")

        ok_req = {"image_mime": "image/png", "image_base64": png_b64,
                  "expected_text": "限时优惠"}
        s, raw = _http("POST", f"{base}/api/v1/check", body=ok_req)
        assert s == 200, raw[:300]
        _save("check_success.json", ok_req, s, raw)

        from textproof.api.routes import _MAX_BASE64_CHARS

        cases = [
            ("error_INVALID_IMAGE_MIME.json",
             {"image_mime": "image/gif", "image_base64": png_b64,
              "expected_text": "限时优惠"}),
            ("error_INVALID_BASE64.json",
             {"image_mime": "image/png", "image_base64": "!!!not-b64!!!",
              "expected_text": "限时优惠"}),
            ("error_INVALID_IMAGE_FORMAT.json",
             {"image_mime": "image/png",
              "image_base64": _b64(b"hello world, not an image"),
              "expected_text": "限时优惠"}),
            ("error_INVALID_IMAGE.json",
             {"image_mime": "image/png",
              "image_base64": _b64(b"\x89PNG\r\n\x1a\n" + b"\x00" * 64),
              "expected_text": "限时优惠"}),
            ("error_ANIMATED_IMAGE_NOT_SUPPORTED.json",
             {"image_mime": "image/webp",
              "image_base64": _b64(_animated_webp()),
              "expected_text": "限时优惠"}),
            ("error_IMAGE_DIMENSION_EXCEEDED.json",
             {"image_mime": "image/png",
              "image_base64": _b64(_fake_png(9000, 10)),
              "expected_text": "限时优惠"}),
            ("error_IMAGE_TOO_MANY_PIXELS.json",
             {"image_mime": "image/png",
              "image_base64": _b64(_fake_png(8000, 6000)),
              "expected_text": "限时优惠"}),
            ("error_IMAGE_TOO_LARGE.json",
             {"image_mime": "image/png",
              "image_base64": "A" * (_MAX_BASE64_CHARS + 4),
              "expected_text": "限时优惠"}),
            ("error_EXPECTED_TEXT_EMPTY.json",
             {"image_mime": "image/png", "image_base64": png_b64,
              "expected_text": ""}),
            ("error_EXPECTED_TEXT_TOO_LONG.json",
             {"image_mime": "image/png", "image_base64": png_b64,
              "expected_text": "x" * 5001}),
            ("error_EXPECTED_TEXT_TOO_MANY_LINES.json",
             {"image_mime": "image/png", "image_base64": png_b64,
              "expected_text": "\n".join(["a"] * 101)}),
        ]
        for name, req in cases:
            s, raw = _http("POST", f"{base}/api/v1/check", body=req)
            _save(name, req, s, raw)

        # INVALID_REQUEST: missing field.
        s, raw = _http("POST", f"{base}/api/v1/check",
                       body={"image_mime": "image/png", "image_base64": png_b64})
        _save("error_INVALID_REQUEST.json",
              {"image_mime": "image/png", "image_base64": "<fixture png b64>",
               "expected_text": "<MISSING>"},
              s, raw)
    finally:
        proc.terminate()
        proc.wait(timeout=15)

    # OCR_FAILED via in-process server + stub engine.
    import uvicorn
    from textproof.api.app import create_app
    from textproof.api.routes import reset_ocr_adapter, set_ocr_adapter

    class _Failing:
        def recognize(self, image):
            raise RuntimeError("simulated engine failure")

    port2 = _free_port()
    server = uvicorn.Server(uvicorn.Config(
        create_app(), host="127.0.0.1", port=port2, log_level="error"))
    thread = threading.Thread(target=asyncio.run, args=(server.serve(),),
                              daemon=True)
    thread.start()
    base2 = f"http://127.0.0.1:{port2}"
    try:
        for _ in range(100):
            try:
                s, _ = _http("GET", f"{base2}/api/v1/health")
                if s == 200:
                    break
            except Exception:
                pass
            time.sleep(0.3)
        set_ocr_adapter(_Failing())
        try:
            req = {"image_mime": "image/png", "image_base64": png_b64,
                   "expected_text": "限时优惠"}
            s, raw = _http("POST", f"{base2}/api/v1/check", body=req)
            _save("error_OCR_FAILED.json", req, s, raw)
        finally:
            reset_ocr_adapter()
    finally:
        server.should_exit = True
        thread.join(timeout=15)
    print("done.")


if __name__ == "__main__":
    main()
