"""Golden tests: §4.3 normalisation (PROJECT_BOOK.md).

Every rule is tested against a fixed literal, not against a second
implementation of the same rule.
"""

from textproof.core.normalize import (
    normalize_line,
    normalize_lines,
    normalize_text,
    split_normalized_lines,
)


def test_nfc_composes_combining_marks():
    # e + COMBINING ACUTE (2 code points) -> é (1 code point).
    decomposed = "e" + chr(0x301)
    assert len(decomposed) == 2
    composed = normalize_line(decomposed)
    assert composed == chr(0xE9)
    assert len(composed) == 1


def test_crlf_and_cr_unified_to_lf():
    assert normalize_text("a\r\nb\rc") == "a\nb\nc"
    assert split_normalized_lines("a\r\nb\rc") == ("a", "b", "c")


def test_fullwidth_ascii_mapped_to_halfwidth():
    assert normalize_line("ＡＢＣ１２３ａｂｃ！＠＃") == "ABC123abc!@#"
    assert normalize_line("Ｈｅｌｌｏ，世界") == "Hello,世界"


def test_fullwidth_space_mapped_to_space():
    assert normalize_line("ａ\u3000ｂ") == "a b"
    assert normalize_line("\u3000\u3000x\u3000") == "x"


def test_fullwidth_yen_sign_is_not_ascii_and_is_kept():
    # U+FFE5 is not in the U+FF01-U+FF5E ASCII range: §4.3 maps
    # full-width *ASCII* only, so ￥ stays ￥ (both sides agree).
    assert normalize_line("￥２８．８０") == "￥28.80"


def test_leading_trailing_whitespace_stripped_per_line():
    assert normalize_line("  hello world  ") == "hello world"
    assert normalize_line("\tTabbed\t") == "Tabbed"


def test_consecutive_horizontal_whitespace_folded_to_one_space():
    assert normalize_line("a   b\t\tc") == "a b c"
    assert normalize_line("a\u00a0\u00a0b") == "a b"


def test_case_is_preserved_case_sensitive():
    assert normalize_line("Hello WORLD") == "Hello WORLD"
    assert normalize_line("ＡｂＣ") == "AbC"


def test_punctuation_is_kept():
    # ，(U+FF0C) and ！(U+FF01) ARE full-width ASCII, so §4.3.3 maps
    # them to , and !; 。(U+3002) is outside the ASCII range and stays.
    assert normalize_line("你好，世界！") == "你好,世界!"
    assert normalize_line("你好。世界") == "你好。世界"
    assert normalize_line("a,b.c;d:e") == "a,b.c;d:e"


def test_blank_line_stays_blank_not_dropped():
    assert split_normalized_lines("a\n\nb") == ("a", "", "b")
    assert normalize_lines(["  ", "x"]) == ("", "x")


def test_normalize_text_keeps_line_structure():
    assert normalize_text("  ＡＢＣ  \r\n\tｄｅｆ\t") == "ABC\ndef"


def test_empty_string_normalises_to_empty():
    assert normalize_text("") == ""
    assert split_normalized_lines("") == ("",)
