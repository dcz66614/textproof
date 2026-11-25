"""Image loading and input validation (T002).

Implements ``PROJECT_BOOK.md`` §4.2:

* only PNG / JPEG / WebP, checked by **magic bytes**, never by file
  extension (this module takes ``bytes`` only -- it has no path
  parameter at all, so there is no arbitrary-path read or write);
* 25 MiB / 8192 px / 40,000,000 px limits, checked on the image header
  *before* full decode so an oversized file cannot force a large
  allocation (decompression-bomb defence);
* animated WebP, corrupt/truncated files, magic/format mismatches and
  decode errors all fail closed with the unified ``INVALID_INPUT`` code;
* EXIF orientation is applied; width/height and every coordinate use
  the oriented frame (``oriented_image_px_top_left``, §5.1);
* expected text: at most 5,000 Unicode code points, at most 100 lines,
  blank input rejected.

Privacy (§4.2 / §9): the loader reads exactly one EXIF value -- the
orientation tag (274).  EXIF UserComment (0x9286), GPS tags (0x8825)
and PNG text chunks are never read, never copied and never returned:
the decoded image handed downstream is stripped of all EXIF / text
metadata.  No error message contains a path, user text or EXIF content.
"""

from __future__ import annotations

from io import BytesIO

from PIL import Image, ImageOps

from textproof.contracts import (
    ACCEPTED_FORMATS,
    ERROR_CODE_INVALID_INPUT,
    MAX_DIMENSION_PX,
    MAX_EXPECTED_CODEPOINTS,
    MAX_EXPECTED_LINES,
    MAX_FILE_SIZE_BYTES,
    MAX_PIXELS,
    MIME_BY_FORMAT,
    ExpectedTextInput,
    ImageInput,
    InvalidInputError,
    invalid_input,
)

__all__ = [
    "ERROR_CODE_INVALID_INPUT",
    "InvalidInputError",
    "detect_format",
    "load_image",
    "validate_expected_text",
]

# Defence in depth: Pillow itself must refuse absurd pixel counts even if
# a caller bypasses the header check below.  The explicit header check
# remains primary (it runs before any decode).
Image.MAX_IMAGE_PIXELS = MAX_PIXELS

_EXIF_ORIENTATION_TAG = 274  # the only EXIF tag this module ever reads

# Magic-byte prefixes (PROJECT_BOOK.md §4.2 / §9: never trust extension).
_PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
_JPEG_MAGIC = b"\xff\xd8\xff"
_RIFF_MAGIC = b"RIFF"
_WEBP_MARKER = b"WEBP"

# Metadata keys that are safe to keep on the decoded image (colour /
# resolution hints).  Everything else in ``Image.info`` -- EXIF blob,
# PNG text chunks, comments -- is dropped.
_SAFE_INFO_KEYS = frozenset({"icc_profile", "dpi"})


def detect_format(data: bytes) -> str | None:
    """Sniff the image format from magic bytes only.

    Returns ``"PNG"`` / ``"JPEG"`` / ``"WEBP"``, or ``None`` when the
    bytes match no accepted format.  Never looks at a file name: the
    loader has no file-name input at all.
    """
    if data.startswith(_PNG_MAGIC):
        return "PNG"
    if data.startswith(_JPEG_MAGIC):
        return "JPEG"
    if (
        len(data) >= 12
        and data[:4] == _RIFF_MAGIC
        and data[8:12] == _WEBP_MARKER
    ):
        return "WEBP"
    return None


def _webp_has_animation_flag(data: bytes) -> bool:
    """True iff a WebP VP8X extended chunk carries the animation bit.

    VP8X layout: ``"VP8X"`` + 4-byte chunk size + 1 flag byte whose
    bit ``0x02`` marks an animated image.  A static (lossy / lossless)
    WebP has no VP8X chunk at all, or a VP8X chunk without that bit.
    This raw-byte check catches animated files even if a decoder
    reports only one frame.
    """
    idx = data.find(b"VP8X", 0, 32)
    if idx < 0 or len(data) < idx + 9:
        return False
    return bool(data[idx + 8] & 0x02)


def _strip_private_metadata(image: Image.Image) -> Image.Image:
    """Return a copy of *image* with all EXIF / text metadata removed.

    Keeps only colour/resolution hints (``icc_profile``, ``dpi``).
    Drops the EXIF blob (UserComment, GPS, ...), PNG text chunks and
    any other ``info`` entries, so downstream code cannot accidentally
    read or leak them.  Pixel data is unchanged.
    """
    clean = image.copy()
    kept = {k: v for k, v in clean.info.items() if k in _SAFE_INFO_KEYS}
    clean.info.clear()
    clean.info.update(kept)
    text = getattr(clean, "text", None)
    if isinstance(text, dict):
        text.clear()
    return clean


def _check_dimensions(width: int, height: int) -> None:
    """Enforce the frozen 8192 px / 40 MP limits on a (w, h) pair."""
    if width <= 0 or height <= 0:
        raise invalid_input(
            "invalid_dimensions", "Image dimensions must be positive."
        )
    if width > MAX_DIMENSION_PX or height > MAX_DIMENSION_PX:
        raise invalid_input(
            "image_dimension_exceeded",
            "Image width or height exceeds the 8192 px limit.",
        )
    if width * height > MAX_PIXELS:
        raise invalid_input(
            "too_many_pixels",
            "Image pixel count exceeds the 40,000,000 px limit.",
        )


