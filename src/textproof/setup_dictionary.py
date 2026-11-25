"""Rebuild the PP-OCRv6 recognition dictionary from local model metadata.

This is the in-package home of the dictionary rebuild (T013-U01).
It used to live only in ``scripts/setup_dictionary.py``; that script
is now a thin wrapper around this module, so the rebuild works after
a wheel install too, where there is no ``scripts/`` directory::

    python -m textproof.setup_dictionary          # rebuild if missing
    python -m textproof.setup_dictionary --check  # verify only

Why this module exists (T014, review finding R-03)
---------------------------------------------------
The recognition dictionary ``ppocrv6_dict.txt`` (18,708 lines,
SHA-256 ``b5f2bfe2...``) has no dictionary-specific licence
statement: the file itself carries no licence header, and the RapidOCR
model licence notice expressly excludes recognition dictionaries from its
Apache-2.0 declaration. The dictionary is therefore NOT redistributed as
a separate file in any public snapshot of this repository
(see ``THIRD_PARTY_NOTICES.md`` section 4 and the packaging exclusion
list there). This module recreates it on the user's own machine, from
data the user already holds locally: the character list embedded in
the locally shipped ``PP-OCRv6_rec_small.onnx`` model file.

Where the dictionary is written
--------------------------------
Into the assets directory resolved by
:func:`textproof.ocr.rapidocr_adapter.default_assets_dir`: the
checkout ``<repo>/assets/ocr`` in a source tree, or the packaged
``<package>/assets/ocr`` in an installed wheel (the models ship in
the wheel; the dictionary is rebuilt next to them).  Pass
``--assets-dir`` to target a different directory explicitly, or set
``TEXTPROOF_ASSETS_DIR``.

How the rebuild works
---------------------
The PP-OCRv6 recognition model ``PP-OCRv6_rec_small.onnx`` -- itself an
Apache-2.0 model artifact shipped with the package -- embeds the
very same character list in its ``character`` model metadata. The adapter
already cross-checks the dictionary file against that embedded list on
every start-up. This module performs the reverse step, once, at install
time: it reads the embedded list from the local model file and writes it
out as the dictionary file, then verifies the result byte-for-byte
(SHA-256 and line count) against the frozen values below.

What this module never does
---------------------------
- It reads only two files already present on the local disk (the model
  file and, for the idempotence check, the dictionary file itself).
- It opens no remote location, fetches nothing, and needs no
  credentials. The model file is verified by SHA-256 *before* its
  metadata is trusted, so a substituted model cannot silently yield a
  wrong dictionary.
- It never overwrites an existing dictionary whose contents differ from
  the frozen value unless ``--force`` is given explicitly: a differing
  local file is reported as an error and left untouched, so tampering
  stays visible instead of being silently papered over.

Exit codes: 0 = dictionary present and verified; 2 = the model file is
missing or its hash does not match the frozen value; 3 = a differing
dictionary already exists and ``--force`` was not given; 4 = the rebuilt
file failed its own verification (the partial file is removed).
"""

from __future__ import annotations

import argparse
import hashlib
import os
import sys
from pathlib import Path

# Telemetry opt-out, set before the inference engine is imported, mirroring
# src/textproof/ocr/rapidocr_adapter.py (PROJECT_BOOK.md section 9).
os.environ["ORT_DISABLE_TELEMETRY"] = "1"

from textproof.ocr.rapidocr_adapter import (  # noqa: E402
    DICT_FILE,
    REC_MODEL,
    default_assets_dir,
)

# Frozen values (PROJECT_BOOK.md section 6.2; THIRD_PARTY_NOTICES.md
# section 4). Single source of truth: the adapter's frozen tuples.
# The model hash is the RapidOCR registry value for
# multi_PP-OCRv6_rec_small; the dictionary hash and line count are the
# T003-verified values for ppocrv6_dict.txt.
REC_MODEL_NAME = REC_MODEL[0]
REC_MODEL_SHA256 = REC_MODEL[2]
DICT_NAME = DICT_FILE[0]
DICT_SHA256 = DICT_FILE[2]
DICT_LINES = DICT_FILE[3]

__all__ = [
    "REC_MODEL_NAME",
    "REC_MODEL_SHA256",
    "DICT_NAME",
    "DICT_SHA256",
    "DICT_LINES",
    "rebuild",
    "check_only",
    "main",
]


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _assets_dir(explicit: Path | None) -> Path:
    if explicit is not None:
        return explicit.resolve()
    return default_assets_dir()


