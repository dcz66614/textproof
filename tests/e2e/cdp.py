"""Minimal Chrome DevTools Protocol client (stdlib only, T008).

No new dependency is allowed (frozen ``requirements.lock``), so the
E2E tests drive the headless Chrome binary found in the Playwright
browser cache (or ``CHROME_PATH``) over a raw WebSocket implemented
here with :mod:`socket` / :mod:`base64` / :mod:`struct`.  Only the
CDP methods the tests need are wrapped; everything else goes through
:meth:`CDPClient.call`.

The client records every ``Network.requestWillBeSent`` event so the
tests can prove, from the browser's own log, that the page only ever
talked to the same-origin local server (the external-request
interception log required by the T008 card).
"""

from __future__ import annotations

import base64
import glob
import json
import os
import shutil
import socket
import struct
import subprocess
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

__all__ = ["CDPError", "Chrome", "Page", "find_chrome",
           "STORAGE_TRAP_SCRIPT", "navigate_fresh"]


#: Injected before every navigation: records any access to persistent
#: browser storage.  The UI must never touch it (T008 acceptance 6).
STORAGE_TRAP_SCRIPT = """
window.__tpStorageAccess = [];
(function () {
  var names = ["localStorage", "sessionStorage"];
  names.forEach(function (name) {
    try {
      var desc = Object.getOwnPropertyDescriptor(Window.prototype, name);
      if (!desc || !desc.get) return;
      var realGet = desc.get;
      Object.defineProperty(window, name, {
        configurable: true,
        get: function () {
          window.__tpStorageAccess.push(name);
          return realGet.call(window);
        },
      });
    } catch (e) { /* trap install failure must not break the page */ }
  });
  try {
    /* Read the real value through the prototype descriptor, NOT
     * through window.indexedDB: on later navigations an earlier copy
     * of this trap may already shadow it, and a plain read would
     * trip that trap (false positive on the second test onwards). */
    var idbDesc = Object.getOwnPropertyDescriptor(
      Window.prototype, "indexedDB");
    var realIDB = (idbDesc && idbDesc.get)
      ? idbDesc.get.call(window)
      : undefined;
    Object.defineProperty(window, "indexedDB", {
      configurable: true,
      get: function () {
        window.__tpStorageAccess.push("indexedDB");
        return realIDB;
      },
    });
  } catch (e) { /* ignore */ }
})();
"""


def navigate_fresh(page, base: str) -> None:
    """Navigate to the UI with the storage trap installed first."""
    page.enable()
    page.add_init_script(STORAGE_TRAP_SCRIPT)
    page.navigate(base + "/")
    page.wait_for(
        "document.querySelector('#btn-check') !== null",
        timeout=30, desc="UI controls to render",
    )


class CDPError(Exception):
    """A CDP call failed, or Chrome did not come up."""


def find_chrome() -> str:
    """Locate a Chrome/Chromium binary (no install, no download)."""
    env = os.environ.get("CHROME_PATH")
    if env and Path(env).is_file():
        return env
    which = shutil.which("chromium") or shutil.which("chromium-browser") \
        or shutil.which("google-chrome") or shutil.which("chrome")
    if which:
        return which
    candidates = sorted(
        glob.glob(
            str(Path.home() / ".cache/ms-playwright/chromium-*/chrome-linux64/chrome")
        )
    )
    if candidates:
        return candidates[-1]
    candidates = sorted(
        glob.glob(
            str(Path.home()
                / ".cache/ms-playwright/chromium_headless_shell-*/"
                "chrome-headless-shell-linux64/chrome-headless-shell")
        )
    )
    if candidates:
        return candidates[-1]
    raise CDPError(
        "No Chrome binary found (checked CHROME_PATH, PATH, and the "
        "Playwright browser cache under ~/.cache/ms-playwright)."
    )


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


