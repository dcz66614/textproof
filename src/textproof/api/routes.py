"""API routes and the check pipeline (T007).

Wiring only — no algorithm lives here:

* transport validation (MIME allow-list, strict base64, encoded-size
  pre-check) is done here because it is HTTP-layer input handling;
* image / expected-text limits are enforced by T002
  (:mod:`textproof.io.image_loader`, :mod:`textproof.contracts`) —
  this module only maps T002's ``InvalidInputError.reason`` to a
  stable, distinct API error code (see :data:`_REASON_TO_CODE`);
* OCR is T003's :class:`~textproof.ocr.rapidocr_adapter.RapidOCRAdapter`;
* comparison + report assembly is T004's
  :func:`textproof.core.report.build_report`.

Error model: every failure raised by :func:`run_check` is an
:class:`ApiError` carrying a stable ``code`` (documented in
``API_CONTRACT.md``), an HTTP status, and a short machine-readable
``detail`` (a snake_case reason, never user text, never a path, never
image bytes).  The only 500s are ``OCR_FAILED`` (the OCR engine raised)
and ``INTERNAL_ERROR`` (an unexpected exception, last resort); no
client-input failure ever surfaces as a bare 500.

OCR engine lifecycle: the adapter is expensive to construct (model
hash verification + ONNX session load), so one process-wide instance
is created lazily on the first ``/check`` and reused for later
requests.  That instance holds model weights only — never request
data — so reusing it does not retain images or reports across
requests.  :func:`set_ocr_adapter` / :func:`reset_ocr_adapter` exist
solely so tests can inject a stub engine (e.g. one that raises, to
exercise ``OCR_FAILED``); they are not part of any request path.
"""

from __future__ import annotations

import base64
import binascii
import logging
import threading
from typing import Final

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict

from textproof.contracts import (
    ERROR_CODE_INVALID_INPUT,
    MAX_FILE_SIZE_BYTES,
    MIME_BY_FORMAT,
    SCHEMA_ID,
)
from textproof.core.report import TOOL_VERSION, build_report
from textproof.io.image_loader import (
    InvalidInputError,
    load_image,
    validate_expected_text,
)
from textproof.ocr.rapidocr_adapter import (
    OCRAdapterError,
    ONNXRUNTIME_VERSION,
    RAPIDOCR_VERSION,
    RapidOCRAdapter,
)

logger = logging.getLogger(__name__)

SPEC_VERSION: Final[str] = "1.0.0"

