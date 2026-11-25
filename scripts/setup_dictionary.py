"""Rebuild the PP-OCRv6 recognition dictionary from local model metadata.

Thin wrapper (T013-U01): the implementation lives in
``textproof.setup_dictionary`` so the rebuild works after a wheel
install too, where there is no ``scripts/`` directory.  This script
only resolves the checkout assets directory from ``--root`` and
delegates to that module, so the historical entry point keeps working
exactly as before::

    .venv/bin/python scripts/setup_dictionary.py          # rebuild if missing
    .venv/bin/python scripts/setup_dictionary.py --check  # verify only

After a wheel install, run the same rebuild as a module instead::

    python -m textproof.setup_dictionary

Why the rebuild exists (T014, review finding R-03): the recognition
dictionary ``ppocrv6_dict.txt`` (18,708 lines, SHA-256 ``b5f2bfe2...``)
has no dictionary-specific licence statement, so it is NOT
redistributed as a separate file in any public snapshot (see
``THIRD_PARTY_NOTICES.md`` section 4).  It is recreated on the user's
own machine from the character list embedded in the locally shipped
``PP-OCRv6_rec_small.onnx`` model file, then verified byte-for-byte
against the frozen hash and line count.  The rebuild reads only local
files, opens no remote location, and never overwrites a differing
local dictionary unless ``--force`` is given.

Exit codes: 0 = dictionary present and verified; 2 = the model file is
missing or its hash does not match the frozen value; 3 = a differing
dictionary already exists and ``--force`` was not given; 4 = the rebuilt
file failed its own verification (the partial file is removed).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

try:
    from textproof.setup_dictionary import check_only, rebuild
except ImportError:  # pragma: no cover - checkout without src on path
    # Running the script directly from a checkout
    # (``python scripts/setup_dictionary.py``) puts only ``scripts/``
    # on ``sys.path``; the package lives in ``src/`` next to it.
    # Add that directory and retry once.
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
    from textproof.setup_dictionary import check_only, rebuild


def _repo_root(explicit: Path | None) -> Path:
    if explicit is not None:
        return explicit.resolve()
    return Path(__file__).resolve().parents[1]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Rebuild assets/ocr/dictionaries/ppocrv6_dict.txt from the "
            "character list embedded in the locally shipped "
            "PP-OCRv6_rec_small.onnx model file. Local files only."
        )
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=None,
        help="repository root (default: parent of the scripts/ directory)",
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
    assets_dir = _repo_root(args.root) / "assets" / "ocr"
    if args.check:
        return check_only(assets_dir)
    return rebuild(assets_dir, force=args.force)


if __name__ == "__main__":
    raise SystemExit(main())