class _WS:
    """A minimal WebSocket client (RFC 6455, text frames)."""

    def __init__(self, url: str, timeout: float = 60.0) -> None:
        rest = url.split("://", 1)[1]
        hostport, _, path = rest.partition("/")
        host, _, port = hostport.partition(":")
        self._sock = socket.create_connection(
            (host, int(port) if port else 80), timeout=timeout
        )
        self._sock.settimeout(timeout)
        self._buf = bytearray()
        key = base64.b64encode(os.urandom(16)).decode("ascii")
        req = (
            f"GET /{path} HTTP/1.1\r\n"
            f"Host: {hostport}\r\n"
            "Upgrade: websocket\r\n"
            "Connection: Upgrade\r\n"
            f"Sec-WebSocket-Key: {key}\r\n"
            "Sec-WebSocket-Version: 13\r\n\r\n"
        )
        self._sock.sendall(req.encode("ascii"))
        head = b""
        while b"\r\n\r\n" not in head:
            chunk = self._sock.recv(4096)
            if not chunk:
                raise CDPError("WebSocket handshake: connection closed")
            head += chunk
        if b" 101 " not in head.split(b"\r\n", 1)[0]:
            raise CDPError(f"WebSocket handshake failed: {head[:200]!r}")

    def _read_exact(self, n: int) -> bytes:
        while len(self._buf) < n:
            chunk = self._sock.recv(65536)
            if not chunk:
                raise CDPError("WebSocket: connection closed")
            self._buf += chunk
        out = bytes(self._buf[:n])
        del self._buf[:n]
        return out

    def send_text(self, payload: bytes) -> None:
        mask = os.urandom(4)
        masked = bytes(b ^ mask[i % 4] for i, b in enumerate(payload))
        header = bytearray([0x81])
        n = len(payload)
        if n < 126:
            header.append(0x80 | n)
        elif n < 65536:
            header.append(0x80 | 126)
            header += struct.pack(">H", n)
        else:
            header.append(0x80 | 127)
            header += struct.pack(">Q", n)
        self._sock.sendall(bytes(header) + mask + masked)

    def recv_text(self) -> str:
        """Read one complete text message (handles fragmentation/ping)."""
        fragments = []
        while True:
            b1, b2 = self._read_exact(2)
            fin = bool(b1 & 0x80)
            opcode = b1 & 0x0F
            masked = bool(b2 & 0x80)
            length = b2 & 0x7F
            if length == 126:
                length = struct.unpack(">H", self._read_exact(2))[0]
            elif length == 127:
                length = struct.unpack(">Q", self._read_exact(8))[0]
            mask = self._read_exact(4) if masked else None
            data = self._read_exact(length)
            if mask:
                data = bytes(b ^ mask[i % 4] for i, b in enumerate(data))
            if opcode == 0x9:  # ping -> pong
                self._send_frame(0xA, data)
                continue
            if opcode == 0x8:
                raise CDPError("WebSocket: server closed the connection")
            fragments.append(data)
            if fin:
                return b"".join(fragments).decode("utf-8")

    def _send_frame(self, opcode: int, payload: bytes) -> None:
        mask = os.urandom(4)
        masked = bytes(b ^ mask[i % 4] for i, b in enumerate(payload))
        header = bytearray([0x80 | opcode])
        n = len(payload)
        if n < 126:
            header.append(0x80 | n)
        elif n < 65536:
            header.append(0x80 | 126)
            header += struct.pack(">H", n)
        else:
            header.append(0x80 | 127)
            header += struct.pack(">Q", n)
        self._sock.sendall(bytes(header) + mask + masked)

    def close(self) -> None:
        try:
            self._send_frame(0x8, b"")
        except Exception:
            pass
        try:
            self._sock.close()
        except Exception:
            pass


