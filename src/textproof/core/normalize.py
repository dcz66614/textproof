"""§4.3 normalisation (PROJECT_BOOK.md).

The single owner of the frozen §4.3 rules.  Both the expected text and
the OCR text go through exactly the same functions, in exactly the
order the spec lists them:

1. Unicode NFC normalisation.
2. ``CRLF`` / ``CR`` unified to ``LF``.
3. Full-width ASCII mapped to half-width ASCII; full-width space
   (U+3000) mapped to an ordinary space.
4. Per line: leading/trailing whitespace stripped; consecutive
   horizontal whitespace folded to a single space.
5. Case sensitive; punctuation kept; no synonym replacement, no
   semantic correction.
6. Character indices are Unicode code-point indices into the
   normalised text, spans half-open ``[start, end)``; the report keeps
   the raw user / OCR text separately (see :mod:`textproof.core.report`).

Notes on literal readings (frozen, do not "improve"):

* Full-width mapping covers exactly U+FF01–U+FF5E (full-width ASCII
  ``!``–``~``) plus U+3000.  U+FFE5 FULLWIDTH YEN SIGN (``￥``) is
  *not* ASCII and is *not* mapped; the S0 sample TP-S0-NUM-001 uses
  ``￥`` on both sides, so it compares equal either way, but mapping
  it would invent a rule the spec does not state.
* Horizontal whitespace folded by step 4 is space, tab, form feed,
  vertical tab and the Unicode spaces (including NBSP and U+3000,
  which step 3 already turned into a space).  Newlines are line
  separators, never folded.
* ``str.strip()`` / the fold regex use Python's Unicode whitespace
  definitions; no locale-dependent behaviour is involved.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Iterable, Sequence

__all__ = [
    "FULLWIDTH_ASCII_START",
    "FULLWIDTH_ASCII_END",
    "FULLWIDTH_SPACE",
    "normalize_text",
    "normalize_line",
    "normalize_lines",
    "split_normalized_lines",
    "normalize_expected_lines",
]

#: First full-width ASCII code point (U+FF01 FULLWIDTH EXCLAMATION MARK).
FULLWIDTH_ASCII_START: int = 0xFF01
#: Last full-width ASCII code point (U+FF5E FULLWIDTH TILDE).
FULLWIDTH_ASCII_END: int = 0xFF5E
#: Full-width space, mapped to an ordinary space by §4.3 step 3.
FULLWIDTH_SPACE: str = "\u3000"

#: Offset between a full-width ASCII code point and its half-width twin.
_FULLWIDTH_OFFSET: int = 0xFEE0

#: Runs of horizontal whitespace (space / tab / FF / VT / Unicode spaces).
_HORIZONTAL_WS_RE: re.Pattern[str] = re.compile(
    r"[ \t\x0b\x0c\u00a0\u1680\u2000-\u200a\u202f\u205f\u3000]+"
)


def _map_fullwidth_ascii(text: str) -> str:
    """Map U+FF01–U+FF5E to U+0021–U+007E and U+3000 to U+0020 (§4.3.3)."""
    out: list[str] = []
    for ch in text:
        cp = ord(ch)
        if FULLWIDTH_ASCII_START <= cp <= FULLWIDTH_ASCII_END:
            out.append(chr(cp - _FULLWIDTH_OFFSET))
        elif ch == FULLWIDTH_SPACE:
            out.append(" ")
        else:
            out.append(ch)
    return "".join(out)


def normalize_line(line: str) -> str:
    """Normalise one line (§4.3 steps 1, 3, 4; no newline handling).

    Assumes the line contains no ``\\r`` / ``\\n`` (use
    :func:`normalize_text` for whole texts).  Applies NFC, full-width
    mapping, then strip + horizontal-whitespace folding.
    """
    text = unicodedata.normalize("NFC", line)
    text = _map_fullwidth_ascii(text)
    text = _HORIZONTAL_WS_RE.sub(" ", text).strip()
    return text


def normalize_lines(lines: Iterable[str]) -> tuple[str, ...]:
    """Normalise each line of an already-split sequence (§4.3).

    Empty lines stay empty (a blank expected line is still a line; it
    is not silently dropped, so line counts and indices stay honest).
    """
    return tuple(normalize_line(line) for line in lines)


def normalize_text(text: str) -> str:
    """Normalise a whole multi-line text (§4.3 steps 1–4, in order).

    Newlines are unified to ``LF`` first (step 2), then each line is
    normalised by :func:`normalize_line` and rejoined with ``LF``.
    """
    unified = text.replace("\r\n", "\n").replace("\r", "\n")
    return "\n".join(normalize_line(line) for line in unified.split("\n"))


def split_normalized_lines(text: str) -> tuple[str, ...]:
    """Split a raw text into its normalised lines (§4.3).

    Equivalent to ``tuple(normalize_text(text).split("\\n"))``; kept as
    its own function because line splitting is what the aligner
    consumes.
    """
    return tuple(normalize_text(text).split("\n"))


def normalize_expected_lines(lines: Sequence[str]) -> tuple[str, ...]:
    """Normalise T002's ``ExpectedTextInput.normalized_lines`` (§4.3).

    T002 split on newlines only; the full §4.3 treatment (NFC,
    full-width mapping, whitespace folding) is applied here, exactly
    once, by this module.
    """
    return normalize_lines(lines)
