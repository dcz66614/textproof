"""Unit tests for T002: input contracts + image loader.

Acceptance mapping (IMPLEMENTATION_PLAN.md T002 card):

1. PNG/JPEG/WebP only, magic-byte checked, extension-independent --
   ``test_*_accepted``, ``test_*_rejected``, ``test_*_disguise*``.
2. 25 MiB / 8192 px / 40 MP boundaries, positive and negative --
   ``test_file_size_*``, ``test_*dimension*``, ``test_pixels_*``.
3. Animated WebP, corrupt files, extension disguise, over-pixel and
   decode failures fail closed -- ``test_animated_*``,
   ``test_truncated_*``, ``test_*_rejected``.
4. EXIF orientation applied, oriented width/height, §5 coordinate
   basis -- ``test_exif_orientation_*``, ``test_report_fields_*``.
5. Expected text 5,000 code points / 100 lines boundaries; blank
   rejected -- ``test_expected_text_*``.
6. No absolute path, EXIF UserComment or GPS in any output --
   ``test_privacy_*``, ``test_error_messages_contain_no_paths``,
   ``test_loader_takes_bytes_only``.

All test images are synthetic, generated in-memory with Pillow.
No real user images, no network images, no network access.
"""

from __future__ import annotations

import hashlib
import inspect

import pytest
from PIL import Image
from PIL.PngImagePlugin import PngInfo

from textproof.contracts import (
    COORDINATE_SYSTEM,
    ERROR_CODE_INVALID_INPUT,
    MAX_DIMENSION_PX,
    MAX_EXPECTED_CODEPOINTS,
    MAX_EXPECTED_LINES,
    MAX_FILE_SIZE_BYTES,
    MAX_PIXELS,
    SCHEMA_ID,
    InvalidInputError,
)
from textproof.io.image_loader import detect_format, load_image, validate_expected_text


# ---------------------------------------------------------------------------
# Synthetic image builders (in-memory only)
# ---------------------------------------------------------------------------


def _png_bytes(size=(64, 48), color="white", mode="RGB", **kwargs) -> bytes:
    from io import BytesIO

    img = Image.new(mode, size, color)
    buf = BytesIO()
    img.save(buf, "PNG", **kwargs)
    return buf.getvalue()


def _jpeg_bytes(size=(64, 48), color="white", exif=None) -> bytes:
    from io import BytesIO

    img = Image.new("RGB", size, color)
    buf = BytesIO()
    kwargs = {"format": "JPEG"}
    if exif is not None:
        kwargs["exif"] = exif
    img.save(buf, **kwargs)
    return buf.getvalue()


def _webp_bytes(size=(64, 48), color="white", mode="RGB", **kwargs) -> bytes:
    from io import BytesIO

    img = Image.new(mode, size, color)
    buf = BytesIO()
    img.save(buf, "WEBP", **kwargs)
    return buf.getvalue()


def _exif_with_orientation(value: int) -> Image.Exif:
    exif = Image.Exif()
    exif[274] = value
    return exif


def _assert_invalid(data_or_text, func, reason=None):
    """Assert *func* fails closed with the unified INVALID_INPUT code."""
    with pytest.raises(InvalidInputError) as excinfo:
        func(data_or_text)
    err = excinfo.value
    assert err.code == ERROR_CODE_INVALID_INPUT == "INVALID_INPUT"
    assert isinstance(err, ValueError)
    if reason is not None:
        assert err.reason == reason
    return err


# ---------------------------------------------------------------------------
# 0. Frozen limits are pinned here so any drift fails loudly.
# ---------------------------------------------------------------------------


def test_frozen_limits_match_project_book_4_2():
    assert MAX_FILE_SIZE_BYTES == 25 * 1024 * 1024
    assert MAX_DIMENSION_PX == 8192
    assert MAX_PIXELS == 40_000_000
    assert MAX_EXPECTED_CODEPOINTS == 5_000
    assert MAX_EXPECTED_LINES == 100
    assert SCHEMA_ID == "textproof.report/v1"
    assert COORDINATE_SYSTEM == "oriented_image_px_top_left"


