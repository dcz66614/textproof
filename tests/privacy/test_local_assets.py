"""T010 acceptance 2: OCR model, dictionary, JS, CSS and fonts are local.

* Model + dictionary: the three ONNX files and the recognition
  dictionary live under ``assets/ocr/`` and their SHA-256 values
  equal the frozen constants in
  :mod:`textproof.ocr.rapidocr_adapter`; the adapter is constructed
  with explicit local paths, so RapidOCR never takes its download
  path at runtime (T003 verified the same hashes; this re-checks
  them from the privacy side).
* UI: ``index.html`` / ``app.js`` / ``style.css`` contain no
  external reference (same pattern set as T008's static tests),
  no remote ``@font-face``, and only a local system font stack.
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

from t010_privacy_helpers import REPO_ROOT

from textproof.api.routes import get_ocr_adapter
from textproof.ocr.rapidocr_adapter import (
    CLS_MODEL,
    DET_MODEL,
    DICT_FILE,
    MODEL_FILES,
    REC_MODEL,
)

UI_DIR = REPO_ROOT / "src" / "textproof" / "ui"
ASSETS_OCR = REPO_ROOT / "assets" / "ocr"

EXTERNAL_PATTERNS = [
    re.compile(r"https?://", re.IGNORECASE),
    re.compile(r"(?<![\w:])//[A-Za-z0-9][\w.-]*\.[a-z]{2,}", re.IGNORECASE),
    re.compile(r"@import", re.IGNORECASE),
    re.compile(r"url\(\s*[\"']?https?:", re.IGNORECASE),
    re.compile(r"(?:src|href)\s*=\s*[\"']https?:", re.IGNORECASE),
    re.compile(r"fonts\.googleapis|googleapis\.com|gstatic\.com",
               re.IGNORECASE),
    re.compile(r"\bcdn\b", re.IGNORECASE),
    re.compile(r"unpkg\.com|jsdelivr\.net|cdnjs\.cloudflare\.com",
               re.IGNORECASE),
]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def test_model_files_are_local_with_frozen_hashes():
    """All three ONNX models + dict: local files, frozen SHA-256."""
    checked = []
    for name, _url, sha256, _key in MODEL_FILES:
        path = ASSETS_OCR / "models" / name
        assert path.is_file(), f"missing local model file: {path}"
        assert _sha256(path) == sha256, (
            f"model hash mismatch (tampered or replaced?): {name}")
        assert path.stat().st_size > 0
        checked.append(name)
    dict_path = ASSETS_OCR / "dictionaries" / DICT_FILE[0]
    assert dict_path.is_file(), f"missing local dictionary: {dict_path}"
    assert _sha256(dict_path) == DICT_FILE[2]
    assert len(dict_path.read_text(encoding="utf-8").splitlines()) \
        == DICT_FILE[3]
    assert checked == [DET_MODEL[0], REC_MODEL[0], CLS_MODEL[0]]


def test_adapter_uses_local_assets_and_cpu_only():
    """The running engine: local model files, CPU provider only."""
    adapter = get_ocr_adapter()
    assert adapter.assets_dir == ASSETS_OCR, (
        f"adapter assets dir is not the local repo dir: "
        f"{adapter.assets_dir}")
    for name, s in adapter.providers.items():
        assert s == ["CPUExecutionProvider"], (
            f"provider for {name} is not CPU-only: {s}")
    info = adapter.model_info
    for key in ("det", "rec", "cls"):
        assert info[key]["sha256"] in (
            DET_MODEL[2], REC_MODEL[2], CLS_MODEL[2])
    assert info["dict"]["sha256"] == DICT_FILE[2]
    assert info["rapidocr_version"] == "3.10.0"
    assert info["onnxruntime_version"] == "1.32.0"


def test_ui_files_have_no_external_references():
    for name in ("index.html", "app.js", "style.css"):
        text = (UI_DIR / name).read_text(encoding="utf-8")
        hits = [pat.pattern for pat in EXTERNAL_PATTERNS if pat.search(text)]
        assert not hits, f"{name} contains external-reference(s): {hits}"


def test_ui_uses_only_local_system_fonts():
    """No remote @font-face; the font stack is local system fonts."""
    css = (UI_DIR / "style.css").read_text(encoding="utf-8")
    assert "@font-face" not in css, "remote font loading in style.css"
    assert "system-ui" in css, "font stack is not the local system stack"
    assert "url(" not in css, "style.css references an external URL"


def test_ui_calls_only_same_origin_api():
    js = (UI_DIR / "app.js").read_text(encoding="utf-8")
    urls = dict(re.findall(
        r"var (CHECK_URL|VERSION_URL) = \"([^\"]+)\";", js))
    assert urls.get("CHECK_URL") == "/api/v1/check"
    assert urls.get("VERSION_URL") == "/api/v1/version"
    for call in re.findall(r"fetch\(\s*([A-Za-z_]+)\s*,", js):
        assert call in urls, f"fetch() with unknown target: {call}"
    assert "127.0.0.1" not in js
    assert "localhost" not in js


def test_ui_never_names_browser_storage():
    """Static half of acceptance 3: no storage API in the UI source."""
    for name in ("index.html", "app.js", "style.css"):
        text = (UI_DIR / name).read_text(encoding="utf-8")
        for token in ("localStorage", "sessionStorage", "indexedDB",
                      "document.cookie"):
            assert token not in text, f"{name} mentions {token}"