def load_image(data: bytes | bytearray | memoryview) -> ImageInput:
    """Validate and decode one image from in-memory bytes.

    Args:
        data: raw image bytes (PNG / JPEG / WebP).  No file path is
            accepted, by design -- see module docstring.

    Returns:
        An :class:`ImageInput` whose ``width``/``height`` are the
        EXIF-oriented dimensions and whose ``pil_image`` is the
        decoded, oriented, metadata-stripped image.

    Raises:
        InvalidInputError: with code ``INVALID_INPUT`` for every
            rejection (oversize, unsupported format, animated WebP,
            corrupt/truncated data, magic/format mismatch, decode
            failure).  Fail-closed: any unexpected decode exception is
            converted to ``INVALID_INPUT`` instead of propagating.
    """
    if isinstance(data, (bytearray, memoryview)):
        data = bytes(data)
    if not isinstance(data, bytes):
        raise invalid_input("not_bytes", "Image input must be bytes.")
    if len(data) == 0:
        raise invalid_input("empty_file", "Image input is empty.")
    if len(data) > MAX_FILE_SIZE_BYTES:
        raise invalid_input(
            "file_too_large", "Image file exceeds the 25 MiB limit."
        )

    fmt = detect_format(data)
    if fmt is None or fmt not in ACCEPTED_FORMATS:
        raise invalid_input(
            "unsupported_format",
            "Only PNG, JPEG and WebP images are accepted.",
        )

    # Raw-byte animation check first: cheap, decoder-independent.
    if fmt == "WEBP" and _webp_has_animation_flag(data):
        raise invalid_input(
            "animated_webp", "Animated WebP images are not accepted."
        )

    try:
        image = Image.open(BytesIO(data))
    except Exception as exc:  # noqa: BLE001 -- fail-closed by contract
        raise invalid_input(
            "decode_failed", "Image could not be decoded."
        ) from exc

    # Magic bytes and decoded format must agree (extension disguise /
    # magic spoofing is rejected here, not by file name).
    if image.format != fmt:
        raise invalid_input(
            "format_magic_mismatch",
            "Image content does not match its format signature.",
        )

    # Header dimensions are checked before full decode (bomb defence).
    width, height = image.size
    _check_dimensions(width, height)

    # Animated WebP, second check via the decoder's frame count.
    if fmt == "WEBP":
        try:
            n_frames = getattr(image, "n_frames", 1) or 1
            is_animated = bool(getattr(image, "is_animated", False))
        except Exception:  # noqa: BLE001 -- unreadable frame info: reject
            raise invalid_input(
                "animated_webp", "Animated WebP images are not accepted."
            ) from None
        if n_frames > 1 or is_animated:
            raise invalid_input(
                "animated_webp", "Animated WebP images are not accepted."
            )

    # EXIF orientation only (tag 274).  No other EXIF tag is read.
    oriented = False
    try:
        exif = image.getexif()
        orientation = exif.get(_EXIF_ORIENTATION_TAG) if exif else None
        oriented = orientation in (2, 3, 4, 5, 6, 7, 8)
    except Exception:  # noqa: BLE001 -- unreadable EXIF: treat as none
        oriented = False

    try:
        oriented_image = ImageOps.exif_transpose(image)
        if oriented_image is None:
            oriented_image = image
        oriented_image.load()  # full decode; truncated data fails here
    except InvalidInputError:
        raise
    except Exception as exc:  # noqa: BLE001 -- fail-closed by contract
        raise invalid_input(
            "decode_failed", "Image could not be decoded."
        ) from exc

    # Re-check dimensions after orientation (transpose swaps w/h) and
    # after full decode, in case a header lied about the true size.
    width, height = oriented_image.size
    _check_dimensions(width, height)

    clean_image = _strip_private_metadata(oriented_image)

    return ImageInput(
        data=data,
        mime=MIME_BY_FORMAT[fmt],
        format=fmt,
        width=width,
        height=height,
        oriented=oriented,
        pil_image=clean_image,
    )


def validate_expected_text(text: object) -> ExpectedTextInput:
    """Validate the user's expected text (PROJECT_BOOK.md §4.2, FR-02).

    * at most 5,000 Unicode code points (``len`` counts code points);
    * at most 100 lines (``CRLF`` / ``CR`` unified to ``LF`` first);
    * blank input (empty or whitespace-only) is rejected.

    Only newline unification is done here; full §4.3 normalisation
    (NFC, full-width mapping, whitespace folding) belongs to T004's
    ``core/normalize.py``.

    Raises:
        InvalidInputError: with code ``INVALID_INPUT`` for every
            rejection.  The error carries no user text.
    """
    if not isinstance(text, str):
        raise invalid_input(
            "expected_text_not_string", "Expected text must be a string."
        )
    if text.strip() == "":
        raise invalid_input(
            "expected_text_empty", "Expected text must not be blank."
        )
    if len(text) > MAX_EXPECTED_CODEPOINTS:
        raise invalid_input(
            "expected_text_too_long",
            "Expected text exceeds the 5,000 code point limit.",
        )
    if any(0xD800 <= ord(ch) <= 0xDFFF for ch in text):
        raise invalid_input(
            "expected_text_invalid_unicode",
            "Expected text contains unpaired surrogates.",
        )
    unified = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = tuple(unified.split("\n"))
    if len(lines) > MAX_EXPECTED_LINES:
        raise invalid_input(
            "expected_text_too_many_lines",
            "Expected text exceeds the 100 line limit.",
        )
    return ExpectedTextInput(
        raw=text,
        normalized_lines=lines,
        codepoint_count=len(text),
        line_count=len(lines),
    )
