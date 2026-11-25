"""TextProof comparison core (PROJECT_BOOK.md §4.3–§4.6, §7).

Public entry points: :func:`textproof.core.report.compare` (expected
text + fixed OCR line records → :class:`ComparisonResult`) and
:func:`textproof.core.report.build_report` (adds the §5.4 image block).
The core never touches the OCR engine, the network or the UI, so it
is testable on fixed OCR line records alone.
"""

from textproof.core.align_lines import (
    AMBIGUITY_MARGIN,
    GAP_PENALTY,
    HIGH_COST_PAIR_THRESHOLD,
    LineAlignment,
    align_lines,
    pair_cost,
)
from textproof.core.classify import Difference
from textproof.core.line_order import order_lines
from textproof.core.normalize import (
    normalize_line,
    normalize_lines,
    normalize_text,
    split_normalized_lines,
)
from textproof.core.report import (
    TOOL_VERSION,
    ComparisonResult,
    build_report,
    compare,
)
from textproof.core.weighted_edit import (
    COST_CONFUSION,
    COST_DIGIT,
    COST_PUNCTUATION,
    weighted_edit_distance,
    weighted_edit_ops,
)

__all__ = [
    "AMBIGUITY_MARGIN",
    "COST_CONFUSION",
    "COST_DIGIT",
    "COST_PUNCTUATION",
    "GAP_PENALTY",
    "HIGH_COST_PAIR_THRESHOLD",
    "TOOL_VERSION",
    "ComparisonResult",
    "Difference",
    "LineAlignment",
    "align_lines",
    "build_report",
    "compare",
    "normalize_line",
    "normalize_lines",
    "normalize_text",
    "order_lines",
    "pair_cost",
    "split_normalized_lines",
    "weighted_edit_distance",
    "weighted_edit_ops",
]
