"""Validate a ``textproof.report/v1`` report against PROJECT_BOOK.md §5.

Thin wrapper (T013-U01): the implementation lives in
``textproof.core.report_schema`` so the installed wheel can validate
its own reports without a source checkout.  This script only
re-exports the validator and its file-checking CLI, so the historical
entry point keeps working exactly as before::

    python scripts/validate_report_schema.py report.json [report2.json ...]
    python scripts/validate_report_schema.py --reports-dir dir/

Exit code 0 iff every report is valid; every violation is printed
with its JSON path.  See ``src/textproof/core/report_schema.py`` for
the rules (one §5 clause each) and the frozen T009/T013 notes.
"""

from __future__ import annotations

import sys
from pathlib import Path

try:
    from textproof.core.report_schema import (
        COORDINATE_SYSTEM,
        ERROR_TYPES,
        IMAGE_FORMATS,
        SCHEMA_ID,
        TOP_LEVEL_KEYS,
        VERDICTS,
        WARNING_CODES,
        main,
        validate_report,
    )
except ImportError:  # pragma: no cover - checkout without src on path
    # Running the script directly from a checkout
    # (``python scripts/validate_report_schema.py ...``) puts only
    # ``scripts/`` on ``sys.path``; the package lives in ``src/`` next
    # to it.  Add that directory and retry once.
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
    from textproof.core.report_schema import (
        COORDINATE_SYSTEM,
        ERROR_TYPES,
        IMAGE_FORMATS,
        SCHEMA_ID,
        TOP_LEVEL_KEYS,
        VERDICTS,
        WARNING_CODES,
        main,
        validate_report,
    )

__all__ = [
    "COORDINATE_SYSTEM",
    "ERROR_TYPES",
    "IMAGE_FORMATS",
    "SCHEMA_ID",
    "TOP_LEVEL_KEYS",
    "VERDICTS",
    "WARNING_CODES",
    "main",
    "validate_report",
]


if __name__ == "__main__":
    raise SystemExit(main())
