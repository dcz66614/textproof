"""FastAPI application factory and loopback-only server entry (T007).

Binding rule (PROJECT_BOOK.md §5.5, §9; IMPLEMENTATION_PLAN.md T007
acceptance 3): the service binds **only** ``127.0.0.1``.  Any other
host — ``0.0.0.0``, a public IP, a hostname, ``::1``, an empty string —
is rejected by :func:`validate_bind_host` **before** uvicorn starts,
so a misconfiguration can never silently open a public listener.
:func:`serve` is the only way this module starts a server, and it
always goes through that check.

No CORS middleware is registered (deliberate): the API serves the
local UI / CLI on the same machine only.  There is no external origin
to allow, and adding one would violate the T007 failure fallback
("API 不得为方便调试而开放公网监听或启用外部 CORS").

Run locally::

    python -m textproof.api.app            # 127.0.0.1:8765
    python -m textproof.api.app --port 9000
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import Final

import uvicorn
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from textproof.api.routes import (
    CODE_INTERNAL_ERROR,
    CODE_INVALID_REQUEST,
    ApiError,
    api_error_handler,
    router,
)
from textproof.core.report import TOOL_VERSION

logger = logging.getLogger(__name__)

#: The only bind address this service will ever use.
DEFAULT_HOST: Final[str] = "127.0.0.1"
#: Default port (PROJECT_BOOK.md §5.5 CLI example: ``serve --port 8765``).
DEFAULT_PORT: Final[int] = 8765

#: Hosts allowed by validate_bind_host: exactly the loopback address.
_ALLOWED_HOSTS: Final[frozenset[str]] = frozenset({DEFAULT_HOST})


def validate_bind_host(host: str) -> str:
    """Validate a bind host; return it iff it is exactly ``127.0.0.1``.

    Raises:
        ValueError: for ``0.0.0.0``, any public/private non-loopback
            IP, any hostname (including ``localhost``), ``::1``, or an
            empty/blank value.  The check is exact-string: no DNS
            resolution, no "looks like loopback" heuristics.
    """
    if not isinstance(host, str) or host != DEFAULT_HOST:
        raise ValueError(
            "TextProof binds only to 127.0.0.1; refusing host "
            f"{host!r}. Public / 0.0.0.0 listening is forbidden "
            "(PROJECT_BOOK.md §5.5, §9)."
        )
    return host


def create_app() -> FastAPI:
    """Build the FastAPI application (no CORS, no docs UI).

    The T008 local UI is served as same-origin static files at ``/``
    (see the mount in this function); it is not an API docs UI.
    """
    app = FastAPI(
        title="TextProof",
        version=TOOL_VERSION,
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )
    app.include_router(router)
    # T008: serve the local single-page UI from the same origin.
    # Mounted AFTER the API router, so /api/v1/* routes win; the UI
    # files (index.html / app.js / style.css) are same-origin static
    # assets only — no CDN, no external origin, no extra dependency
    # (starlette.staticfiles ships with FastAPI).  The UI directory is
    # resolved relative to this file, never from a request path.
    ui_dir = Path(__file__).resolve().parent.parent / "ui"
    app.mount("/", StaticFiles(directory=str(ui_dir), html=True), name="ui")
    app.add_exception_handler(ApiError, api_error_handler)

    async def _validation_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        # Pydantic request validation (missing / wrong-type / unknown
        # field, malformed JSON): normalise FastAPI's 422 body to the
        # API error envelope with the stable INVALID_REQUEST code.
        # The detail carries no user text — only the field locations.
        locations = sorted(
            {str(loc) for err in exc.errors() for loc in err.get("loc", ())}
        )
        return JSONResponse(
            status_code=422,
            content={
                "error": {
                    "code": CODE_INVALID_REQUEST,
                    "message": "Request body failed validation.",
                    "detail": ",".join(locations) if locations else "invalid_request",
                }
            },
        )

    async def _http_handler(
        request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        code = "NOT_FOUND" if exc.status_code == 404 else "HTTP_ERROR"
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": code,
                    "message": "Not found." if exc.status_code == 404 else "HTTP error.",
                    "detail": code.lower(),
                }
            },
        )

    async def _unhandled_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled error")
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": CODE_INTERNAL_ERROR,
                    "message": "Internal error.",
                    "detail": "unexpected_error",
                }
            },
        )

    app.add_exception_handler(RequestValidationError, _validation_handler)
    app.add_exception_handler(StarletteHTTPException, _http_handler)
    app.add_exception_handler(Exception, _unhandled_handler)
    return app


def serve(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT) -> None:
    """Serve the API on loopback only.

    Raises ValueError before binding unless ``host`` is ``127.0.0.1``.
    """
    validate_bind_host(host)
    if not isinstance(port, int) or not 1 <= port <= 65535:
        raise ValueError(f"Invalid port: {port!r}.")
    logger.info("TextProof API listening on %s:%d (loopback only)", host, port)
    uvicorn.run(create_app(), host=host, port=port, log_level="warning")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="textproof-api",
        description="TextProof local API (loopback only, 127.0.0.1).",
    )
    parser.add_argument(
        "--host",
        default=DEFAULT_HOST,
        help="Bind host; only 127.0.0.1 is accepted (default: %(default)s).",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=DEFAULT_PORT,
        help="Bind port (default: %(default)s).",
    )
    args = parser.parse_args(argv)
    serve(host=args.host, port=args.port)


if __name__ == "__main__":
    main()

__all__ = [
    "DEFAULT_HOST",
    "DEFAULT_PORT",
    "create_app",
    "main",
    "serve",
    "validate_bind_host",
]