# ---------------------------------------------------------------------------
# 1. Accepted formats, magic-byte detection, extension independence.
#    (The loader takes bytes only, so "extension" can never influence it;
#    these tests prove acceptance is decided by magic bytes + content.)
# ---------------------------------------------------------------------------


def test_png_accepted():
    data = _png_bytes((120, 80))
    assert detect_format(data) == "PNG"
    img = load_image(data)
    assert img.format == "PNG"
    assert img.mime == "image/png"
    assert (img.width, img.height) == (120, 80)
    assert img.oriented is False
    assert img.data == data
    assert img.sha256_hex() == hashlib.sha256(data).hexdigest()
    assert img.pil_image.size == (120, 80)


def test_jpeg_accepted():
    data = _jpeg_bytes((120, 80))
    assert detect_format(data) == "JPEG"
    img = load_image(data)
    assert img.format == "JPEG"
    assert img.mime == "image/jpeg"
    assert (img.width, img.height) == (120, 80)
    assert img.oriented is False


def test_webp_accepted():
    data = _webp_bytes((120, 80))
    assert detect_format(data) == "WEBP"
    img = load_image(data)
    assert img.format == "WEBP"
    assert img.mime == "image/webp"
    assert (img.width, img.height) == (120, 80)
    assert img.oriented is False


def test_webp_lossless_and_rgba_accepted():
    assert load_image(_webp_bytes((32, 32), mode="RGBA", lossless=True)).format == "WEBP"
    assert load_image(_webp_bytes((32, 32), mode="RGBA")).format == "WEBP"


def test_magic_detection_ignores_would_be_extension():
    # Same PNG bytes would be "a .jpg file" to a name-based checker;
    # the loader has no name input, so magic alone decides.
    data = _png_bytes()
    assert detect_format(data) == "PNG"
    assert load_image(data).format == "PNG"


# ---------------------------------------------------------------------------
# 1b. Unsupported / corrupt input fails closed.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "data",
    [
        b"",
        b"not an image at all",
        b"GIF89a" + b"\x00" * 100,  # GIF is not accepted
        b"\x89PNG\r\n\x1a\n" + b"\x00" * 10,  # PNG magic, no valid chunks
        b"\xff\xd8\xff" + b"\x00" * 10,  # JPEG magic, no valid segments
        bytes(range(256)),
    ],
)
def test_unsupported_or_garbage_bytes_rejected(data):
    _assert_invalid(data, load_image)


def test_non_bytes_input_rejected():
    for bad in (None, 123, "image.png", ["bytes"]):
        _assert_invalid(bad, load_image)


