"""TextProof local HTTP API (T007).

Implements ``PROJECT_BOOK.md`` §5.5 / §6.1 item 6 and §9:

* ``GET /api/v1/health`` — health status, no user data.
* ``GET /api/v1/version`` — versions (product, schema, spec, OCR).
* ``POST /api/v1/check`` — JSON ``{image_mime, image_base64,
  expected_text}`` in memory; returns ``textproof.report/v1``.

Binding is loopback-only (``127.0.0.1``); see :mod:`textproof.api.app`
for the enforced check. No CORS middleware is registered anywhere in
this package — the API is for the local UI / CLI on the same machine
only (PROJECT_BOOK.md §5.5: "不启用公网监听、CORS 外域白名单或外部回调").

Statelessness (§9): the service keeps no per-request state. The only
module-level object is the OCR engine singleton (model weights, not
request data). Image bytes and reports live only in request-local
variables and are dropped when the handler returns; nothing is written
to disk, to a database, or to any cache. The OCR adapter itself is
owned by T003 (``textproof.ocr.rapidocr_adapter``) and is not modified
here; the comparison core is owned by T004
(``textproof.core.report.build_report``) and is not modified here.
This package only validates transport input, decodes base64, and
wires the frozen modules together.
"""

from textproof.api.app import (
    DEFAULT_HOST,
    DEFAULT_PORT,
    create_app,
    serve,
    validate_bind_host,
)
from textproof.api.routes import ApiError, CheckRequest, run_check

__all__ = [
    "DEFAULT_HOST",
    "DEFAULT_PORT",
    "ApiError",
    "CheckRequest",
    "create_app",
    "run_check",
    "serve",
    "validate_bind_host",
]