class CDPClient:
    """One CDP session; ``events`` collects non-reply messages."""

    def __init__(self, ws_url: str) -> None:
        self._ws = _WS(ws_url)
        self._next_id = 1
        self.events: list[dict[str, Any]] = []

    def call(self, method: str, params: dict[str, Any] | None = None,
             timeout: float = 120.0) -> dict[str, Any]:
        msg_id = self._next_id
        self._next_id += 1
        self._ws._sock.settimeout(timeout)
        self._ws.send_text(json.dumps(
            {"id": msg_id, "method": method, "params": params or {}}
        ).encode("utf-8"))
        deadline = time.monotonic() + timeout
        while True:
            if time.monotonic() > deadline:
                raise CDPError(f"CDP call {method} timed out after {timeout}s")
            raw = self._ws.recv_text()
            msg = json.loads(raw)
            if msg.get("id") == msg_id:
                if "error" in msg:
                    raise CDPError(f"CDP {method} failed: {msg['error']}")
                return msg.get("result", {})
            self.events.append(msg)

    def drain_events(self) -> list[dict[str, Any]]:
        """Collect events already buffered (non-blocking best effort)."""
        self._ws._sock.settimeout(0.3)
        try:
            while True:
                raw = self._ws.recv_text()
                self.events.append(json.loads(raw))
        except (socket.timeout, TimeoutError):
            pass
        except CDPError:
            pass
        finally:
            self._ws._sock.settimeout(120.0)
        return self.events

    def close(self) -> None:
        self._ws.close()


class Page:
    """One headless-Chrome tab driving the TextProof UI."""

    def __init__(self, client: CDPClient) -> None:
        self.cdp = client

    def enable(self) -> None:
        self.cdp.call("Page.enable")
        self.cdp.call("Runtime.enable")
        self.cdp.call("Network.enable")
        self.cdp.call("DOM.enable")

    def add_init_script(self, source: str) -> None:
        self.cdp.call("Page.addScriptToEvaluateOnNewDocument",
                      {"source": source})

    def navigate(self, url: str) -> None:
        self.cdp.call("Page.navigate", {"url": url})
        self.wait_for("document.readyState === 'complete'", timeout=30)

    def evaluate(self, expression: str, await_promise: bool = False,
                 timeout: float = 120.0) -> Any:
        result = self.cdp.call(
            "Runtime.evaluate",
            {"expression": expression, "returnByValue": True,
             "awaitPromise": await_promise},
            timeout=timeout,
        )
        if result.get("exceptionDetails"):
            raise CDPError(
                f"JS evaluate failed: {result['exceptionDetails']}")
        return result.get("result", {}).get("value")

    def wait_for(self, expression: str, timeout: float = 120.0,
                 desc: str = "") -> Any:
        deadline = time.monotonic() + timeout
        last: Any = None
        while True:
            last = self.evaluate(expression)
            if last:
                return last
            if time.monotonic() > deadline:
                raise CDPError(
                    f"Timed out after {timeout}s waiting for: "
                    f"{desc or expression} (last value: {last!r})")
            time.sleep(0.25)

    def click(self, selector: str) -> None:
        rect = self.evaluate(
            "(function(){var n=document.querySelector("
            + json.dumps(selector)
            + ");if(!n) return null;var r=n.getBoundingClientRect();"
              "return {x:r.left+r.width/2,y:r.top+r.height/2};})()"
        )
        if rect is None:
            raise CDPError(f"click: no element matches {selector}")
        x, y = rect["x"], rect["y"]
        for typ in ("mousePressed", "mouseReleased"):
            self.cdp.call("Input.dispatchMouseEvent",
                          {"type": typ, "x": x, "y": y,
                           "button": "left", "clickCount": 1})
        time.sleep(0.2)

    def set_file_input(self, selector: str, path: str) -> None:
        doc = self.cdp.call("DOM.getDocument", {"depth": -1})
        node = self.cdp.call(
            "DOM.querySelector",
            {"nodeId": doc["root"]["nodeId"], "selector": selector})
        if not node.get("nodeId"):
            raise CDPError(f"set_file_input: no element matches {selector}")
        self.cdp.call("DOM.setFileInputFiles",
                      {"nodeId": node["nodeId"], "files": [path]})

    def set_textarea(self, selector: str, text: str) -> None:
        self.evaluate(
            "(function(){var n=document.querySelector(" + json.dumps(selector)
            + ");n.value=" + json.dumps(text)
            + ";n.dispatchEvent(new Event('input',{bubbles:true}));})()"
        )

    def screenshot(self, path: Path) -> Path:
        result = self.cdp.call("Page.captureScreenshot", {"format": "png"})
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(base64.b64decode(result["data"]))
        return path

    def network_requests(self) -> list[dict[str, Any]]:
        """All requests the page issued, from the CDP event log."""
        out = []
        for ev in self.cdp.events:
            if ev.get("method") == "Network.requestWillBeSent":
                p = ev.get("params", {})
                out.append({
                    "url": p.get("request", {}).get("url", ""),
                    "method": p.get("request", {}).get("method", ""),
                    "type": p.get("type", ""),
                })
        return out


