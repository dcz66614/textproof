"""T010 offline static checks: the product's own dependency surface
and fixtures are local.

Honest note (do not over-claim): ``requests==2.34.2`` IS present in
``requirements.lock`` — as a transitive dependency of ``rapidocr``
(``# via rapidocr``), installed in the venv.  What this module
asserts is the narrower, true claim: TextProof's own declared
dependencies (``pyproject.toml``) include no HTTP client library,
and every S0 fixture, font and model asset the product needs is a
local file.  The runtime proof that nothing ever calls the network
is the socket interception (``tests/privacy/``) plus strace
(``test_strace.py``) plus the offline namespace runs — not the
absence of a library from the lockfile.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from t010_offline_helpers import FIXTURES, MANIFEST, REPO_ROOT


def test_no_network_client_in_declared_dependencies():
    text = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    deps = re.search(r"dependencies = \[(.*?)\]", text, re.DOTALL)
    assert deps is not None
    for client in ("requests", "httpx", "aiohttp", "urllib3"):
        assert f'"{client}' not in deps.group(1), (
            f"declared dependency on network client {client!r}")


def test_requests_in_lock_is_transitive_only():
    """requests exists in the lock only as rapidocr's transitive dep."""
    lock = (REPO_ROOT / "requirements.lock").read_text(encoding="utf-8")
    assert "requests==2.34.2" in lock
    assert "# via rapidocr" in lock
    assert "httpx" not in lock, "httpx must not be in the frozen lock"
    assert "aiohttp" not in lock, "aiohttp must not be in the frozen lock"


def test_all_s0_fixtures_present_locally():
    missing = []
    for record in MANIFEST["fixtures"]:
        path = FIXTURES / record["filename"]
        if not path.is_file() or path.stat().st_size == 0:
            missing.append(record["id"])
    assert not missing, f"S0 fixtures missing locally: {missing[:5]}"
    assert len(MANIFEST["fixtures"]) == 300
    for name in ("manifest.json", "expected_output.json",
                 "blind_subset.json"):
        assert (FIXTURES / name).is_file()
    assert (FIXTURES / "fonts" / "NotoSansSC[wght].ttf").is_file()


def test_model_assets_present_locally():
    assets = REPO_ROOT / "assets" / "ocr"
    for rel in ("models/PP-OCRv6_det_small.onnx",
                "models/PP-OCRv6_rec_small.onnx",
                "models/ch_ppocr_mobile_v2.0_cls_mobile.onnx",
                "dictionaries/ppocrv6_dict.txt",
                "SHA256SUMS.txt"):
        assert (assets / rel).is_file(), f"missing local asset: {rel}"
