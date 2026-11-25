"""Input / IO layer: image loading and validation (T002)."""

from textproof.io.image_loader import (
    InvalidInputError,
    detect_format,
    load_image,
    validate_expected_text,
)

__all__ = [
    "InvalidInputError",
    "detect_format",
    "load_image",
    "validate_expected_text",
]
