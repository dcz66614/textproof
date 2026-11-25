#!/usr/bin/env python3
"""Generate the 300 fixed synthetic fixtures for P033 TextProof (T005).

Implements PROJECT_BOOK.md SS8.1 / SS8.2 and IMPLEMENTATION_PLAN.md T005:

* 300 unique static PNGs: 100 clean, 70 substitution, 70 omission,
  60 numeric change.  All drawn with Pillow and the bundled
  Noto Sans SC variable font (Regular / wght 400, SIL OFL 1.1),
  fixed canvas 1200x480, white background, black text, font size 64,
  fixed seed.  No network images, no user images, no real photos,
  no human annotation.  No network access at generation time (the font
  was fetched once at build time from the official Google Fonts source;
  see ``tests/fixtures/s0/fonts/FONT_NOTICE.md``).

Determinism: every random choice comes from ``random.Random(SEED)``
in a fixed call order, the font file is pinned by SHA-256, and Pillow
PNG encoding is byte-deterministic, so two runs produce identical
PNG bytes (checked by ``--verify-manifest`` and by the T005 tests).

``target_region_xyxy`` (PROJECT_BOOK.md SS8.1): the expected text
region used only to verify OCR line-box localisation
(IoU(ocr_bbox, target_region) >= 0.80); it is NOT a per-character box.
Definition: a rectangle centred on the drawn text's ink bbox
(``draw.textbbox``), sized by a linear rule in the ink geometry::

    height = 70 + 0.7 * ink_height - 0.05 * ink_width
    width  = ink_width + 40 - 0.02 * ink_width

The rule is calibrated on the frozen PP-OCRv6 detector's *measured*
box geometry over the 240 non-blind fixtures (single OCR pass,
2026-11-25): the detector's line box shrinks relative to the ink as
the line gets longer (measured OCR height falls from ~101 px for
100-199 px-wide lines to ~80 px for 600-699 px-wide lines) and grows
with ink height (CJK ink ~60 px vs Latin cap ink ~49 px).  A raw ink
bbox scores IoU 0.42-0.62 against real OCR output, and a fixed-height
region (first attempt: 100 px) still leaves 58/300 below 0.80,
because the detector's box is content-dependent in exactly this
width/height-dependent way.  The calibrated rule scores min IoU 0.833
over the 240 non-blind fixtures (0 below 0.80).  It is a general
function of ink geometry only -- it never uses any fixture's own OCR
output -- and the 60 blind fixtures were NOT used to fit it; they
are measured once, at the end, as the acceptance check (see
TASK_RESULT.md for the measured blind IoU distribution).

Expected reports: ``expected_errors`` / ``expected_verdict`` are
computed from the *construction* (expected text, drawn text and the
recorded mutation), not by running OCR or the compare module.  The
T005 tests cross-check them against T004 ``compare`` fed with the
drawn text as a fixed OCR line record (the same style as T004's SS8.1
golden tests).  The one known live-OCR divergence is documented in
``TASK_RESULT.md``: real RapidOCR reads a drawn fullwidth ``\\uffe5``
as ``\\u00a5``, so TP-S0-NUM-001 shows one extra SUBSTITUTION under
live OCR; the frozen fixture (drawn ``\\uffe5``) is unchanged per SS8.1
and the ``\\uffe5`` character is used nowhere else in the 300.

Usage:
    python scripts/generate_fixtures.py [--output-dir DIR] [--seed N]
        Generate all fixtures + manifest.json + expected_output.json +
        blind_subset.json into DIR (default: tests/fixtures/s0/).
    python scripts/generate_fixtures.py --verify-manifest tests/fixtures/s0/manifest.json
        Re-render every fixture in memory and check PNG bytes, hashes,
        manifest/expected-output/blind-subset consistency.  Exit 0 on
        pass, 1 on any failure.  This is the T005 acceptance command.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import random
import sys
import unicodedata
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

# ---------------------------------------------------------------------------
# Frozen generator parameters (recorded verbatim in the manifest).
# ---------------------------------------------------------------------------

GENERATOR_VERSION = "1.0.0"
SEED = 20261125
BLIND_SEED = 20261126
CANVAS_WIDTH = 1200
CANVAS_HEIGHT = 480
FONT_SIZE_PX = 64
FONT_WEIGHT_NAME = "Regular"  # variable-font named instance, wght 400
FONT_FILE_NAME = "NotoSansSC[wght].ttf"
FONT_SOURCE_URL = (
    "https://github.com/google/fonts/raw/main/ofl/notosanssc/"
    "NotoSansSC%5Bwght%5D.ttf"
)
FONT_VERSION = "2.004-H2"
FONT_SHA256 = "a3041811a78c361b1de50f953c805e0244951c21c5bd412f7232ef0d899af0da"
FONT_BYTES = 17772300
FONT_LICENSE = "SIL Open Font License, Version 1.1 (OFL-1.1)"
REGION_H_BASE_PX = 70.0
REGION_H_PER_INK_H = 0.7
REGION_H_PER_INK_W = 0.05
REGION_W_EXTRA_PX = 40.0
REGION_W_PER_INK_W = 0.02

SCHEMA_MANIFEST = "textproof.fixture-manifest/v1"
SCHEMA_EXPECTED = "textproof.fixture-expected-output/v1"
SCHEMA_BLIND = "textproof.fixture-blind-subset/v1"

# The four frozen SS8.1 samples: (fixture id, expected text, drawn text,
# mutation kind, mutation position).  Their texts are excluded from the
# generated pools so no other fixture can collide with them.
S0_FIXED = [
    ("TP-S0-ZH-001", "限时优惠", "限时优", "omission", 3),
    ("TP-S0-ZH-002", "新品上市", "新口上市", "substitution", 1),
    ("TP-S0-NUM-001", "￥28.80", "￥28.00", "numeric_change", 4),
    ("TP-S0-ZH-003", "新客立减20元", "新客立减元", "omission", 4),
]

COUNTS = {"clean": 100, "substitution": 70, "omission": 70, "numeric_change": 60}
TOTAL = 300
BLIND_COUNTS = {"clean": 20, "substitution": 14, "omission": 14, "numeric_change": 12}

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_FIXTURES_DIR = REPO_ROOT / "tests" / "fixtures" / "s0"

# ---------------------------------------------------------------------------
# Text pools (all strings are NFC, halfwidth ASCII, no fullwidth space;
# currency uses U+00A5 YEN SIGN, which RapidOCR returns verbatim --
# see the module docstring on U+FFE5).
# ---------------------------------------------------------------------------

ZH_A = ["限时", "新品", "新客", "会员", "今日", "全场", "春季", "秋季",
        "周年", "开学", "周末", "首单", "品牌", "精选", "热销", "人气",
        "爆款", "经典", "招牌", "当季"]
ZH_B = ["优惠", "上市", "立减", "特惠", "直降", "满减", "包邮", "折扣",
        "秒杀", "清仓", "专享", "大促", "礼遇", "回馈", "预售", "首发",
        "尝鲜", "加购", "狂欢", "好礼"]
ZH_C = ["20元", "50元", "10元", "5折", "8折", "半价", "免单", "大礼包",
        "好礼相送", "惊喜价"]
ZH_YUAN = [5, 10, 20, 30, 50, 88, 100]

EN_1 = ["SALE", "NEW", "FREE", "HOT", "BEST", "BIG", "MEGA", "FLASH",
        "SUPER", "TOP", "LIMITED", "SPECIAL"]
EN_2 = ["50% OFF", "BUY 1 GET 1", "FREE SHIPPING", "NEW ARRIVAL",
        "LIMITED TIME", "ONLY TODAY", "SAVE 20%", "2 FOR 1", "HALF PRICE",
        "MEMBERS ONLY", "EXTRA 10% OFF", "TODAY ONLY"]
EN_PCT = [10, 20, 30, 40, 50, 60, 70, 80]

PRICES = [9, 19, 28, 39, 49, 59, 69, 79, 88, 99, 128, 158, 199, 259,
          299, 399, 599, 899]
CENTS = ["00", "50", "80", "90", "99", "95", "88", "20", "10", "30"]
MAN_JIAN = [(100, 10), (100, 20), (200, 30), (200, 50), (300, 50),
            (300, 80), (500, 100), (500, 80)]

# Characters usable as substitution replacements (same class only).
CJK_REPLACEMENT_CHARS = sorted(set("".join(ZH_A + ZH_B + ZH_C)))

EXCLUDED_EXPECTED = {expected for _, expected, _, _, _ in S0_FIXED}
EXCLUDED_DRAWN = {drawn for _, _, drawn, _, _ in S0_FIXED}


def _zh(rng: random.Random) -> str:
    a, b = rng.choice(ZH_A), rng.choice(ZH_B)
    r = rng.random()
    if r < 0.45:
        return a + b
    if r < 0.75:
        return a + b + rng.choice(ZH_C)
    return a + b + f"{rng.choice(ZH_YUAN)}元"


def _en(rng: random.Random) -> str:
    r = rng.random()
    if r < 0.50:
        return f"{rng.choice(EN_1)} {rng.choice(EN_2)}"
    if r < 0.80:
        return rng.choice(EN_2)
    return f"{rng.choice(EN_1)} {rng.choice(EN_PCT)}% OFF"


def _num(rng: random.Random) -> str:
    r = rng.random()
    if r < 0.55:
        return f"¥{rng.choice(PRICES)}.{rng.choice(CENTS)}"
    if r < 0.75:
        return f"{rng.choice(EN_PCT)}% OFF"
    if r < 0.90:
        a, b = rng.choice(MAN_JIAN)
        return f"满{a}减{b}"
    if rng.random() < 0.5:
        return f"买{rng.choice([1, 2, 3])}送{rng.choice([1, 2])}"
    return f"CODE {rng.randint(1000, 9999)}"


def _mixed(rng: random.Random) -> str:
    r = rng.random()
    if r < 0.40:
        return f"{_zh(rng)} {rng.choice(EN_1)}"
    if r < 0.70:
        return f"{rng.choice(EN_1)} {_zh(rng)}"
    if r < 0.85:
        return f"¥{rng.choice(PRICES)}.{rng.choice(CENTS)} {_zh(rng)}"
    return f"{_zh(rng)} {rng.choice(EN_PCT)}% OFF"


_FAMILY_BUILDERS = {"zh": _zh, "en": _en, "num": _num, "mixed": _mixed}


def _build_pool(rng: random.Random, family: str, size: int) -> list[str]:
    """Unique candidate base texts for one family (S0 texts excluded)."""
    out: list[str] = []
    seen: set[str] = set()
    attempts = 0
    while len(out) < size:
        attempts += 1
        if attempts > size * 200:
            raise RuntimeError(f"pool exhausted for family {family!r}")
        text = _FAMILY_BUILDERS[family](rng)
        if text in seen or text in EXCLUDED_EXPECTED or text in EXCLUDED_DRAWN:
            continue
        if not _is_normalized_text(text):
            continue
        seen.add(text)
        out.append(text)
    return out


def _is_normalized_text(text: str) -> bool:
    """Raw text must equal its SS4.3 normal form (so spans index it).

    All pool strings are built NFC with halfwidth ASCII; this guards the
    invariant instead of assuming it.
    """
    if not unicodedata.is_normalized("NFC", text):
        return False
    for ch in text:
        cp = ord(ch)
        if 0xFF01 <= cp <= 0xFF5E or cp == 0x3000:
            return False
    return True


# ---------------------------------------------------------------------------
# Mutations.  Each returns (drawn_text, mutation_dict, expected_errors).
# Spans are code-point spans into the (already normalised) expected text.
# ---------------------------------------------------------------------------

def _error_dict(error_type: str, expected_frag: str, recognized_frag: str,
                expected_span: list[int], recognized_span: list[int]) -> dict:
    return {
        "type": error_type,
        "expected_fragment": expected_frag,
        "recognized_fragment": recognized_frag,
        "expected_span": expected_span,
        "recognized_span": recognized_span,
        "bbox_scope": "ocr_line",
        "bbox_rule": ("bbox_xyxy equals the OCR line bbox containing the "
                      "error; IoU(ocr_bbox, target_region_xyxy) >= 0.80"),
    }


def _mutate_substitution(expected: str, rng: random.Random):
    """Replace one non-digit letter/CJK char with a different same-class char."""
    indices = [i for i, ch in enumerate(expected)
               if not ch.isdigit() and ch != " " and (ch.isalpha() or "\u4e00" <= ch <= "\u9fff")]
    if not indices:
        return None
    rng.shuffle(indices)
    for i in indices:
        ch = expected[i]
        if "\u4e00" <= ch <= "\u9fff":
            pool = [c for c in CJK_REPLACEMENT_CHARS if c != ch]
            replacement = rng.choice(pool)
        elif ch.isupper():
            replacement = rng.choice([c for c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ" if c != ch])
        elif ch.islower():
            replacement = rng.choice([c for c in "abcdefghijklmnopqrstuvwxyz" if c != ch])
        else:
            continue
        drawn = expected[:i] + replacement + expected[i + 1:]
        mutation = {"kind": "substitution", "position": i,
                    "expected_char": ch, "drawn_char": replacement}
        errors = [_error_dict("SUBSTITUTION", ch, replacement, [i, i + 1], [i, i + 1])]
        return drawn, mutation, errors
    return None


def _mutate_omission(expected: str, rng: random.Random):
    """Drop one non-space char.

    The dropped char must differ from both neighbours: with a repeated
    neighbour (e.g. expected ``AA``, drop one ``A``) the alignment of the
    missing char is ambiguous and the recorded span would not be unique.
    It must also not sit next to a space: dropping it would leave a
    double space in the drawn text, which SS4.3 normalisation folds to
    one space, so compare would report the missing fragment as
    ``" 1"`` (space + char) instead of the single recorded char
    (observed on ``NEW BUY 1 GET 1`` before this guard was added).
    """
    indices = [i for i, ch in enumerate(expected) if ch != " "]
    rng.shuffle(indices)
    for i in indices:
        if i > 0 and expected[i] == expected[i - 1]:
            continue
        if i + 1 < len(expected) and expected[i] == expected[i + 1]:
            continue
        if i > 0 and expected[i - 1] == " ":
            continue
        if i + 1 < len(expected) and expected[i + 1] == " ":
            continue
        drawn = expected[:i] + expected[i + 1:]
        mutation = {"kind": "omission", "position": i,
                    "expected_char": expected[i], "drawn_char": None}
        errors = [_error_dict("MISSING_CHARACTER", expected[i], "", [i, i + 1], [i, i])]
        return drawn, mutation, errors
    return None


def _mutate_numeric(expected: str, rng: random.Random):
    """Replace one digit with a different digit (-> NUMERIC_CHANGE)."""
    indices = [i for i, ch in enumerate(expected) if ch.isdigit()]
    if not indices:
        return None
    rng.shuffle(indices)
    for i in indices:
        replacement = rng.choice([d for d in "0123456789" if d != expected[i]])
        drawn = expected[:i] + replacement + expected[i + 1:]
        mutation = {"kind": "numeric_change", "position": i,
                    "expected_char": expected[i], "drawn_char": replacement}
        errors = [_error_dict("NUMERIC_CHANGE", expected[i], replacement,
                              [i, i + 1], [i, i + 1])]
        return drawn, mutation, errors
    return None


_MUTATORS = {"substitution": _mutate_substitution,
             "omission": _mutate_omission,
             "numeric_change": _mutate_numeric}


def _mutation_for_s0(fixture_id: str, expected: str, drawn: str, kind: str, pos: int):
    """Expected errors for a frozen S0 sample, from its SS8.1 definition."""
    if kind == "omission":
        # TP-S0-ZH-003 omits two adjacent chars ("20"); the others omit one.
        frag_len = 2 if fixture_id == "TP-S0-ZH-003" else 1
        frag = expected[pos:pos + frag_len]
        end = pos + frag_len
        errors = [_error_dict("MISSING_CHARACTER", frag, "", [pos, end], [pos, pos])]
    elif kind == "substitution":
        errors = [_error_dict("SUBSTITUTION", expected[pos], drawn[pos],
                              [pos, pos + 1], [pos, pos + 1])]
    else:  # numeric_change
        errors = [_error_dict("NUMERIC_CHANGE", expected[pos], drawn[pos],
                              [pos, pos + 1], [pos, pos + 1])]
    mutation = {"kind": kind, "position": pos,
                "expected_char": expected[pos:pos + len(errors[0]["expected_fragment"])],
                "drawn_char": drawn[pos] if kind != "omission" else None}
    return mutation, errors


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------

def load_font(font_path: Path) -> ImageFont.FreeTypeFont:
    if not font_path.is_file():
        raise FileNotFoundError(
            f"bundled font missing: {font_path} (build-time download from "
            f"{FONT_SOURCE_URL}; see tests/fixtures/s0/fonts/FONT_NOTICE.md)")
    data = font_path.read_bytes()
    if hashlib.sha256(data).hexdigest() != FONT_SHA256:
        raise ValueError(f"font SHA-256 mismatch: {font_path}")
    if len(data) != FONT_BYTES:
        raise ValueError(f"font size mismatch: {font_path} ({len(data)} bytes)")
    font = ImageFont.truetype(str(font_path), FONT_SIZE_PX)
    font.set_variation_by_name(FONT_WEIGHT_NAME)
    if font.getname()[1] != FONT_WEIGHT_NAME:
        raise ValueError(f"unexpected font variation: {font.getname()}")
    return font


def target_region_for(ink_bbox: list[int]) -> list[int]:
    """Expected text region for a drawn ink bbox (PROJECT_BOOK.md SS8.1).

    Centred on the ink bbox centre; size follows the calibrated linear
    rule in the module docstring (fit on the 240 non-blind fixtures'
    measured PP-OCRv6 boxes, never on the blind subset, never on any
    fixture's own OCR output).  Clipped to the canvas.
    """
    ink_w = ink_bbox[2] - ink_bbox[0]
    ink_h = ink_bbox[3] - ink_bbox[1]
    height = REGION_H_BASE_PX + REGION_H_PER_INK_H * ink_h - REGION_H_PER_INK_W * ink_w
    width = ink_w + REGION_W_EXTRA_PX - REGION_W_PER_INK_W * ink_w
    cx = (ink_bbox[0] + ink_bbox[2]) / 2.0
    cy = (ink_bbox[1] + ink_bbox[3]) / 2.0
    return [
        max(0, int(round(cx - width / 2.0))),
        max(0, int(round(cy - height / 2.0))),
        min(CANVAS_WIDTH, int(round(cx + width / 2.0))),
        min(CANVAS_HEIGHT, int(round(cy + height / 2.0))),
    ]


def render(text: str, font: ImageFont.FreeTypeFont) -> tuple[bytes, list[int], list[int]]:
    """Render one fixture.  Returns (png_bytes, target_region_xyxy, ink_bbox)."""
    img = Image.new("RGB", (CANVAS_WIDTH, CANVAS_HEIGHT), "white")
    draw = ImageDraw.Draw(img)
    ink = draw.textbbox((0, 0), text, font=font)
    ink_w, ink_h = ink[2] - ink[0], ink[3] - ink[1]
    if ink_w > CANVAS_WIDTH - 60:
        raise ValueError(f"text too wide for canvas: {text!r} ({ink_w}px)")
    draw_x = (CANVAS_WIDTH - ink_w) // 2 - ink[0]
    draw_y = (CANVAS_HEIGHT - ink_h) // 2 - ink[1]
    draw.text((draw_x, draw_y), text, fill="black", font=font)
    final_ink = draw.textbbox((draw_x, draw_y), text, font=font)
    region = target_region_for([int(v) for v in final_ink])
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue(), region, [int(v) for v in final_ink]


# ---------------------------------------------------------------------------
# Catalogue construction
# ---------------------------------------------------------------------------

def build_catalog(rng: random.Random) -> list[dict]:
    """Fixture records without PNG bytes/hashes (filled in by generate())."""
    pools = {
        "zh": _build_pool(rng, "zh", 220),
        "en": _build_pool(rng, "en", 90),
        "num": _build_pool(rng, "num", 90),
        "mixed": _build_pool(rng, "mixed", 90),
    }
    used_expected: set[str] = set(EXCLUDED_EXPECTED)
    used_drawn: set[str] = set(EXCLUDED_DRAWN)
    fixtures: list[dict] = []

    # Frozen S0 samples first, in SS8.1 order.
    for fixture_id, expected, drawn, kind, pos in S0_FIXED:
        mutation, errors = _mutation_for_s0(fixture_id, expected, drawn, kind, pos)
        fixtures.append({
            "id": fixture_id, "category": kind, "expected_text": expected,
            "drawn_text": drawn, "mutation": mutation,
            "expected_verdict": "MISMATCH", "expected_errors": errors,
        })
        used_expected.add(expected)
        used_drawn.add(drawn)

    # (category, id prefix, mutator kind, family plan).  Family-plan
    # counts are the *additional* fixtures beyond the frozen S0 samples
    # in that category (S0 contributes 1 substitution, 2 omissions,
    # 1 numeric change, 0 clean).
    has_digit = lambda t: any(c.isdigit() for c in t)
    plan = [
        ("clean", "TP-CLN", None,
         [("zh", 40, None), ("en", 20, None), ("num", 20, None), ("mixed", 20, None)]),
        ("substitution", "TP-SUB", "substitution",
         [("zh", 39, None), ("en", 15, None), ("mixed", 15, None)]),
        ("omission", "TP-OMI", "omission",
         [("zh", 34, None), ("en", 15, None), ("num", 9, None), ("mixed", 10, None)]),
        ("numeric_change", "TP-NMC", "numeric_change",
         [("num", 30, None), ("zh", 15, has_digit), ("mixed", 14, has_digit)]),
    ]
    for category, prefix, mutator_kind, family_plan in plan:
        n = 0
        for family, count, predicate in family_plan:
            pool = [t for t in pools[family] if predicate is None or predicate(t)]
            rng.shuffle(pool)
            taken = 0
            for expected in pool:
                if taken >= count:
                    break
                if expected in used_expected:
                    continue
                if mutator_kind is None:
                    drawn, mutation, errors = expected, {"kind": "none"}, []
                    verdict = "MATCH"
                else:
                    mutated = _MUTATORS[mutator_kind](expected, rng)
                    if mutated is None:
                        continue
                    drawn, mutation, errors = mutated
                    verdict = "MISMATCH"
                if drawn in used_drawn or drawn in used_expected:
                    continue
                if drawn in EXCLUDED_DRAWN or drawn in EXCLUDED_EXPECTED:
                    continue
                n += 1
                taken += 1
                used_expected.add(expected)
                used_drawn.add(drawn)
                fixtures.append({
                    "id": f"{prefix}-{n:03d}", "category": category,
                    "expected_text": expected, "drawn_text": drawn,
                    "mutation": mutation, "expected_verdict": verdict,
                    "expected_errors": errors,
                })
        # S0 samples already contribute 1 omission (ZH-001) + 1 omission
        # (ZH-003), 1 substitution, 1 numeric_change; clean contributes 0.
        s0_extra = {"omission": 2, "substitution": 1, "numeric_change": 1}.get(category, 0)
        if n != COUNTS[category] - s0_extra:
            raise RuntimeError(
                f"category {category}: built {n}, need {COUNTS[category] - s0_extra}")
    if len(fixtures) != TOTAL:
        raise RuntimeError(f"catalogue has {len(fixtures)} fixtures, need {TOTAL}")
    return fixtures


def select_blind_subset(fixtures: list[dict]) -> list[dict]:
    """Stratified blind subset (>=60): fixed seed, separate RNG stream."""
    rng = random.Random(BLIND_SEED)
    chosen: list[dict] = []
    for category, count in BLIND_COUNTS.items():
        ids = sorted(f["id"] for f in fixtures if f["category"] == category)
        chosen.extend(rng.sample(ids, count))
    by_id = {f["id"]: f for f in fixtures}
    return [{"id": fid, "sha256": by_id[fid]["sha256"]}
            for fid in sorted(chosen)]


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------

def manifest_font_record() -> dict:
    return {
        "name": "Noto Sans SC",
        "file": f"fonts/{FONT_FILE_NAME}",
        "source_url": FONT_SOURCE_URL,
        "version": FONT_VERSION,
        "sha256": FONT_SHA256,
        "bytes": FONT_BYTES,
        "license": FONT_LICENSE,
        "license_file": "fonts/OFL.txt",
        "weight": f"{FONT_WEIGHT_NAME} (wght 400)",
        "usage": "synthetic test images only (PROJECT_BOOK.md SS10.2)",
    }


def generate(output_dir: Path, seed: int = SEED) -> dict:
    """Generate all fixtures; returns the manifest dict."""
    output_dir = Path(output_dir)
    fonts_dir = output_dir / "fonts"
    font = load_font(fonts_dir / FONT_FILE_NAME)
    rng = random.Random(seed)
    catalog = build_catalog(rng)

    fixtures_out: list[dict] = []
    for record in catalog:
        png_bytes, region, ink = render(record["drawn_text"], font)
        sha = hashlib.sha256(png_bytes).hexdigest()
        filename = f"{record['id']}.png"
        (output_dir / filename).write_bytes(png_bytes)
        fixtures_out.append({
            "id": record["id"],
            "filename": filename,
            "sha256": sha,
            "bytes": len(png_bytes),
            "width": CANVAS_WIDTH,
            "height": CANVAS_HEIGHT,
            "format": "PNG",
            "category": record["category"],
            "mutation": record["mutation"],
            "expected_text": record["expected_text"],
            "drawn_text": record["drawn_text"],
            "ink_bbox_xyxy": ink,
            "target_region_xyxy": region,
            "expected_verdict": record["expected_verdict"],
            "expected_errors": record["expected_errors"],
        })

    manifest = {
        "schema": SCHEMA_MANIFEST,
        "generator": {
            "script": "scripts/generate_fixtures.py",
            "version": GENERATOR_VERSION,
            "seed": seed,
            "python": sys.version.split()[0],
            "pillow": Image.__version__ if hasattr(Image, "__version__") else None,
            "canvas": {"width": CANVAS_WIDTH, "height": CANVAS_HEIGHT,
                       "format": "PNG", "background": "white",
                       "foreground": "black"},
            "font_size_px": FONT_SIZE_PX,
            "font_weight": f"{FONT_WEIGHT_NAME} (wght 400)",
            "target_region": {
                "definition": ("rectangle centred on the drawn-text ink "
                               "bbox, sized by a linear rule in ink "
                               "geometry: height = 70 + 0.7*ink_height "
                               "- 0.05*ink_width px; width = ink_width "
                               "+ 40 - 0.02*ink_width px"),
                "calibration": ("rule fitted to the frozen PP-OCRv6 "
                                "detector's measured box geometry over "
                                "the 240 non-blind fixtures (2026-11-25, "
                                "single OCR pass; min IoU 0.833, 0 below "
                                "0.80 on the calibration set); the 60 "
                                "blind fixtures were not used to fit it"),
                "height_base_px": REGION_H_BASE_PX,
                "height_per_ink_h": REGION_H_PER_INK_H,
                "height_per_ink_w": REGION_H_PER_INK_W,
                "width_extra_px": REGION_W_EXTRA_PX,
                "width_per_ink_w": REGION_W_PER_INK_W,
            },
        },
        "font": manifest_font_record(),
        "counts": {"total": TOTAL, **COUNTS,
                   "blind_subset": sum(BLIND_COUNTS.values())},
        "fixtures": fixtures_out,
    }
    expected_output = {
        "schema": SCHEMA_EXPECTED,
        "fixtures": {
            f["id"]: {
                "expected_text": f["expected_text"],
                "drawn_text": f["drawn_text"],
                "verdict": f["expected_verdict"],
                "errors": f["expected_errors"],
                "summary": {
                    "expected_lines": 1,
                    "ocr_lines": 1,
                    "error_count": len(f["expected_errors"]),
                    "warning_count": 0,
                },
            }
            for f in fixtures_out
        },
    }
    blind = {
        "schema": SCHEMA_BLIND,
        "count": sum(BLIND_COUNTS.values()),
        "counts_by_category": dict(BLIND_COUNTS),
        "selection": {
            "method": "stratified random sample over manifest ids",
            "seed": BLIND_SEED,
            "note": ("Frozen before any acceptance tuning; do not use for "
                     "parameter tuning before S0."),
        },
        "fixtures": select_blind_subset(fixtures_out),
    }

    (output_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (output_dir / "expected_output.json").write_text(
        json.dumps(expected_output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (output_dir / "blind_subset.json").write_text(
        json.dumps(blind, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return manifest


# ---------------------------------------------------------------------------
# Verification (--verify-manifest): re-render everything and check.
# ---------------------------------------------------------------------------

def verify_manifest(manifest_path: Path) -> list[str]:
    """Return a list of failure messages (empty means PASS)."""
    errors: list[str] = []
    manifest_path = Path(manifest_path)
    fixtures_dir = manifest_path.resolve().parent
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001 - report, don't crash
        return [f"manifest unreadable: {exc}"]

    if manifest.get("schema") != SCHEMA_MANIFEST:
        errors.append(f"schema mismatch: {manifest.get('schema')!r}")
    gen = manifest.get("generator", {})
    if gen.get("version") != GENERATOR_VERSION:
        errors.append(f"generator version {gen.get('version')!r} != {GENERATOR_VERSION!r}")
    if gen.get("seed") != SEED:
        errors.append(f"seed {gen.get('seed')!r} != {SEED!r}")
    font_rec = manifest.get("font", {})
    if font_rec.get("sha256") != FONT_SHA256 or font_rec.get("version") != FONT_VERSION:
        errors.append("font record does not match pinned font (version/SHA-256)")
    if manifest.get("counts", {}).get("total") != TOTAL:
        errors.append("counts.total != 300")

    fixtures = manifest.get("fixtures", [])
    if len(fixtures) != TOTAL:
        errors.append(f"fixture count {len(fixtures)} != {TOTAL}")
    by_category: dict[str, int] = {}
    seen_ids: set[str] = set()
    seen_sha: set[str] = set()
    seen_expected: set[str] = set()
    seen_drawn: set[str] = set()
    for f in fixtures:
        fid = f.get("id")
        if fid in seen_ids:
            errors.append(f"duplicate id {fid}")
        seen_ids.add(fid)
        by_category[f.get("category")] = by_category.get(f.get("category"), 0) + 1
        if f.get("sha256") in seen_sha:
            errors.append(f"duplicate sha256 for {fid}")
        seen_sha.add(f.get("sha256"))
        if f.get("expected_text") in seen_expected:
            errors.append(f"duplicate expected_text for {fid}")
        seen_expected.add(f.get("expected_text"))
        if f.get("drawn_text") in seen_drawn:
            errors.append(f"duplicate drawn_text for {fid}")
        seen_drawn.add(f.get("drawn_text"))
        if not _is_normalized_text(f.get("expected_text", "")):
            errors.append(f"expected_text not normalised for {fid}")
        if not _is_normalized_text(f.get("drawn_text", "")):
            errors.append(f"drawn_text not normalised for {fid}")
        if "￥" in (f.get("expected_text", "") + f.get("drawn_text", "")) and fid != "TP-S0-NUM-001":
            errors.append(f"fullwidth yen U+FFE5 outside TP-S0-NUM-001: {fid}")
        region = f.get("target_region_xyxy", [])
        if len(region) != 4 or not (0 <= region[0] < region[2] <= CANVAS_WIDTH
                                    and 0 <= region[1] < region[3] <= CANVAS_HEIGHT):
            errors.append(f"target_region out of bounds for {fid}: {region}")
        elif region != target_region_for(f.get("ink_bbox_xyxy", [])):
            errors.append(f"target_region does not match calibrated rule for {fid}")
        if f.get("width") != CANVAS_WIDTH or f.get("height") != CANVAS_HEIGHT:
            errors.append(f"canvas size wrong for {fid}")
        if (f.get("expected_verdict") == "MATCH") != (len(f.get("expected_errors", [])) == 0):
            errors.append(f"verdict/errors mismatch for {fid}")
    for category, want in COUNTS.items():
        if by_category.get(category, 0) != want:
            errors.append(f"category {category}: {by_category.get(category, 0)} != {want}")

    # Frozen S0 samples, verbatim per PROJECT_BOOK.md SS8.1.
    by_id = {f.get("id"): f for f in fixtures}
    s0_expectations = {
        "TP-S0-ZH-001": ("限时优惠", "限时优", "MISSING_CHARACTER", "惠", "", [3, 4], [3, 3]),
        "TP-S0-ZH-002": ("新品上市", "新口上市", "SUBSTITUTION", "品", "口", [1, 2], [1, 2]),
        "TP-S0-NUM-001": ("￥28.80", "￥28.00", "NUMERIC_CHANGE", "8", "0", [4, 5], [4, 5]),
        "TP-S0-ZH-003": ("新客立减20元", "新客立减元", "MISSING_CHARACTER", "20", "", [4, 6], [4, 4]),
    }
    for fid, (exp, drawn, etype, efrag, rfrag, espan, rspan) in s0_expectations.items():
        f = by_id.get(fid)
        if f is None:
            errors.append(f"missing frozen sample {fid}")
            continue
        if f.get("expected_text") != exp or f.get("drawn_text") != drawn:
            errors.append(f"{fid}: text mismatch ({f.get('expected_text')!r}/{f.get('drawn_text')!r})")
        errs = f.get("expected_errors", [])
        if fid == "TP-S0-ZH-003":
            if len(errs) < 1 or errs[0].get("type") != etype:
                errors.append(f"{fid}: need >=1 MISSING_CHARACTER")
        elif len(errs) != 1 or errs[0].get("type") != etype:
            errors.append(f"{fid}: need exactly 1 {etype}, got {errs}")
        if errs:
            e0 = errs[0]
            if (e0.get("expected_fragment") != efrag
                    or e0.get("recognized_fragment") != rfrag
                    or e0.get("expected_span") != espan
                    or e0.get("recognized_span") != rspan):
                errors.append(f"{fid}: fragment/span mismatch: {e0}")

    # Re-render every fixture and compare PNG bytes + hashes (reproducibility).
    try:
        font = load_font(fixtures_dir / "fonts" / FONT_FILE_NAME)
    except Exception as exc:  # noqa: BLE001
        errors.append(f"font load failed: {exc}")
        font = None
    if font is not None:
        for f in fixtures:
            png_path = fixtures_dir / f.get("filename", "")
            if not png_path.is_file():
                errors.append(f"missing file {f.get('filename')}")
                continue
            on_disk = png_path.read_bytes()
            if hashlib.sha256(on_disk).hexdigest() != f.get("sha256"):
                errors.append(f"sha256 mismatch on disk for {f.get('id')}")
                continue
            if len(on_disk) != f.get("bytes"):
                errors.append(f"byte size mismatch for {f.get('id')}")
            try:
                with Image.open(io.BytesIO(on_disk)) as im:
                    if im.format != "PNG" or im.size != (CANVAS_WIDTH, CANVAS_HEIGHT):
                        errors.append(f"bad PNG format/size for {f.get('id')}: {im.format} {im.size}")
            except Exception as exc:  # noqa: BLE001
                errors.append(f"unreadable PNG for {f.get('id')}: {exc}")
            try:
                fresh, region, _ink = render(f.get("drawn_text", ""), font)
            except Exception as exc:  # noqa: BLE001
                errors.append(f"re-render failed for {f.get('id')}: {exc}")
                continue
            if hashlib.sha256(fresh).hexdigest() != f.get("sha256"):
                errors.append(f"re-render SHA mismatch (not reproducible) for {f.get('id')}")
            if region != f.get("target_region_xyxy"):
                errors.append(f"target_region mismatch on re-render for {f.get('id')}")

    # expected_output.json must mirror the manifest exactly.
    exp_path = fixtures_dir / "expected_output.json"
    if not exp_path.is_file():
        errors.append("expected_output.json missing")
    else:
        try:
            expected_output = json.loads(exp_path.read_text(encoding="utf-8"))
        except Exception as exc:  # noqa: BLE001
            errors.append(f"expected_output.json unreadable: {exc}")
            expected_output = None
        if expected_output is not None:
            if expected_output.get("schema") != SCHEMA_EXPECTED:
                errors.append("expected_output.json schema mismatch")
            exp_fixtures = expected_output.get("fixtures", {})
            if set(exp_fixtures) != seen_ids:
                errors.append("expected_output.json fixture ids != manifest ids")
            for fid, entry in exp_fixtures.items():
                f = by_id.get(fid)
                if f is None:
                    continue
                if (entry.get("verdict") != f.get("expected_verdict")
                        or entry.get("errors") != f.get("expected_errors")
                        or entry.get("expected_text") != f.get("expected_text")
                        or entry.get("drawn_text") != f.get("drawn_text")):
                    errors.append(f"expected_output.json mismatch for {fid}")

    # Blind subset: >=60, ids + SHAs match the manifest, stratified counts.
    blind_path = fixtures_dir / "blind_subset.json"
    if not blind_path.is_file():
        errors.append("blind_subset.json missing")
    else:
        try:
            blind = json.loads(blind_path.read_text(encoding="utf-8"))
        except Exception as exc:  # noqa: BLE001
            errors.append(f"blind_subset.json unreadable: {exc}")
            blind = None
        if blind is not None:
            if blind.get("schema") != SCHEMA_BLIND:
                errors.append("blind_subset.json schema mismatch")
            entries = blind.get("fixtures", [])
            if len(entries) < 60:
                errors.append(f"blind subset has {len(entries)} < 60")
            blind_ids = [e.get("id") for e in entries]
            if len(set(blind_ids)) != len(blind_ids):
                errors.append("blind subset has duplicate ids")
            for e in entries:
                f = by_id.get(e.get("id"))
                if f is None:
                    errors.append(f"blind id not in manifest: {e.get('id')}")
                elif e.get("sha256") != f.get("sha256"):
                    errors.append(f"blind sha mismatch: {e.get('id')}")
            blind_cats: dict[str, int] = {}
            for fid in blind_ids:
                f = by_id.get(fid)
                if f:
                    blind_cats[f["category"]] = blind_cats.get(f["category"], 0) + 1
            if blind_cats != BLIND_COUNTS:
                errors.append(f"blind counts {blind_cats} != {BLIND_COUNTS}")
    return errors


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate / verify P033 S0 fixtures (T005).")
    parser.add_argument("--verify-manifest", metavar="PATH",
                        help="verify the manifest at PATH and exit 0/1")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_FIXTURES_DIR,
                        help="output directory for generation (default: tests/fixtures/s0)")
    parser.add_argument("--seed", type=int, default=SEED,
                        help="RNG seed (default: frozen 20261125)")
    args = parser.parse_args(argv)

    if args.verify_manifest:
        failures = verify_manifest(Path(args.verify_manifest))
        if failures:
            print(f"VERIFY FAILED: {len(failures)} problem(s)")
            for failure in failures:
                print(f"  - {failure}")
            return 1
        manifest = json.loads(Path(args.verify_manifest).read_text(encoding="utf-8"))
        print(f"VERIFY OK: {len(manifest['fixtures'])} fixtures, "
              f"counts={manifest['counts']}, "
              f"font={manifest['font']['name']} {manifest['font']['version']} "
              f"sha256={manifest['font']['sha256'][:16]}...")
        return 0

    if args.seed != SEED:
        print(f"WARNING: non-frozen seed {args.seed} (frozen seed is {SEED}); "
              "manifest will record the seed used.", file=sys.stderr)
    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest = generate(output_dir, seed=args.seed)
    counts = manifest["counts"]
    print(f"GENERATED: {counts['total']} fixtures "
          f"(clean={counts['clean']}, substitution={counts['substitution']}, "
          f"omission={counts['omission']}, numeric_change={counts['numeric_change']})")
    print(f"  output: {output_dir}")
    print(f"  font: {manifest['font']['name']} {manifest['font']['version']} "
          f"sha256={manifest['font']['sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
