# THIRD_PARTY_NOTICES.md — TextProof (P033)

TextProof's own source code is MIT (see `LICENSE`, to be added by T014 if
not yet present). MIT applies **only** to TextProof's own code. It does not
cover dependencies, OCR models, dictionaries, or fonts. This file records
every third-party asset used by T003, with source URL, version, SHA-256,
and licence status. Model copyright is **not** claimed as TextProof's own.

## 1. RapidOCR source code

| Item | Value |
|---|---|
| Project | RapidOCR — https://github.com/RapidAI/RapidOCR |
| Version used | 3.10.0 (PyPI package `rapidocr==3.10.0`, released 2026-10-08) |
| Licence | Apache License, Version 2.0 (Apache-2.0) |
| Licence source | RapidOCR project `LICENSE` file; docs: https://rapidai.github.io/RapidOCRDocs/latest/en/model_licenses/ §1 |
| Copyright | RapidOCR Authors |

Install/usage docs consulted (2026-11-25):

- https://rapidai.github.io/RapidOCRDocs/main/en/install_usage/rapidocr/install/
- https://rapidai.github.io/RapidOCRDocs/main/en/install_usage/rapidocr/usage/
- https://rapidai.github.io/RapidOCRDocs/latest/en/model_licenses/

Note (T001, retained): the legacy PyPI package `rapidocr-onnxruntime`
stops at 1.4.4 and has no 3.10.0 release; the frozen version is satisfied by
the `rapidocr` package only. `rapidocr` does not declare `onnxruntime` as a
dependency, so the CPU engine is installed explicitly (see §3).

## 2. OCR models (frozen route, PROJECT_BOOK.md §6.2)

Default model route confirmed against the installed `rapidocr` 3.10.0
package (`config.yaml` defaults + `default_models.yaml` routing) and the
official model licence page §6, which lists exactly these three artifacts
as the default ONNX Runtime configuration:

- Detection: PP-OCRv6 `small` (`multi_PP-OCRv6_det_small`)
- Recognition: PP-OCRv6 `small` (`multi_PP-OCRv6_rec_small`)
- Direction classification: PP-OCRv4 `mobile`
  (`ch_ppocr_mobile_v2.0_cls_mobile`)

| File (`assets/ocr/models/`) | Upstream model | Registry model_key | Source URL | SHA-256 | Licence |
|---|---|---|---|---|---|
| `PP-OCRv6_det_small.onnx` (9,929,594 B) | `PP-OCRv6_small_det` | `multi_PP-OCRv6_det_small` | https://www.modelscope.cn/models/RapidAI/RapidOCR/resolve/v3.10.0/onnx/PP-OCRv6/det/PP-OCRv6_det_small.onnx | `090f04abcd9d9a7498bc4ebf677e4cb9bdce1fe4197ddb7e529f1ef44e1ff94f` | Apache-2.0 |
| `PP-OCRv6_rec_small.onnx` (21,234,383 B) | `PP-OCRv6_small_rec` | `multi_PP-OCRv6_rec_small` | https://www.modelscope.cn/models/RapidAI/RapidOCR/resolve/v3.10.0/onnx/PP-OCRv6/rec/PP-OCRv6_rec_small.onnx | `6f327246b50388f3c176ae304bd95767ea6dc0c9ae92153ef8cbe210b3c14884` | Apache-2.0 |
| `ch_ppocr_mobile_v2.0_cls_mobile.onnx` (585,532 B) | `ch_ppocr_mobile_v2.0_cls` | `ch_ppocr_mobile_v2.0_cls_mobile` | https://www.modelscope.cn/models/RapidAI/RapidOCR/resolve/v3.10.0/onnx/PP-OCRv4/cls/ch_ppocr_mobile_v2.0_cls_mobile.onnx | `e47acedf663230f8863ff1ab0e64dd2d82b838fceb5957146dab185a89d6215c` | Apache-2.0 |

