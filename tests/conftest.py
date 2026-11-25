"""Make the ``src/`` layout importable without an installed package.

T002's tests run against the worktree source directly
(``.venv/bin/python -m pytest tests/unit/test_image_loader.py``);
the package is not installed into the shared venv, so ``src`` is put
on ``sys.path`` here.  This conftest ships with the repo so the
acceptance command works from a clean checkout.
"""

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))