class Chrome:
    """A headless Chrome process with one page target."""

    def __init__(self) -> None:
        self.chrome = find_chrome()
        self.port = _free_port()
        self.profile = Path(tempfile.mkdtemp(prefix="textproof-chrome-"))
        self.proc = subprocess.Popen(
            [self.chrome, "--headless=new", "--no-sandbox", "--disable-gpu",
             "--disable-dev-shm-usage", "--no-first-run",
             "--no-default-browser-check", "--hide-scrollbars",
             f"--remote-debugging-port={self.port}",
             f"--user-data-dir={self.profile}",
             "--window-size=1400,1000", "about:blank"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        self.page: Page | None = None
        self._browser_ws: CDPClient | None = None
        try:
            self._wait_ready()
        except Exception:
            self.stop()
            raise

    def _http_json(self, path: str) -> Any:
        req = urllib.request.Request(
            f"http://127.0.0.1:{self.port}{path}")
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def _wait_ready(self) -> None:
        deadline = time.monotonic() + 60
        while True:
            try:
                self._http_json("/json/version")
                return
            except Exception:
                if self.proc.poll() is not None:
                    raise CDPError(
                        f"Chrome exited early (code {self.proc.returncode})")
                if time.monotonic() > deadline:
                    raise CDPError("Chrome did not come up in 60s")
                time.sleep(0.2)

    def new_page(self) -> Page:
        targets = self._http_json("/json/list")
        page_targets = [t for t in targets if t.get("type") == "page"]
        if not page_targets:
            raise CDPError("Chrome has no page target")
        self.page = Page(CDPClient(page_targets[0]["webSocketDebuggerUrl"]))
        return self.page

    def browser_client(self) -> CDPClient:
        if self._browser_ws is None:
            version = self._http_json("/json/version")
            self._browser_ws = CDPClient(version["webSocketDebuggerUrl"])
        return self._browser_ws

    def set_download_dir(self, path: Path) -> None:
        path.mkdir(parents=True, exist_ok=True)
        self.browser_client().call(
            "Browser.setDownloadBehavior",
            {"behavior": "allow", "downloadPath": str(path)})

    def grant_clipboard(self) -> None:
        try:
            self.browser_client().call(
                "Browser.grantPermissions",
                {"permissions": ["clipboardReadWrite",
                                 "clipboardSanitizedWrite"]})
        except CDPError:
            pass  # copy test accepts the fallback message instead

    def stop(self) -> None:
        try:
            if self.page is not None:
                self.page.cdp.close()
        except Exception:
            pass
        try:
            if self._browser_ws is not None:
                self._browser_ws.close()
        except Exception:
            pass
        if self.proc.poll() is None:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.proc.kill()
        shutil.rmtree(self.profile, ignore_errors=True)
