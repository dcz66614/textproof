"""Packaged OCR assets shipped inside the ``textproof`` wheel.

``textproof/assets/ocr/models/`` holds verbatim copies of the three
frozen ONNX models from ``assets/ocr/models/`` (same files, same
SHA-256 — see ``THIRD_PARTY_NOTICES.md`` §2 and the adapter's frozen
hashes).  They are shipped in the wheel as package data so an
installed ``textproof`` can run OCR with no source checkout: the
adapter resolves them when no checkout assets are visible
(see :func:`textproof.ocr.rapidocr_adapter.default_assets_dir`).

The recognition dictionary is deliberately NOT shipped here: its
licence is UNVERIFIED (``THIRD_PARTY_NOTICES.md`` §4), so it is
rebuilt locally into ``textproof/assets/ocr/dictionaries/`` by
``python -m textproof.setup_dictionary`` after install.  The
``dictionaries/`` directory exists so that rebuild has a stable
target; it ships empty.
"""

from __future__ import annotations