Licence basis: RapidOCR official model licence statement
(https://rapidai.github.io/RapidOCRDocs/latest/en/model_licenses/):
“All models registered in `rapidocr/default_models.yaml` are licensed
under the Apache License, Version 2.0 (`Apache-2.0`), without exception.”
(§4). Upstream model weights are copyright Baidu and/or the applicable
PaddleOCR rights holders; RapidOCR does not claim ownership (§1, §5).
PaddleOCR itself is Apache-2.0
(https://github.com/PaddlePaddle/PaddleOCR/blob/main/LICENSE).
Redistribution must follow Apache-2.0 §4 (include the licence text, retain
attribution notices, mark modified files). The licence text is reproduced
in the RapidOCR/PaddleOCR distributions; TextProof ships the model files
unmodified, so no modification notice is due for them.

All three SHA-256 values above were verified locally (2026-11-25) against
both the `rapidocr` 3.10.0 registry (`default_models.yaml`) and the
official licence page §6 table. See `assets/ocr/SHA256SUMS.txt`.

Wheel copies (T013-U01): the wheel ships verbatim copies of the same
three files as package data (`textproof/assets/ocr/models/`), so an
installed `textproof` can run OCR with no source checkout. The copies
are byte-identical to the checkout files above (same SHA-256, verified
by the adapter at start-up whichever copy it uses); `assets/ocr/models/`
remains the canonical checkout location. The dictionary is NOT copied
alongside them — see §4.

## 3. ONNX Runtime (inference engine)

| Item | Value |
|---|---|
| Package | `onnxruntime==1.32.0` (CPU wheel only; `onnxruntime-gpu` is not installed and is forbidden by PROJECT_BOOK.md §6.2) |
| Licence | MIT |
| Licence source | ONNX Runtime `LICENSE` file as distributed with the wheel |
| Runtime providers used | `CPUExecutionProvider` only (asserted at adapter start-up and in `tests/integration/test_ocr_adapter.py`) |

Note: `onnxruntime.get_available_providers()` also lists
`AzureExecutionProvider`; that is a built-in registration of the stock CPU
wheel, not a GPU provider, and it is never selected — sessions are created
with an explicit `["CPUExecutionProvider"]` provider list.

## 4. Recognition dictionary — SEPARATELY VERIFIED, LICENCE UNVERIFIED

| Item | Value |
|---|---|
| File (`assets/ocr/dictionaries/`) | `ppocrv6_dict.txt` (18,708 lines, 74,947 B) |
| What it is | The PP-OCRv6 multilingual recognition character list used by `PP-OCRv6_rec_small` |
| Registry source (`dict_url`) | https://www.modelscope.cn/models/RapidAI/RapidOCR/resolve/v3.10.0/paddle/PP-OCRv6/rec/PP-OCRv6_rec_small/ppocrv6_dict.txt |
| Upstream source | https://github.com/PaddlePaddle/PaddleOCR/blob/main/ppocr/utils/dict/ppocrv6_dict.txt |
| SHA-256 | `b5f2bfe2bdd9448429e3e82b51c789775d9b42f2403d082b00662eb77e401c5d` |
| Licence | **未核实 (UNVERIFIED — no dictionary-specific licence statement found; re-verified 2026-11-25, T014/R-03 — see below)** |

Verification performed (2026-11-25, T003):

1. The file downloaded from the registry `dict_url` is byte-identical
   (SHA-256 `b5f2bfe2…`) to the file at the PaddleOCR upstream URL above.
2. It is byte-identical to the `character` list embedded in the
   `PP-OCRv6_rec_small.onnx` model metadata (read via ONNX Runtime
   `get_modelmeta().custom_metadata_map`). The ONNX engine reads the
   embedded copy at runtime; the local file is cross-checked against it
   on every adapter start-up (see `src/textproof/ocr/rapidocr_adapter.py`).
3. It is **not** the older `ppocr_keys_v1.txt` (6,623 lines); that file
   does not match the embedded list and was not used.

Licence status — read carefully, do **not** infer from the models:

- The RapidOCR model licence statement explicitly **excludes**
  dictionaries: “The registry also records non-model resources, including
  recognition dictionaries (`dict_url`) and fonts (`fonts`). These
  resources are not model artifacts and are not covered by the Apache-2.0
  declaration in this notice; they remain subject to their own applicable
  terms.” (§2; repeated in §6.)
- The dictionary file itself carries no licence header or licence
  statement.
- The file is distributed as part of the PaddleOCR repository, whose
  repository-level licence is Apache-2.0 — but no source was found that
  states a licence for this dictionary file specifically.
- Therefore, per PROJECT_BOOK.md §10.2 and T003 acceptance criterion 7,
  the dictionary licence is recorded here as **未核实 (unverified)**. It
  must **not** be described as Apache-2.0 on the strength of the model
  licence, and T014 (SBOM / licence report) must revisit it before any
  public release that redistributes the dictionary as a separate file.

Re-verification (2026-11-25, T014 / review finding R-03 — full record in
`task_handoffs/T014/r03/LICENSE_VERIFICATION_R03.md`): a fresh check of
the RapidOCR model licence page, the upstream dictionary file and its
git history, the PaddleOCR repository `LICENSE`, and third-party claims
found **no source that clearly and unambiguously proves the dictionary
may be redistributed**. The decisive evidence runs the other way: the
RapidOCR notice expressly excludes `dict_url` resources from its
Apache-2.0 declaration (§2, repeated in §6). The PaddleOCR repository
`LICENSE` is a generic Apache-2.0 text that does not state it covers
this data file, and the dictionary file itself carries no licence
header. Third-party pages that label the dictionary Apache-2.0 are
downstream assertions, not rights-holder statements, and were not
accepted as proof. **Verdict: licence remains UNVERIFIED.**

Consequence — the dictionary is NOT redistributed as a separate file.
Public artifacts (GitHub snapshot tree, `source.zip`, wheel) must not
contain `assets/ocr/dictionaries/ppocrv6_dict.txt` — and, since
T013-U01, must not contain the installed-layout copy either
(`textproof/assets/ocr/dictionaries/ppocrv6_dict.txt`, rebuilt locally
into the installed package; it is git-ignored and the wheel's
package-data glob matches only the three model files):

- The file is removed from git tracking in the T014/R-03 commit and
  listed in `.gitignore`, so no snapshot taken from this tree contains
  it. (It is still present on a developer's disk after running the
  rebuild below; that local copy is ignored, not tracked.)
- `source.zip` / wheel builders must exclude the same path
  (`assets/ocr/dictionaries/ppocrv6_dict.txt`) explicitly — do not rely
  on the git tree alone when assembling an archive from a working copy.
- `assets/ocr/SHA256SUMS.txt` still records the dictionary hash: it is
  the verification reference for the locally rebuilt file, not a claim
  that the file ships in the archive.

Local rebuild (the only supported way to obtain the file, after
checkout or after a wheel install):

```bash
.venv/bin/python scripts/setup_dictionary.py        # rebuild if missing (checkout)
.venv/bin/python scripts/setup_dictionary.py --check  # verify only
python -m textproof.setup_dictionary               # same rebuild (installed wheel)
```

The rebuild reads **only local files**: it takes the `character` list
embedded in the locally shipped `PP-OCRv6_rec_small.onnx` model file —
itself an Apache-2.0 model artifact — writes it out as the dictionary,
and verifies SHA-256 `b5f2bfe2…` and 18,708 lines before reporting
success. It performs no remote fetch and no download; it verifies the
model file's hash before trusting its metadata; and it refuses to
overwrite an existing differing dictionary unless `--force` is given.
The rebuilt file is byte-identical to the frozen file (verified
2026-11-25, T014). **Run this script before running the test suite on
a fresh checkout**: `tests/offline/test_offline_static.py::test_model_assets_present_locally`
and `tests/privacy/test_local_assets.py::test_model_files_are_local_with_frozen_hashes`
assert the dictionary file exists, so they fail on a fresh clone until
the rebuild has run. That ordering is intentional and documented here,
not a test defect — do not weaken the tests to accommodate a missing
dictionary.

## 5. PaddleOCR (upstream project, not shipped)

| Item | Value |
|---|---|
| Project | PaddleOCR — https://github.com/PaddlePaddle/PaddleOCR |
| Licence | Apache-2.0 |
| Role | Upstream origin of the PP-OCR model weights and of the recognition dictionary; technical precedent only. No PaddleOCR code is copied or shipped. |

## 6. What is NOT included

- No ComfyUI, AnyText, Qwen-Image, or Qwen-Image-Edit code, weights,
  workflows, or training data is copied or used (PROJECT_BOOK.md §10.3).
- No remote inference, cloud OCR, or paid API is used. All OCR runs
  locally on CPU; the adapter refuses to download anything at runtime.
- No fonts are shipped by T003. (Test images in
  `tests/integration/test_ocr_adapter.py` are rendered with system fonts
  at test time only — `Noto Sans CJK SC`
  (`/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc`) and
  `DejaVu Sans` (`/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf`),
  see `tests/integration/test_ocr_adapter.py:38–39` — never shipped or
  redistributed by TextProof.)

### Fixture font — Noto Sans SC (T005, recorded here for completeness)

Scope note: this font is a T005 deliverable, not a T003 asset. This
file's stated scope (§0: “records every third-party asset used by
T003”) therefore does not cover it; it is summarised here so that the
§10.2 font record (OFL, source, version, hash) is complete in one
place. The authoritative record remains
`tests/fixtures/s0/fonts/FONT_NOTICE.md`; the values below were
verified against that file and the font file itself (2026-11-25).

| Item | Value |
|---|---|
| Font | Noto Sans SC (variable font, `wght` axis), named instance `Regular` (wght 400) |
| File | `tests/fixtures/s0/fonts/NotoSansSC[wght].ttf` (17,772,300 bytes) |
| Source (official) | https://github.com/google/fonts/raw/main/ofl/notosanssc/NotoSansSC%5Bwght%5D.ttf (Google Fonts repository, `ofl/notosanssc`) |
| Version (name table, ID 5) | 2.004-H2 (`Version 2.004-H2;hotconv 1.0.118;makeotfexe 2.5.65603`) |
| SHA-256 | `a3041811a78c361b1de50f953c805e0244951c21c5bd412f7232ef0d899af0da` |
| Licence | SIL Open Font License, Version 1.1 (OFL-1.1) — full text in `tests/fixtures/s0/fonts/OFL.txt` (SHA-256 `1c05c68c34f9708415aada51f17e1b0092d2cea709bf4a94cd38114f9e73d7d9`) |
| Use | Only to render synthetic S0 test images (64 px, black on white, 1200×480 PNG); never shipped as a product asset |
| Generator check | `scripts/generate_fixtures.py` verifies this file's SHA-256 and byte size on every run and refuses to generate or verify if either differs |

T014 (SBOM / licence report) re-verifies this record before any
public release.