def _embedded_characters(model_path: Path) -> list[str]:
    """Read the ``character`` list embedded in the local rec model file."""
    import onnxruntime as ort

    session = ort.InferenceSession(
        str(model_path), providers=["CPUExecutionProvider"]
    )
    meta = session.get_modelmeta().custom_metadata_map
    if "character" not in meta:
        raise ValueError(
            "Recognition model carries no embedded 'character' metadata; "
            "cannot rebuild the dictionary."
        )
    chars = meta["character"].splitlines()
    if len(chars) != DICT_LINES:
        raise ValueError(
            f"Embedded character list has {len(chars)} lines, "
            f"expected {DICT_LINES}."
        )
    if any(not line or "\r" in line for line in chars):
        raise ValueError(
            "Embedded character list contains an empty line or a "
            "carriage return; refusing to write the dictionary."
        )
    return chars


def _check_dictionary(dict_path: Path) -> bool:
    """True when the dictionary file exists and matches the frozen value."""
    if not dict_path.is_file():
        return False
    if _sha256_file(dict_path) != DICT_SHA256:
        return False
    lines = dict_path.read_text(encoding="utf-8").splitlines()
    return len(lines) == DICT_LINES


def rebuild(assets_dir: Path, *, force: bool) -> int:
    """Rebuild the dictionary from the local model file. Returns exit code."""
    model_path = assets_dir / "models" / REC_MODEL_NAME
    dict_path = assets_dir / "dictionaries" / DICT_NAME
    rel_model = model_path.relative_to(assets_dir)
    rel_dict = dict_path.relative_to(assets_dir)

    if not model_path.is_file():
        print(f"error: model file missing: {rel_model}", file=sys.stderr)
        print(
            "The recognition model is part of the shipped assets; "
            "re-fetch it from the frozen registry source before "
            "rebuilding the dictionary.",
            file=sys.stderr,
        )
        return 2
    if _sha256_file(model_path) != REC_MODEL_SHA256:
        print(
            f"error: model file hash mismatch: {rel_model}\n"
            f"  expected: {REC_MODEL_SHA256}",
            file=sys.stderr,
        )
        print(
            "Refusing to rebuild from an unverified model file.",
            file=sys.stderr,
        )
        return 2

    if dict_path.is_file() and not _check_dictionary(dict_path):
        if not force:
            print(
                f"error: existing dictionary differs from the frozen "
                f"value: {rel_dict}",
                file=sys.stderr,
            )
            print(
                "Remove it by hand, or re-run with --force to replace "
                "it with the rebuilt file.",
                file=sys.stderr,
            )
            return 3
        print(f"warning: replacing differing dictionary: {rel_dict}")

    if _check_dictionary(dict_path):
        print(f"dictionary already present and verified: {rel_dict}")
        print(f"  sha256: {DICT_SHA256}")
        print(f"  lines:  {DICT_LINES}")
        return 0

    chars = _embedded_characters(model_path)
    content = "\n".join(chars) + "\n"
    dict_path.parent.mkdir(parents=True, exist_ok=True)
    dict_path.write_text(content, encoding="utf-8", newline="\n")

    if not _check_dictionary(dict_path):
        try:
            dict_path.unlink()
        except OSError:
            pass
        print(
            "error: rebuilt dictionary failed verification; "
            "partial file removed.",
            file=sys.stderr,
        )
        return 4

    print(f"rebuilt dictionary: {rel_dict}")
    print(f"  source: {rel_model} (embedded character metadata)")
    print(f"  sha256: {DICT_SHA256}")
    print(f"  lines:  {DICT_LINES}")
    return 0


def check_only(assets_dir: Path) -> int:
    """Verify the dictionary without writing anything. Returns exit code."""
    dict_path = assets_dir / "dictionaries" / DICT_NAME
    rel_dict = dict_path.relative_to(assets_dir)
    if not dict_path.is_file():
        print(f"missing: {rel_dict}", file=sys.stderr)
        print(
            "Run without --check to rebuild it from the local model file.",
            file=sys.stderr,
        )
        return 2
    if _check_dictionary(dict_path):
        print(f"dictionary verified: {rel_dict}")
        print(f"  sha256: {DICT_SHA256}")
        print(f"  lines:  {DICT_LINES}")
        return 0
    print(f"error: dictionary differs from the frozen value: {rel_dict}",
          file=sys.stderr)
    return 3


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Rebuild ppocrv6_dict.txt from the character list embedded "
            "in the locally shipped PP-OCRv6_rec_small.onnx model file. "
            "Local files only."
        )
    )
    parser.add_argument(
        "--assets-dir",
        type=Path,
        default=None,
        help="assets/ocr directory (default: resolved the same way the "
        "OCR adapter resolves it: TEXTPROOF_ASSETS_DIR, checkout assets, "
        "then packaged assets)",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="verify the dictionary only; write nothing",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="replace an existing dictionary whose contents differ",
    )
    args = parser.parse_args(argv)
    assets_dir = _assets_dir(args.assets_dir)
    if args.check:
        return check_only(assets_dir)
    return rebuild(assets_dir, force=args.force)


if __name__ == "__main__":
    raise SystemExit(main())
