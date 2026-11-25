"""Integration tests for the T003 RapidOCR CPU offline adapter.

All test images are synthetic, generated in-memory with Pillow (white
background, black text). No real user images, no web images, no network.
The Chinese test uses the system Noto Sans CJK SC font when present and is
skipped otherwise; the English/digits tests use DejaVu Sans (always present
on this VM) and always run.
"""

from __future__ import annotations

import hashlib
import importlib.metadata as md
import io
import shutil
import tempfile
from pathlib import Path

import numpy as np
import pytest
from PIL import Image, ImageDraw, ImageFont

from textproof.ocr.rapidocr_adapter import (
    ALLOWED_PROVIDERS,
    CLS_MODEL,
    DET_MODEL,
    DICT_FILE,
    OCRAdapterError,
    ONNXRUNTIME_VERSION,
    RAPIDOCR_VERSION,
    REC_MODEL,
    RapidOCRAdapter,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
ASSETS_DIR = REPO_ROOT / "assets" / "ocr"

CJK_FONT = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
LATIN_FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"


def _render(lines, font_path, size=(1200, 480), font_size=64):
    img = Image.new("RGB", size, "white")
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype(font_path, font_size)
    y = 60
    for text in lines:
        draw.text((60, y), text, fill="black", font=font)
        y += 110
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue(), img.size


@pytest.fixture(scope="module")
def adapter():
    return RapidOCRAdapter(assets_dir=ASSETS_DIR)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


# --- acceptance 1: exact frozen versions -------------------------------

def test_rapidocr_exact_version():
    assert md.version("rapidocr") == RAPIDOCR_VERSION == "3.10.0"


def test_onnxruntime_exact_version_cpu_package():
    assert md.version("onnxruntime") == ONNXRUNTIME_VERSION == "1.32.0"
    # The GPU package must not be installed (T001 lock has no such entry).
    with pytest.raises(md.PackageNotFoundError):
        md.version("onnxruntime-gpu")


# --- acceptance 2/3: frozen route, local assets, hashes ----------------

def test_model_assets_present_and_hashes_match_registry():
    for filename, _url, sha256, _key in (DET_MODEL, REC_MODEL, CLS_MODEL):
        path = ASSETS_DIR / "models" / filename
        assert path.is_file(), f"missing model asset: {path}"
        assert _sha256(path) == sha256


def test_assets_sha256sums_file_matches():
    sums_file = ASSETS_DIR / "SHA256SUMS.txt"
    assert sums_file.is_file()
    recorded = {}
    for line in sums_file.read_text(encoding="utf-8").splitlines():
        digest, rel = line.split(None, 1)
        recorded[rel.strip()] = digest
    for filename, _url, sha256, _key in (DET_MODEL, REC_MODEL, CLS_MODEL):
        rel = f"models/{filename}"
        assert recorded.get(rel) == sha256, rel
    assert recorded.get(f"dictionaries/{DICT_FILE[0]}") == DICT_FILE[2]


def test_dictionary_asset_present_and_matches_embedded_list(adapter):
    dict_path = ASSETS_DIR / "dictionaries" / DICT_FILE[0]
    assert dict_path.is_file()
    assert _sha256(dict_path) == DICT_FILE[2]
    lines = dict_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == DICT_FILE[3] == 18708
    # The adapter already cross-checked this file against the character list
    # embedded in the recognition model at start-up; re-check the invariant
    # through the same code path used in production.
    embedded = adapter._embedded_characters()
    assert lines == embedded


def test_frozen_model_route_recorded():
    assert DET_MODEL[3] == "multi_PP-OCRv6_det_small"
    assert REC_MODEL[3] == "multi_PP-OCRv6_rec_small"
    assert CLS_MODEL[3] == "ch_ppocr_mobile_v2.0_cls_mobile"
    info = RapidOCRAdapter(assets_dir=ASSETS_DIR).model_info
    assert info["det"]["model_key"] == "multi_PP-OCRv6_det_small"
    assert info["rec"]["model_key"] == "multi_PP-OCRv6_rec_small"
    assert info["cls"]["model_key"] == "ch_ppocr_mobile_v2.0_cls_mobile"


# --- acceptance 4: fail-closed, no download on start-up ---------------

def test_missing_model_asset_fails_closed_without_download():
    with tempfile.TemporaryDirectory() as tmp:
        copied = Path(tmp) / "ocr"
        shutil.copytree(ASSETS_DIR, copied)
        (copied / "models" / REC_MODEL[0]).unlink()
        with pytest.raises(FileNotFoundError, match="missing"):
            RapidOCRAdapter(assets_dir=copied)


def test_tampered_model_asset_fails_closed():
    with tempfile.TemporaryDirectory() as tmp:
        copied = Path(tmp) / "ocr"
        shutil.copytree(ASSETS_DIR, copied)
        target = copied / "models" / DET_MODEL[0]
        with open(target, "r+b") as fh:
            fh.seek(100)
            fh.write(b"\x00")
        with pytest.raises(ValueError, match="hash mismatch"):
            RapidOCRAdapter(assets_dir=copied)


def test_missing_dictionary_fails_closed():
    with tempfile.TemporaryDirectory() as tmp:
        copied = Path(tmp) / "ocr"
        shutil.copytree(ASSETS_DIR, copied)
        (copied / "dictionaries" / DICT_FILE[0]).unlink()
        with pytest.raises(FileNotFoundError, match="dictionary"):
            RapidOCRAdapter(assets_dir=copied)


# --- acceptance 5: CPU-only provider -----------------------------------

def test_onnx_providers_are_cpu_only(adapter):
    providers = adapter.providers
    assert set(providers) == {"det", "cls", "rec"}
    for name, eps in providers.items():
        assert eps == list(ALLOWED_PROVIDERS) == ["CPUExecutionProvider"], name
        assert "CUDAExecutionProvider" not in eps
        assert "DmlExecutionProvider" not in eps
        assert "TensorrtExecutionProvider" not in eps


def test_no_gpu_provider_available_in_runtime():
    import onnxruntime as ort

    assert "CUDAExecutionProvider" not in ort.get_available_providers()
    assert ort.get_device() == "CPU"


# --- acceptance 6: return structure ------------------------------------

def _check_line_shape(lines, width, height):
    assert lines, "expected at least one OCR line"
    for i, line in enumerate(lines):
        assert line.line_index == i
        assert line.source_order == i
        assert isinstance(line.text, str) and line.text.strip()
        assert 0.0 <= line.confidence <= 1.0
        x0, y0, x1, y1 = line.bbox_xyxy
        assert 0 <= x0 < x1 <= width
        assert 0 <= y0 < y1 <= height
        assert line.bbox == line.bbox_xyxy
        assert len(line.quad) == 4
        for px, py in line.quad:
            assert 0 <= px <= width and 0 <= py <= height


def test_recognize_english_and_digits(adapter):
    png, (w, h) = _render(["Hello World 123"], LATIN_FONT)
    lines = adapter.recognize(png)
    _check_line_shape(lines, w, h)
    assert " ".join(line.text for line in lines) == "Hello World 123"
    assert lines[0].confidence > 0.9


def test_recognize_chinese(adapter):
    if not Path(CJK_FONT).is_file():
        pytest.skip("Noto Sans CJK SC not installed on this machine")
    png, (w, h) = _render(["限时优惠"], CJK_FONT)
    lines = adapter.recognize(png)
    _check_line_shape(lines, w, h)
    assert "".join(line.text for line in lines) == "限时优惠"
    assert lines[0].confidence > 0.9


def test_recognize_numeric_price(adapter):
    if not Path(CJK_FONT).is_file():
        pytest.skip("Noto Sans CJK SC not installed on this machine")
    png, (w, h) = _render(["￥28.80"], CJK_FONT)
    lines = adapter.recognize(png)
    _check_line_shape(lines, w, h)
    # The model emits U+00A5 YEN SIGN for the drawn U+FFE5 fullwidth yen;
    # the digits are the load-bearing part for this adapter-level check
    # (fullwidth normalisation is T004's job, PROJECT_BOOK.md §4.3).
    assert "28.80" in "".join(line.text for line in lines)


def test_recognize_two_lines_keeps_source_order(adapter):
    png, (w, h) = _render(["Hello World", "Goodbye 42"], LATIN_FONT)
    lines = adapter.recognize(png)
    _check_line_shape(lines, w, h)
    assert len(lines) == 2
    assert [line.text for line in lines] == ["Hello World", "Goodbye 42"]
    assert [line.source_order for line in lines] == [0, 1]


def test_recognize_accepts_ndarray_and_pil_image(adapter):
    png, (w, h) = _render(["Hello World 123"], LATIN_FONT)
    from_bytes = adapter.recognize(png)
    array = np.asarray(Image.open(io.BytesIO(png)).convert("RGB"))
    from_array = adapter.recognize(array)
    from_pil = adapter.recognize(Image.open(io.BytesIO(png)))
    assert [l.text for l in from_array] == [l.text for l in from_bytes]
    assert [l.text for l in from_pil] == [l.text for l in from_bytes]


def test_blank_image_returns_no_lines(adapter):
    img = Image.new("RGB", (1200, 480), "white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    assert adapter.recognize(buf.getvalue()) == []


def test_invalid_input_raises(adapter):
    with pytest.raises(ValueError):
        adapter.recognize(b"")
    with pytest.raises(ValueError):
        adapter.recognize(b"this is not an image")
    with pytest.raises(TypeError):
        adapter.recognize(12345)  # type: ignore[arg-type]


def test_repeat_recognition_is_deterministic(adapter):
    png, _ = _render(["Hello World 123"], LATIN_FONT)
    first = adapter.recognize(png)
    second = adapter.recognize(png)
    assert [(l.text, l.confidence, l.bbox_xyxy, l.quad) for l in first] == [
        (l.text, l.confidence, l.bbox_xyxy, l.quad) for l in second
    ]
