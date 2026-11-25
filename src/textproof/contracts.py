"""Frozen input contracts for TextProof (P033).

Single source of truth for the input limits frozen in
``PROJECT_BOOK.md`` §4.2 and the report coordinate basis frozen in §5.1.
No other module may redefine these limits: T002's loader, T004's core and
T005's fixtures must all import them from here, so a limit change fails
loudly in one place instead of drifting silently across modules.

Privacy (PROJECT_BOOK.md §4.2 / §9): nothing in this module carries a
file path, an EXIF blob, a user comment or GPS data.  ``ImageInput`` holds
only the validated image bytes plus oriented dimensions; the EXIF
orientation tag is the *only* EXIF value the loader ever reads, and the
decoded image handed downstream has all EXIF / text metadata stripped
(see :mod:`textproof.io.image_loader`).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha256
from typing import Final

# ---------------------------------------------------------------------------
# Frozen report identity (PROJECT_BOOK.md §5.1)
# ---------------------------------------------------------------------------

SCHEMA_ID: Final[str] = "textproof.report/v1"
COORDINATE_SYSTEM: Final[str] = "oriented_image_px_top_left"

# ---------------------------------------------------------------------------
# Frozen input limits (PROJECT_BOOK.md §4.2).  Do not relax.
# ---------------------------------------------------------------------------

#: Maximum accepted image file size: 25 MiB.
MAX_FILE_SIZE_BYTES: Final[int] = 25 * 1024 * 1024
#: Maximum accepted width or height, in pixels (after EXIF orientation).
MAX_DIMENSION_PX: Final[int] = 8192
#: Maximum accepted total pixel count.
MAX_PIXELS: Final[int] = 40_000_000
#: Maximum expected-text length, in Unicode code points.
MAX_EXPECTED_CODEPOINTS: Final[int] = 5_000
#: Maximum expected-text line count.
MAX_EXPECTED_LINES: Final[int] = 100

#: Accepted image formats (Pillow ``Image.format`` names).
ACCEPTED_FORMATS: Final[frozenset[str]] = frozenset({"PNG", "JPEG", "WEBP"})

#: MIME type per accepted format.
MIME_BY_FORMAT: Final[dict[str, str]] = {
    "PNG": "image/png",
    "JPEG": "image/jpeg",
    "WEBP": "image/webp",
}

# ---------------------------------------------------------------------------
# Unified error code (IMPLEMENTATION_PLAN.md T002 completion definition:
# "所有输入错误使用统一错误码").  Every input rejection raised by the
# loader carries exactly this code, whatever the underlying reason.
# The short ``reason`` string distinguishes cases for logs/tests; it is
# never a file path and never contains user text or EXIF content.
# ---------------------------------------------------------------------------

ERROR_CODE_INVALID_INPUT: Final[str] = "INVALID_INPUT"


class InvalidInputError(ValueError):
    """An input that fails the frozen §4.2 contract.

    Attributes:
        code: always :data:`ERROR_CODE_INVALID_INPUT`.
        reason: short machine-readable snake_case reason, e.g.
            ``"file_too_large"``, ``"animated_webp"``,
            ``"expected_text_too_long"``.  Contains no paths, no user
            text and no EXIF content.
    """

    def __init__(self, reason: str, message: str) -> None:
        self.code: str = ERROR_CODE_INVALID_INPUT
        self.reason: str = reason
        super().__init__(message)

    def __str__(self) -> str:  # keep logs free of anything but code+reason
        return f"{self.code}: {self.reason}"


def invalid_input(reason: str, message: str) -> InvalidInputError:
    """Build an :class:`InvalidInputError` (single construction point)."""
    return InvalidInputError(reason, message)


# ---------------------------------------------------------------------------
# Core interfaces (IMPLEMENTATION_PLAN.md §5.1)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ImageInput:
    """A validated, decoded image ready for OCR / comparison.

    Fields (per §5.1: bytes, MIME, width, height, oriented flag):

    * ``data``: the original validated input bytes.  This is the byte
      string whose SHA-256 goes into the report ``image.sha256`` field
      (PROJECT_BOOK.md §5.4); it is never re-encoded, so the hash is
      stable across runs.
    * ``mime``: ``image/png`` / ``image/jpeg`` / ``image/webp``.
    * ``format``: Pillow format name (``PNG`` / ``JPEG`` / ``WEBP``),
      as used by the report ``image.format`` field (§5.4).
    * ``width`` / ``height``: dimensions **after** EXIF orientation is
      applied.  All coordinates (§5.1 ``oriented_image_px_top_left``)
      use this oriented frame as their basis.
    * ``oriented``: ``True`` iff an EXIF orientation tag (values 2-8)
      was present and applied; ``False`` for orientation 1 / no EXIF.
    * ``pil_image``: the decoded, EXIF-transposed Pillow image with
      all EXIF / text metadata stripped (no UserComment, no GPS, no
      embedded paths).  Downstream stages (T003 OCR) consume pixels
      from here and must not re-apply orientation.

    ``data`` and ``pil_image`` are excluded from ``repr`` so logs can
    never leak image bytes or user content.
    """

    data: bytes = field(repr=False)
    mime: str
    format: str
    width: int
    height: int
    oriented: bool
    pil_image: object = field(repr=False)  # PIL.Image.Image, metadata-stripped

    def sha256_hex(self) -> str:
        """SHA-256 of the original input bytes (report ``image.sha256``)."""
        return sha256(self.data).hexdigest()

    def image_report_fields(self) -> dict[str, object]:
        """The ``image`` block of a ``textproof.report/v1`` report,
        minus ``sha256`` (callers add :meth:`sha256_hex`).

        Contains no path, no EXIF content and no user text.
        """
        return {
            "format": self.format,
            "width": self.width,
            "height": self.height,
            "coordinate_system": COORDINATE_SYSTEM,
        }


@dataclass(frozen=True)
class ExpectedTextInput:
    """A validated expected text (PROJECT_BOOK.md §4.2, FR-02).

    * ``raw``: the user's text exactly as supplied.
    * ``normalized_lines``: the text split into lines after unifying
      ``CRLF`` / ``CR`` to ``LF`` only.  Full §4.3 normalisation (NFC,
      full-width mapping, whitespace folding) is **T004's**
      ``core/normalize.py`` and is deliberately *not* done here, so
      there is exactly one owner of §4.3.
    * ``codepoint_count`` / ``line_count``: the frozen §4.2 counts
      (Python ``len`` == Unicode code points; line count == number of
      ``LF``-separated segments).

    ``raw`` and ``normalized_lines`` are excluded from ``repr`` so logs
    can never record user text (PROJECT_BOOK.md §9).
    """

    raw: str = field(repr=False)
    normalized_lines: tuple[str, ...] = field(repr=False)
    codepoint_count: int
    line_count: int