def test_truncated_png_rejected():
    data = _png_bytes((64, 64))
    _assert_invalid(data[: len(data) // 2], load_image, reason="decode_failed")


def test_truncated_jpeg_rejected():
    data = _jpeg_bytes((64, 64))
    _assert_invalid(data[: len(data) // 2], load_image, reason="decode_failed")


def test_truncated_webp_rejected():
    data = _webp_bytes((64, 64))
    _assert_invalid(data[: len(data) // 2], load_image)


def test_magic_content_mismatch_rejected():
    # PNG magic bytes glued onto JPEG content: magic says PNG, the
    # decoder cannot read it as PNG -> rejected, not mis-accepted.
    jpeg = _jpeg_bytes((32, 32))
    spoofed = b"\x89PNG\r\n\x1a\n" + jpeg[8:]
    assert detect_format(spoofed) == "PNG"
    _assert_invalid(spoofed, load_image)

    # JPEG magic glued onto PNG content.
    png = _png_bytes((32, 32))
    spoofed2 = b"\xff\xd8\xff" + png[3:]
    assert detect_format(spoofed2) == "JPEG"
    _assert_invalid(spoofed2, load_image)


# ---------------------------------------------------------------------------
# 2. Size / dimension / pixel boundaries: positive and negative each.
# ---------------------------------------------------------------------------


def test_file_size_exactly_25_mib_accepted():
    # Exact boundary: a valid small PNG padded with trailing NUL bytes
    # to exactly MAX_FILE_SIZE_BYTES.  Pillow tolerates trailing bytes
    # after IEND; the loader's size check is on len(data), so this
    # exercises the boundary precisely.
    data = _png_bytes((16, 16))
    padded = data + b"\x00" * (MAX_FILE_SIZE_BYTES - len(data))
    assert len(padded) == MAX_FILE_SIZE_BYTES
    img = load_image(padded)
    assert img.format == "PNG"
    assert (img.width, img.height) == (16, 16)


def test_file_size_25_mib_plus_1_rejected():
    data = _png_bytes((16, 16))
    padded = data + b"\x00" * (MAX_FILE_SIZE_BYTES - len(data) + 1)
    assert len(padded) == MAX_FILE_SIZE_BYTES + 1
    _assert_invalid(padded, load_image, reason="file_too_large")


def test_width_8192_accepted():
    img = load_image(_png_bytes((8192, 1)))
    assert (img.width, img.height) == (8192, 1)


def test_width_8193_rejected():
    _assert_invalid(
        _png_bytes((8193, 1)), load_image, reason="image_dimension_exceeded"
    )


def test_height_8192_accepted():
    img = load_image(_png_bytes((1, 8192)))
    assert (img.width, img.height) == (1, 8192)


def test_height_8193_rejected():
    _assert_invalid(
        _png_bytes((1, 8193)), load_image, reason="image_dimension_exceeded"
    )


def test_pixels_exactly_40m_accepted():
    # 8000 x 5000 = 40,000,000 px, both dimensions <= 8192.
    # Mode "L" keeps the in-memory image at 40 MB.
    img = load_image(_png_bytes((8000, 5000), color=128, mode="L"))
    assert (img.width, img.height) == (8000, 5000)
    assert img.width * img.height == MAX_PIXELS


def test_pixels_over_40m_rejected():
    # 8000 x 5001 = 40,008,000 px > 40,000,000, dimensions in range,
    # so the rejection must come from the pixel-count rule alone.
    _assert_invalid(
        _png_bytes((8000, 5001), color=128, mode="L"),
        load_image,
        reason="too_many_pixels",
    )


# ---------------------------------------------------------------------------
# 3. Animated WebP and decode failures fail closed.
# ---------------------------------------------------------------------------


def test_animated_webp_rejected():
    from io import BytesIO

    f1 = Image.new("RGB", (32, 32), "red")
    f2 = Image.new("RGB", (32, 32), "blue")
    buf = BytesIO()
    f1.save(buf, "WEBP", save_all=True, append_images=[f2], duration=100, loop=0)
    data = buf.getvalue()
    assert detect_format(data) == "WEBP"
    _assert_invalid(data, load_image, reason="animated_webp")


def test_animated_webp_vp8x_flag_rejected_even_with_one_frame():
    # Take a static extended (RGBA) WebP, which carries a VP8X chunk,
    # and set only the VP8X animation bit.  The raw-byte check must
    # reject it before any decoder runs.
    # Semi-transparent pixels force the extended (VP8X) form.
    data = _webp_bytes((32, 32), color=(255, 0, 0, 128), mode="RGBA")
    idx = data.find(b"VP8X")
    assert idx >= 0
    tampered = bytearray(data)
    tampered[idx + 8] |= 0x02  # VP8X animation flag
    _assert_invalid(bytes(tampered), load_image, reason="animated_webp")


def test_static_webp_with_vp8x_but_no_animation_flag_accepted():
    # The RGBA WebP above has a VP8X chunk (alpha flag 0x10) without
    # the animation bit: it must stay accepted.
    data = _webp_bytes((32, 32), color=(255, 0, 0, 128), mode="RGBA")
    idx = data.find(b"VP8X")
    assert idx >= 0
    assert not (data[idx + 8] & 0x02)
    assert load_image(data).format == "WEBP"


# ---------------------------------------------------------------------------
# 4. EXIF orientation: oriented dimensions, oriented flag, §5 basis.
# ---------------------------------------------------------------------------


def test_exif_orientation_6_swaps_dimensions():
    # 100x50 stored, orientation 6 (rotate 90 CW) -> displayed 50x100.
    data = _jpeg_bytes((100, 50), exif=_exif_with_orientation(6))
    img = load_image(data)
    assert img.oriented is True
    assert (img.width, img.height) == (50, 100)
    assert img.pil_image.size == (50, 100)


def test_exif_orientation_8_swaps_dimensions():
    data = _jpeg_bytes((100, 50), exif=_exif_with_orientation(8))
    img = load_image(data)
    assert img.oriented is True
    assert (img.width, img.height) == (50, 100)


def test_exif_orientation_3_keeps_dimensions_but_marks_oriented():
    data = _jpeg_bytes((100, 50), exif=_exif_with_orientation(3))
    img = load_image(data)
    assert img.oriented is True
    assert (img.width, img.height) == (100, 50)


def test_exif_orientation_1_not_oriented():
    data = _jpeg_bytes((100, 50), exif=_exif_with_orientation(1))
    img = load_image(data)
    assert img.oriented is False
    assert (img.width, img.height) == (100, 50)


def test_no_exif_not_oriented():
    img = load_image(_jpeg_bytes((100, 50)))
    assert img.oriented is False
    assert (img.width, img.height) == (100, 50)


def test_exif_orientation_png():
    # PNG eXIf chunk carrying orientation 6.
    data = _png_bytes((100, 50), exif=_exif_with_orientation(6))
    img = load_image(data)
    assert img.oriented is True
    assert (img.width, img.height) == (50, 100)


def test_report_fields_use_oriented_frame_and_section_5_basis():
    data = _jpeg_bytes((100, 50), exif=_exif_with_orientation(6))
    img = load_image(data)
    fields = img.image_report_fields()
    assert fields == {
        "format": "JPEG",
        "width": 50,
        "height": 100,
        "coordinate_system": "oriented_image_px_top_left",
    }


# ---------------------------------------------------------------------------
# 5. Expected text boundaries (5,000 code points / 100 lines; blank out).
# ---------------------------------------------------------------------------


def test_expected_text_simple_lines():
    out = validate_expected_text("限时优惠\n新品上市")
    assert out.raw == "限时优惠\n新品上市"
    assert out.normalized_lines == ("限时优惠", "新品上市")
    assert out.codepoint_count == 9
    assert out.line_count == 2


def test_expected_text_crlf_and_cr_unified_to_lines():
    out = validate_expected_text("a\r\nb\rc")
    assert out.normalized_lines == ("a", "b", "c")
    assert out.line_count == 3


def test_expected_text_exactly_5000_codepoints_accepted():
    text = "限" * 2500 + "a" * 2500  # 5,000 code points, mixed scripts
    assert len(text) == 5_000
    out = validate_expected_text(text)
    assert out.codepoint_count == 5_000


def test_expected_text_5001_codepoints_rejected():
    _assert_invalid(
        "a" * 5_001, validate_expected_text, reason="expected_text_too_long"
    )


def test_expected_text_exactly_100_lines_accepted():
    text = "\n".join(f"line{i}" for i in range(100))
    out = validate_expected_text(text)
    assert out.line_count == 100


def test_expected_text_101_lines_rejected():
    text = "\n".join(f"line{i}" for i in range(101))
    _assert_invalid(
        text, validate_expected_text, reason="expected_text_too_many_lines"
    )


@pytest.mark.parametrize("blank", ["", "   ", "\n\n", "\t \r\n  ", "　　"])
def test_expected_text_blank_rejected(blank):
    _assert_invalid(blank, validate_expected_text, reason="expected_text_empty")


def test_expected_text_non_string_rejected():
    for bad in (None, 123, b"bytes", ["a"]):
        _assert_invalid(
            bad, validate_expected_text, reason="expected_text_not_string"
        )


def test_expected_text_lone_surrogate_rejected():
    _assert_invalid(
        "a\ud800b",
        validate_expected_text,
        reason="expected_text_invalid_unicode",
    )


# ---------------------------------------------------------------------------
# 6. Privacy: no paths, no EXIF UserComment, no GPS anywhere in output.
# ---------------------------------------------------------------------------


def test_privacy_exif_comment_and_gps_not_exposed():
    exif = Image.Exif()
    exif[274] = 1
    exif[0x9286] = b"SECRET_USER_COMMENT"  # EXIF UserComment
    exif[0x8825] = {  # GPS IFD: lat 25N, lon 121E
        0: b"\x02\x03\x00\x00",
        1: "N",
        2: (25.0, 3.0, 0.0),
        3: "E",
        4: (121.0, 33.0, 0.0),
    }
    data = _jpeg_bytes((64, 48), exif=exif)
    img = load_image(data)
    # The load still succeeds (orientation was readable) ...
    assert img.format == "JPEG"
    # ... but no output carries the comment, the GPS values, or any
    # EXIF blob: repr, report fields, and the stripped decoded image.
    assert "SECRET_USER_COMMENT" not in repr(img)
    assert "SECRET_USER_COMMENT" not in str(img.image_report_fields())
    stripped_exif = img.pil_image.getexif()
    assert 0x9286 not in stripped_exif
    assert 0x8825 not in stripped_exif
    assert len(stripped_exif) == 0
    assert "exif" not in img.pil_image.info


def test_privacy_png_text_chunk_not_exposed():
    from io import BytesIO

    info = PngInfo()
    info.add_text("Comment", "SECRET_PNG_COMMENT")
    img = Image.new("RGB", (32, 32), "white")
    buf = BytesIO()
    img.save(buf, "PNG", pnginfo=info)
    loaded = load_image(buf.getvalue())
    assert "SECRET_PNG_COMMENT" not in repr(loaded)
    assert "SECRET_PNG_COMMENT" not in str(loaded.image_report_fields())
    assert "Comment" not in loaded.pil_image.info
    assert not getattr(loaded.pil_image, "text", None)


def test_error_messages_contain_no_paths_or_user_text():
    err = _assert_invalid(b"garbage", load_image)
    assert "/" not in str(err)
    assert "home" not in str(err).lower()
    err2 = _assert_invalid("a" * 5_001, validate_expected_text)
    assert "a" * 10 not in str(err2)  # user text never echoed


def test_loader_takes_bytes_only():
    # No path parameter exists, so there is no arbitrary-path read or
    # write surface by construction (PROJECT_BOOK.md §9).
    params = inspect.signature(load_image).parameters
    assert list(params) == ["data"]
    assert "path" not in params and "filename" not in params
    params2 = inspect.signature(validate_expected_text).parameters
    assert list(params2) == ["text"]


def test_all_rejections_share_the_unified_code():
    bad_inputs = [
        b"",
        b"GIF89a" + b"\x00" * 20,
        _png_bytes((8193, 1)),
        _png_bytes((8000, 5001), color=128, mode="L"),
    ]
    for bad in bad_inputs:
        with pytest.raises(InvalidInputError) as excinfo:
            load_image(bad)
        assert excinfo.value.code == "INVALID_INPUT"
        assert str(excinfo.value).startswith("INVALID_INPUT: ")
