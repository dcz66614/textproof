#!/usr/bin/env python3
"""T001 environment probe for P033 TextProof.

Prints OS, architecture, CPU, memory, disk, Python/pip/Git versions and
the availability of the frozen direct dependencies. Writes nothing outside
stdout; callers may redirect output to ENVIRONMENT.md evidence logs.

Usage:
    python3 scripts/env_probe.py [--json]
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import subprocess
import sys


def _run(argv: list[str]) -> str | None:
    try:
        out = subprocess.run(argv, capture_output=True, text=True, timeout=30)
    except Exception:
        return None
    text = (out.stdout or "").strip()
    return text or None


def _mem_total_bytes() -> int | None:
    try:
        with open("/proc/meminfo", encoding="utf-8") as fh:
            for line in fh:
                if line.startswith("MemTotal:"):
                    parts = line.split()
                    return int(parts[1]) * 1024
    except Exception:
        return None
    return None


def probe() -> dict:
    uname = platform.uname()
    disk = shutil.disk_usage(os.path.abspath(__file__))
    info: dict = {
        "os": platform.platform(),
        "os_system": uname.system,
        "os_release": uname.release,
        "os_version": uname.version,
        "kernel": f"{uname.system} {uname.release} {uname.version}",
        "architecture": platform.machine(),
        "processor": uname.processor or platform.processor(),
        "cpu_count_logical": os.cpu_count(),
        "cpu_count_physical": None,
        "memory_total_bytes": _mem_total_bytes(),
        "disk_total_bytes": disk.total,
        "disk_used_bytes": disk.used,
        "disk_free_bytes": disk.free,
        "disk_path": os.path.abspath(__file__),
        "python_version": platform.python_version(),
        "python_executable": sys.executable,
        "python_implementation": platform.python_implementation(),
        "pip_version": None,
        "git_version": None,
        "hostname": uname.node,
    }
    try:
        import multiprocessing

        info["cpu_count_physical"] = multiprocessing.cpu_count()
    except Exception:
        pass
    pip_out = _run([sys.executable, "-m", "pip", "--version"])
    if pip_out:
        info["pip_version"] = pip_out.split()[1] if len(pip_out.split()) > 1 else pip_out
    git_out = _run(["git", "--version"])
    if git_out:
        info["git_version"] = git_out.replace("git version ", "").strip()
    return info


def main() -> int:
    parser = argparse.ArgumentParser(description="Probe the build environment (T001).")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text.")
    args = parser.parse_args()

    info = probe()
    if args.json:
        print(json.dumps(info, indent=2, sort_keys=True))
        return 0

    mem_gib = (
        f"{info['memory_total_bytes'] / (1024 ** 3):.2f} GiB"
        if info["memory_total_bytes"]
        else "unknown"
    )
    print(f"OS: {info['os']}")
    print(f"Architecture: {info['architecture']}")
    print(f"Processor: {info['processor']}")
    print(f"CPU logical cores: {info['cpu_count_logical']}")
    print(f"Memory total: {mem_gib}")
    print(f"Disk total: {info['disk_total_bytes'] / (1024 ** 3):.2f} GiB")
    print(f"Disk free: {info['disk_free_bytes'] / (1024 ** 3):.2f} GiB")
    print(f"Python: {info['python_version']} ({info['python_executable']})")
    print(f"pip: {info['pip_version']}")
    print(f"Git: {info['git_version']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
