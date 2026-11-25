"""Fixture for the T010 offline tests (PROJECT_BOOK.md §9).

Helpers live in :mod:`t010_offline_helpers`; this module only wires
the ``unshare_available`` fixture pytest injects by name.
"""

from __future__ import annotations

import subprocess

import pytest

from t010_offline_helpers import UNSHARE


@pytest.fixture(scope="module")
def unshare_available():
    if UNSHARE is None:
        pytest.skip("unshare(1) is not installed")
    probe = subprocess.run(
        [UNSHARE, "-n", "true"], capture_output=True, timeout=30)
    if probe.returncode != 0:
        pytest.skip(
            f"unshare -n cannot create a network namespace "
            f"(rc={probe.returncode}): {probe.stderr.decode()[:200]}")
