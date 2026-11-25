"""In-namespace probe for the offline serve test.

Run as ``unshare -n <venv python> _serve_probe.py --port P``.  The
server runs inside the same network namespace as this probe.

Environment fact (verified 2026-11-25 on this VM): ``unshare -n``
here grants no ``CAP_NET_ADMIN``, so the namespace's loopback
interface stays DOWN and cannot be brought up (``ip link set lo
up`` → ``Operation not permitted``); even a connect to 127.0.0.1
fails with ``ENETUNREACH``.  A live HTTP health check inside the
namespace is therefore impossible — NOT a product failure.  What
this probe proves instead, from the kernel's own tables inside the
namespace:

* the server process starts and stays alive with no network;
* its LISTEN socket is ``127.0.0.1:<port>`` and nothing else
  (``/proc/net/tcp`` is network-namespace aware, unlike
  ``/sys/class/net`` on this VM).

The HTTP half of serve is covered where loopback works: the
in-process live servers in ``tests/privacy/`` and T007/T009.
Prints ``SERVE_PROBE_PASS`` and exits 0 on success.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path


def _listen_addresses(port: int) -> list[str]:
    """Local addresses in LISTEN state (0A) for *port*, from the
    kernel table of the current network namespace."""
    port_hex = f"{port:04X}"
    found = []
    for line in Path("/proc/net/tcp").read_text().splitlines()[1:]:
        parts = line.split()
        ip_hex, port_part = parts[1].split(":")
        if port_part.upper() == port_hex and parts[3] == "0A":
            found.append(ip_hex)
    return found


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("--log-file", type=Path, required=True)
    args = parser.parse_args(argv)
    with open(args.log_file, "w", encoding="utf-8") as log:
        proc = subprocess.Popen(
            [sys.executable, "-m", "textproof.api.app",
             "--port", str(args.port)],
            stdout=log, stderr=subprocess.STDOUT, text=True)
    try:
        deadline = time.monotonic() + 60
        listeners: list[str] = []
        while time.monotonic() < deadline:
            if proc.poll() is not None:
                print("server exited early", file=sys.stderr)
                print(args.log_file.read_text(encoding="utf-8"),
                      file=sys.stderr)
                return 1
            listeners = _listen_addresses(args.port)
            if listeners:
                break
            time.sleep(0.5)
        if listeners != ["0100007F"]:
            print(f"server LISTEN sockets for port {args.port}: "
                  f"{listeners} (expected only 127.0.0.1)",
                  file=sys.stderr)
            print(args.log_file.read_text(encoding="utf-8"),
                  file=sys.stderr)
            return 1
        print("SERVE_PROBE_PASS")
        return 0
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=15)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=15)


if __name__ == "__main__":
    sys.exit(main())
