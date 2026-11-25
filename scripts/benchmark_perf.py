"""1920x1080 performance benchmark for P033 TextProof (T011).

Measures the §8.3 runtime threshold on the full product check path:
``1920x1080 合成图，预热后 30 次测量 P95 <= 5s`` (PROJECT_BOOK.md
§8.3).  One run = the production pipeline end to end — T002 image
loading + T003 RapidOCR (CPU-only) + T004 compare + §5 report — driven
through :func:`textproof.api.routes.run_check`, the same entry point
the API and the CLI use, so the timing covers exactly what a user
waits for.

The benchmark image is NOT an S0 fixture: the frozen fixtures are
1200x480 (``tests/fixtures/s0/manifest.json``) and that manifest is
never modified by this script.  The 1920x1080 image is generated here
from the same bundled Noto Sans SC font (``load_font`` from
``scripts/generate_fixtures.py``, font SHA-256 pinned) with a fixed
seed, four lines of mixed Chinese / English / numeric poster text at
the frozen 64 px size on a white canvas; its SHA-256 is recorded in
the output so the measurement is reproducible.  The expected text is
the drawn text.  NOTE (FIX-R1, measured twice): the check verdict is
MISMATCH, not MATCH — the OCR drops two inter-word spaces (E001/E002
``MISSING_CHARACTER``) and reads "减" (U+51CF) as "減" (U+6E1B,
E003 ``SUBSTITUTION``), 3 errors in total, identical
in T011 and in the FIX-R1 re-measurement.  The timing gate constrains
time only, so the verdict does not affect the measurement; the image
and the expected text are unchanged.

Method:

* warm-up runs (default 3) load the OCR models and are excluded;
* 30 measured runs, wall time per run via ``time.perf_counter``;
* P50 / P95 use the linear-interpolation percentile (numpy
  ``percentile(..., method="linear")``), reported alongside mean /
  min / max;
* environment (CPU model + cores, OS, Python, RapidOCR /
  onnxruntime / Pillow / FastAPI / uvicorn / pydantic versions, ONNX
  providers, model file names + SHA-256) is recorded in the summary.

Raw per-run measurements are written as JSONL (one object per run)
and the summary as JSON.  Exit code 0 iff P95 <= 5.0 s; a P95 above
the threshold is reported as a failure for T013, never by editing
the threshold or cherry-picking the data.

Usage::

    python scripts/benchmark_perf.py --out task_handoffs/T011/perf_measurements.jsonl \
        --summary task_handoffs/T011/perf_summary.json \
        --image-out task_handoffs/T011/perf_image_1920x1080.png
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import io
import json
import platform
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))
sys.path.insert(0, str(REPO_ROOT))

from PIL import Image, ImageDraw  # noqa: E402

from scripts.generate_fixtures import (  # noqa: E402
    FONT_FILE_NAME,
    FONT_SIZE_PX,
    load_font,
)
from textproof.api.routes import run_check  # noqa: E402
from textproof.ocr.rapidocr_adapter import (  # noqa: E402
    ALLOWED_PROVIDERS,
    RapidOCRAdapter,
)

# --- benchmark image -------------------------------------------------------
# Fixed seed; the text lines are fixed literals (the seed is recorded
# for provenance and drives nothing random — the image is fully
# determined by this file).  Four lines of mixed poster text at the
# frozen 64 px size, laid out like a typical AI-image poster.
SEED = 20261125
CANVAS_WIDTH = 1920
CANVAS_HEIGHT = 1080
PERF_LINES = [
    "限时优惠 全场5折",
    "新品上市 会员专享",
    "新客立减20元",
    "SALE 50% OFF ￥28.80",
]
LINE_GAP_PX = 40

P95_THRESHOLD_S = 5.0
DEFAULT_RUNS = 30
DEFAULT_WARMUP = 3


def render_perf_image(font) -> tuple[bytes, str]:
    """Render the 1920x1080 benchmark image; return (png_bytes, sha256)."""
    img = Image.new("RGB", (CANVAS_WIDTH, CANVAS_HEIGHT), "white")
    draw = ImageDraw.Draw(img)
    # Vertical layout: centre the 4-line block on the canvas.
    line_boxes = [draw.textbbox((0, 0), line, font=font) for line in PERF_LINES]
    line_heights = [box[3] - box[1] for box in line_boxes]
    total_h = sum(line_heights) + LINE_GAP_PX * (len(PERF_LINES) - 1)
    y = (CANVAS_HEIGHT - total_h) // 2
    for line, box, line_h in zip(PERF_LINES, line_boxes, line_heights):
        line_w = box[2] - box[0]
        x = (CANVAS_WIDTH - line_w) // 2 - box[0]
        draw.text((x, y - box[1]), line, fill="black", font=font)
        y += line_h + LINE_GAP_PX
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    png = buf.getvalue()
    return png, hashlib.sha256(png).hexdigest()


def _cpu_model() -> str:
    try:
        for line in Path("/proc/cpuinfo").read_text(encoding="utf-8").splitlines():
            if line.startswith("model name"):
                return line.split(":", 1)[1].strip()
    except OSError:
        pass
    return platform.processor() or "unknown"


def _model_files() -> list[dict[str, object]]:
    """ONNX model files the adapter loads, with SHA-256 (best effort)."""
    import rapidocr  # noqa: PLC0415  (imported lazily; model dir lives here)

    import onnxruntime as ort  # noqa: PLC0415

    files: list[dict[str, object]] = []
    roots = [Path(rapidocr.__file__).resolve().parent]
    # RapidOCR ships its PP-OCRv5/v6 models under its package tree or a
    # user cache; walk both for *.onnx and hash what exists.
    cache = Path.home() / ".cache" / "rapidocr"
    if cache.is_dir():
        roots.append(cache)
    seen: set[str] = set()
    for root in roots:
        for path in sorted(root.rglob("*.onnx")):
            key = str(path)
            if key in seen:
                continue
            seen.add(key)
            digest = hashlib.sha256()
            with open(path, "rb") as fh:
                for chunk in iter(lambda: fh.read(1 << 20), b""):
                    digest.update(chunk)
            files.append({
                "path": str(path),
                "bytes": path.stat().st_size,
                "sha256": digest.hexdigest(),
            })
    return files


def environment() -> dict[str, object]:
    import importlib.metadata  # noqa: PLC0415

    def ver(dist: str) -> str:
        try:
            return importlib.metadata.version(dist)
        except importlib.metadata.PackageNotFoundError:
            return "not-installed"

    import onnxruntime as ort  # noqa: PLC0415
    from textproof.ocr.rapidocr_adapter import (  # noqa: PLC0415
        ONNXRUNTIME_VERSION,
        RAPIDOCR_VERSION,
    )

    return {
        "cpu_model": _cpu_model(),
        "cpu_count_logical": __import__("os").cpu_count(),
        "os": f"{platform.system()} {platform.release()} ({platform.version()})",
        "machine": platform.machine(),
        "python": platform.python_version(),
        "rapidocr": RAPIDOCR_VERSION,
        "onnxruntime": ONNXRUNTIME_VERSION,
        "onnxruntime_providers_available": ort.get_available_providers(),
        "onnxruntime_providers_used": list(ALLOWED_PROVIDERS),
        "pillow": ver("Pillow"),
        "fastapi": ver("fastapi"),
        "uvicorn": ver("uvicorn"),
        "pydantic": ver("pydantic"),
        "numpy": ver("numpy"),
        "model_files": _model_files(),
        "font": {
            "file": FONT_FILE_NAME,
            "size_px": FONT_SIZE_PX,
        },
    }


def percentile_sorted(sorted_values: list[float], pct: float) -> float:
    """Linear-interpolation percentile (numpy 'linear' method)."""
    import numpy as np  # noqa: PLC0415

    return float(np.percentile(sorted_values, pct, method="linear"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True,
                        help="Raw per-run measurements (JSONL).")
    parser.add_argument("--summary", type=Path, required=True,
                        help="Summary JSON (percentiles + environment).")
    parser.add_argument("--image-out", type=Path, required=True,
                        help="Generated 1920x1080 benchmark PNG.")
    parser.add_argument("--runs", type=int, default=DEFAULT_RUNS)
    parser.add_argument("--warmup", type=int, default=DEFAULT_WARMUP)
    args = parser.parse_args(argv)

    font = load_font(REPO_ROOT / "tests" / "fixtures" / "s0" / "fonts" / FONT_FILE_NAME)
    png, sha256 = render_perf_image(font)
    args.image_out.parent.mkdir(parents=True, exist_ok=True)
    args.image_out.write_bytes(png)
    expected_text = "\n".join(PERF_LINES)
    image_b64 = base64.b64encode(png).decode("ascii")
    print(f"benchmark image: {args.image_out} "
          f"{CANVAS_WIDTH}x{CANVAS_HEIGHT} sha256={sha256}")
    print(f"expected text: {expected_text!r}")

    # One adapter for the whole run (the process-wide singleton the API
    # uses); warm-up loads the models before any timed run.
    adapter = RapidOCRAdapter()

    def one_run() -> tuple[float, str]:
        start = time.perf_counter()
        report = run_check(image_mime="image/png", image_base64=image_b64,
                           expected_text=expected_text, adapter=adapter)
        elapsed = time.perf_counter() - start
        return elapsed, str(report.get("verdict"))

    for i in range(args.warmup):
        elapsed, verdict = one_run()
        print(f"warmup {i + 1}/{args.warmup}: {elapsed:.3f}s verdict={verdict}")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    measurements: list[float] = []
    verdicts: list[str] = []
    with open(args.out, "w", encoding="utf-8") as fh:
        for i in range(args.runs):
            elapsed, verdict = one_run()
            measurements.append(elapsed)
            verdicts.append(verdict)
            fh.write(json.dumps({
                "run": i + 1,
                "warmup": False,
                "seconds": elapsed,
                "verdict": verdict,
                "image_sha256": sha256,
                "width": CANVAS_WIDTH,
                "height": CANVAS_HEIGHT,
            }, ensure_ascii=False) + "\n")
            print(f"run {i + 1}/{args.runs}: {elapsed:.3f}s verdict={verdict}")

    ordered = sorted(measurements)
    summary = {
        "seed": SEED,
        "image": {
            "path": str(args.image_out),
            "width": CANVAS_WIDTH,
            "height": CANVAS_HEIGHT,
            "sha256": sha256,
            "bytes": len(png),
            "lines": PERF_LINES,
            "font_size_px": FONT_SIZE_PX,
            "note": "NOT an S0 fixture; generated by this script only. "
                    "S0 manifest untouched.",
        },
        "runs": args.runs,
        "warmup_runs": args.warmup,
        "verdicts": sorted(set(verdicts)),
        "seconds": {
            "p50": percentile_sorted(ordered, 50),
            "p95": percentile_sorted(ordered, 95),
            "mean": sum(measurements) / len(measurements),
            "min": min(measurements),
            "max": max(measurements),
        },
        "threshold_s": P95_THRESHOLD_S,
        "pass": percentile_sorted(ordered, 95) <= P95_THRESHOLD_S,
        "environment": environment(),
    }
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    args.summary.write_text(json.dumps(summary, indent=2, ensure_ascii=False)
                            + "\n", encoding="utf-8")
    print(json.dumps(summary["seconds"], indent=2))
    print(f"P95 {summary['seconds']['p95']:.3f}s vs threshold "
          f"{P95_THRESHOLD_S}s -> {'PASS' if summary['pass'] else 'FAIL'}")
    return 0 if summary["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
