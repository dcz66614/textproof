"""Make the ``src`` layout importable when running pytest directly.

The project package (``textproof``) is not installed into the venv; tests
run against the working-tree sources. This conftest inserts ``<root>/src``
at the front of ``sys.path`` so ``import textproof...`` resolves to the
checkout under test, whichever directory pytest is launched from.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))