# The largest base64 string that can decode to MAX_FILE_SIZE_BYTES
# (25 MiB): ceil(25 MiB / 3) * 4.  Anything longer is rejected as
# IMAGE_TOO_LARGE *before* decoding, so an oversized payload can
# never force a large allocation.
_MAX_BASE64_CHARS: Final[int] = ((MAX_FILE_SIZE_BYTES + 2) // 3) * 4

#: MIME types accepted by POST /api/v1/check (PROJECT_BOOK.md §4.2).
ACCEPTED_MIMES: Final[frozenset[str]] = frozenset(MIME_BY_FORMAT.values())

# --- API error codes (stable; see API_CONTRACT.md §4) -------------------
CODE_INVALID_REQUEST: Final[str] = "INVALID_REQUEST"
CODE_INVALID_IMAGE_MIME: Final[str] = "INVALID_IMAGE_MIME"
CODE_INVALID_BASE64: Final[str] = "INVALID_BASE64"
CODE_IMAGE_TOO_LARGE: Final[str] = "IMAGE_TOO_LARGE"
CODE_IMAGE_DIMENSION_EXCEEDED: Final[str] = "IMAGE_DIMENSION_EXCEEDED"
CODE_IMAGE_TOO_MANY_PIXELS: Final[str] = "IMAGE_TOO_MANY_PIXELS"
CODE_INVALID_IMAGE_FORMAT: Final[str] = "INVALID_IMAGE_FORMAT"
CODE_ANIMATED_IMAGE_NOT_SUPPORTED: Final[str] = "ANIMATED_IMAGE_NOT_SUPPORTED"
CODE_INVALID_IMAGE: Final[str] = "INVALID_IMAGE"
CODE_EXPECTED_TEXT_EMPTY: Final[str] = "EXPECTED_TEXT_EMPTY"
CODE_EXPECTED_TEXT_TOO_LONG: Final[str] = "EXPECTED_TEXT_TOO_LONG"
CODE_EXPECTED_TEXT_TOO_MANY_LINES: Final[str] = "EXPECTED_TEXT_TOO_MANY_LINES"
CODE_OCR_FAILED: Final[str] = "OCR_FAILED"
CODE_INTERNAL_ERROR: Final[str] = "INTERNAL_ERROR"

#: T002 InvalidInputError.reason -> distinct API error code.
#: Every reason the loader can produce is mapped; unknown reasons
#: fall back to INVALID_IMAGE / INVALID_INPUT (never a bare 500).
_REASON_TO_CODE: Final[dict[str, str]] = {
    "file_too_large": CODE_IMAGE_TOO_LARGE,
    "image_dimension_exceeded": CODE_IMAGE_DIMENSION_EXCEEDED,
    "too_many_pixels": CODE_IMAGE_TOO_MANY_PIXELS,
    "unsupported_format": CODE_INVALID_IMAGE_FORMAT,
    "animated_webp": CODE_ANIMATED_IMAGE_NOT_SUPPORTED,
    "decode_failed": CODE_INVALID_IMAGE,
    "empty_file": CODE_INVALID_IMAGE,
    "not_bytes": CODE_INVALID_IMAGE,
    "invalid_dimensions": CODE_INVALID_IMAGE,
    "format_magic_mismatch": CODE_INVALID_IMAGE,
    "expected_text_empty": CODE_EXPECTED_TEXT_EMPTY,
    "expected_text_too_long": CODE_EXPECTED_TEXT_TOO_LONG,
    "expected_text_too_many_lines": CODE_EXPECTED_TEXT_TOO_MANY_LINES,
    "expected_text_not_string": ERROR_CODE_INVALID_INPUT,
    "expected_text_invalid_unicode": ERROR_CODE_INVALID_INPUT,
}


class ApiError(Exception):
    """An API failure with a stable code and HTTP status.

    ``detail`` is a short machine-readable reason (snake_case); it
    never contains user text, image bytes, or a file path.
    """

    def __init__(
        self, code: str, status: int, message: str, detail: str | None = None
    ) -> None:
        self.code = code
        self.status = status
        self.message = message
        self.detail = detail
        super().__init__(f"{code}: {detail or message}")

    def body(self) -> dict[str, object]:
        error: dict[str, object] = {
            "code": self.code,
            "message": self.message,
        }
        if self.detail is not None:
            error["detail"] = self.detail
        return {"error": error}


def _from_invalid_input(exc: InvalidInputError) -> ApiError:
    code = _REASON_TO_CODE.get(exc.reason, ERROR_CODE_INVALID_INPUT)
    return ApiError(code, 400, "Input failed validation.", detail=exc.reason)


class CheckRequest(BaseModel):
    """POST /api/v1/check request body (PROJECT_BOOK.md §5.5).

    ``extra="forbid"``: unknown fields are rejected with
    ``INVALID_REQUEST`` (422) instead of silently ignored.
    """

    model_config = ConfigDict(extra="forbid")

    image_mime: str
    image_base64: str
    expected_text: str


# --- OCR engine singleton (model weights only, no request data) --------

_adapter: RapidOCRAdapter | None = None
_adapter_lock = threading.Lock()


def get_ocr_adapter() -> RapidOCRAdapter:
    """Return the process-wide OCR adapter, creating it on first use."""
    global _adapter
    if _adapter is None:
        with _adapter_lock:
            if _adapter is None:
                _adapter = RapidOCRAdapter()
    return _adapter


def set_ocr_adapter(adapter: RapidOCRAdapter | None) -> None:
    """Test-only injection: replace the singleton (``None`` clears it).

    Not used by any request path in production; tests use it to inject
    a stub engine (e.g. one that raises, to exercise OCR_FAILED).
    """
    global _adapter
    with _adapter_lock:
        _adapter = adapter


def reset_ocr_adapter() -> None:
    """Drop the singleton so the next request rebuilds the real engine."""
    set_ocr_adapter(None)


# --- check pipeline ------------------------------------------------------

def run_check(
    *,
    image_mime: str,
    image_base64: str,
    expected_text: str,
    adapter: RapidOCRAdapter | None = None,
) -> dict[str, object]:
    """Run one check entirely in memory; return a ``textproof.report/v1`` dict.

    Steps: MIME allow-list -> strict base64 decode (with an encoded-size
    pre-check) -> T002 image validation (magic bytes, 25 MiB / 8192 px /
    40 MP, EXIF orientation) -> MIME-vs-detected-format agreement ->
    T002 expected-text validation -> T003 OCR on the decoded PIL image
    -> T004 ``build_report``.

    Raises :class:`ApiError` with a stable code for every failure (see
    ``API_CONTRACT.md`` §4).  A successful return holds only the report
    dict; the image bytes are request-local and dropped on return.
    ``expected_text`` is never logged.
    """
    if not isinstance(image_mime, str) or image_mime not in ACCEPTED_MIMES:
        raise ApiError(
            CODE_INVALID_IMAGE_MIME,
            400,
            "image_mime must be image/png, image/jpeg or image/webp.",
            detail="unsupported_mime",
        )
    if not isinstance(image_base64, str) or image_base64 == "":
        raise ApiError(
            CODE_INVALID_BASE64,
            400,
            "image_base64 must be a non-empty base64 string.",
            detail="empty_base64",
        )
    if len(image_base64) > _MAX_BASE64_CHARS:
        raise ApiError(
            CODE_IMAGE_TOO_LARGE,
            400,
            "Decoded image would exceed the 25 MiB limit.",
            detail="file_too_large",
        )
    try:
        raw_bytes = base64.b64decode(image_base64, validate=True)
    except (binascii.Error, ValueError):
        raise ApiError(
            CODE_INVALID_BASE64,
            400,
            "image_base64 is not valid base64.",
            detail="invalid_base64",
        ) from None

    try:
        image = load_image(raw_bytes)
    except InvalidInputError as exc:
        raise _from_invalid_input(exc) from None
    finally:
        # The decoded bytes are only needed for load_image; drop the
        # reference as soon as validation is done.
        del raw_bytes

    if image.mime != image_mime:
        raise ApiError(
            CODE_INVALID_IMAGE_MIME,
            400,
            "image_mime does not match the image content.",
            detail="mime_mismatch",
        )

    try:
        expected = validate_expected_text(expected_text)
    except InvalidInputError as exc:
        raise _from_invalid_input(exc) from None

    if adapter is not None:
        engine = adapter
    else:
        try:
            engine = get_ocr_adapter()
        except (FileNotFoundError, ValueError, RuntimeError) as exc:
            # R-04 (PROJECT_BOOK.md §9): engine construction happens
            # outside the recognise() OCR_FAILED range below, so a
            # missing asset used to bubble up to check()'s generic
            # handler, whose logger.exception wrote the absolute
            # asset path into the server log.  Map construction
            # failure to OCR_FAILED exactly like a recognise()
            # failure, and log only the exception type — never the
            # message.  Offline behaviour is unchanged: a missing
            # asset still refuses a runtime download and still fails
            # the request, only the log stays clean.
            logger.error("OCR failed: %s", type(exc).__name__)
            raise ApiError(
                CODE_OCR_FAILED,
                500,
                "OCR failed to produce a result.",
                detail="ocr_engine_error",
            ) from None
    try:
        ocr_lines = engine.recognize(image.pil_image)
    except (OCRAdapterError, ValueError, RuntimeError) as exc:
        # Engine failure: a defined 500 with code OCR_FAILED, not a
        # bare 500.  Never log recognised text or user input.
        logger.error("OCR failed: %s", type(exc).__name__)
        raise ApiError(
            CODE_OCR_FAILED,
            500,
            "OCR failed to produce a result.",
            detail="ocr_engine_error",
        ) from None

    return build_report(image, expected, ocr_lines)


# --- routes ---------------------------------------------------------------

router = APIRouter()


@router.get("/api/v1/health")
def health() -> dict[str, object]:
    """Health status; contains no user data (PROJECT_BOOK.md §5.5)."""
    return {
        "status": "ok",
        "service": "textproof",
        "tool_version": TOOL_VERSION,
        "schema": SCHEMA_ID,
    }


@router.get("/api/v1/version")
def version() -> dict[str, object]:
    """Versions: product, schema, spec, and the frozen OCR route.

    Reports frozen version constants only; it does not construct the
    OCR engine, so it answers even before the first /check.
    """
    return {
        "service": "textproof",
        "tool_version": TOOL_VERSION,
        "schema": SCHEMA_ID,
        "spec_version": SPEC_VERSION,
        "rapidocr_version": RAPIDOCR_VERSION,
        "onnxruntime_version": ONNXRUNTIME_VERSION,
        "providers": ["CPUExecutionProvider"],
    }


# Short alias required by the T007 card wording ("/version").
@router.get("/version")
def version_alias() -> dict[str, object]:
    return version()


@router.post("/api/v1/check")
def check(payload: CheckRequest) -> dict[str, object]:
    """Check one image against expected text; return textproof.report/v1."""
    try:
        return run_check(
            image_mime=payload.image_mime,
            image_base64=payload.image_base64,
            expected_text=payload.expected_text,
        )
    except ApiError:
        raise
    except Exception:  # noqa: BLE001 -- last resort, never a bare 500
        logger.exception("Unexpected error in /api/v1/check")
        raise ApiError(
            CODE_INTERNAL_ERROR,
            500,
            "Internal error.",
            detail="unexpected_error",
        ) from None


async def api_error_handler(request: Request, exc: ApiError) -> JSONResponse:
    return JSONResponse(status_code=exc.status, content=exc.body())


__all__ = [
    "ACCEPTED_MIMES",
    "CODE_ANIMATED_IMAGE_NOT_SUPPORTED",
    "CODE_EXPECTED_TEXT_EMPTY",
    "CODE_EXPECTED_TEXT_TOO_LONG",
    "CODE_EXPECTED_TEXT_TOO_MANY_LINES",
    "CODE_IMAGE_DIMENSION_EXCEEDED",
    "CODE_IMAGE_TOO_LARGE",
    "CODE_IMAGE_TOO_MANY_PIXELS",
    "CODE_INTERNAL_ERROR",
    "CODE_INVALID_BASE64",
    "CODE_INVALID_IMAGE",
    "CODE_INVALID_IMAGE_FORMAT",
    "CODE_INVALID_IMAGE_MIME",
    "CODE_INVALID_REQUEST",
    "CODE_OCR_FAILED",
    "SPEC_VERSION",
    "ApiError",
    "CheckRequest",
    "api_error_handler",
    "get_ocr_adapter",
    "reset_ocr_adapter",
    "router",
    "run_check",
    "set_ocr_adapter",
]
