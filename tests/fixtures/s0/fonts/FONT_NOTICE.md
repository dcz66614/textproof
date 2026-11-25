# Font notice — Noto Sans SC (tests/fixtures/s0/fonts/)

Test-image font for the P033 TextProof S0 fixtures (T005).
Used **only** to render synthetic test images; never shipped as a
product asset and never used for any other purpose
(PROJECT_BOOK.md §10.2).

| Item | Value |
|---|---|
| Font | Noto Sans SC (variable font, `wght` axis) |
| File in this directory | `NotoSansSC[wght].ttf` (17,772,300 bytes) |
| Source (official) | https://github.com/google/fonts/raw/main/ofl/notosanssc/NotoSansSC%5Bwght%5D.ttf (Google Fonts repository, `ofl/notosanssc`) |
| Version (name table, ID 5) | 2.004-H2 (`Version 2.004-H2;hotconv 1.0.118;makeotfexe 2.5.65603`) |
| SHA-256 | `a3041811a78c361b1de50f953c805e0244951c21c5bd412f7232ef0d899af0da` |
| Licence | SIL Open Font License, Version 1.1 (OFL-1.1) — full text in `OFL.txt` in this directory (SHA-256 `1c05c68c34f9708415aada51f17e1b0092d2cea709bf4a94cd38114f9e73d7d9`) |
| Rendering used by the generator | Named instance `Regular` (wght 400), 64 px, black on white, 1200×480 PNG |
| Downloaded | 2026-11-25, once, at build time (no network access at generation or test time) |

Notes:

- The variable font's default instance is Thin (wght 100); the
  generator explicitly selects the `Regular` named instance
  (`set_variation_by_name("Regular")`) and asserts it, so the weight
  is pinned and reproducible.
- The generator (`scripts/generate_fixtures.py`) verifies this file's
  SHA-256 and byte size on every run and refuses to generate or verify
  if either differs.
- The OFL requires the licence text to accompany redistribution; it is
  kept here next to the font file. The font's Reserved Font Name and
  copyright notices are unchanged (the file is byte-identical to the
  upstream download).
- T014 (SBOM / licence report) re-verifies this record before any
  public release.
