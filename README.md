# TextProof（字证）

TextProof checks the text rendered in an AI-generated image against the
expected text and reports every character-level difference deterministically:
missing, extra, substituted and numeric-change errors, with line indexes,
spans and bounding boxes, in a frozen JSON schema (`textproof.report/v1`).

It is a **local, CPU-only, offline** tool. All OCR runs on this machine with
RapidOCR / ONNX Runtime (`CPUExecutionProvider` only). It needs no account,
no API key, no GPU and no network connection at run time.

## First step after a fresh checkout — rebuild the dictionary

A fresh checkout does **not** contain the recognition dictionary
`assets/ocr/dictionaries/ppocrv6_dict.txt`. The file is not redistributed
(its licence is unverified — see `THIRD_PARTY_NOTICES.md` §4) and is not
tracked in git. Rebuild it locally before running any test or check:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install --require-hashes -r requirements.lock
.venv/bin/python scripts/setup_dictionary.py
```

`setup_dictionary.py` extracts the character list embedded in the locally
shipped `PP-OCRv6_rec_small.onnx` model file and verifies the result
(SHA-256 `b5f2bfe2…`, 18,708 lines) before writing it out. It reads only
local files and makes no network connection. Until it has run, tests that
assert the dictionary exists will fail — that is an expected ordering
dependency, not a product defect.

## Install

Requirements: Python 3.12.x, Linux x86_64 (the frozen platform).

### From a source checkout (recommended)

```bash
python3 -m venv .venv
.venv/bin/python -m pip install --require-hashes -r requirements.lock
.venv/bin/python scripts/setup_dictionary.py
```

Then run from the checkout root (the package is not installed into the
venv; tests run the same way):

```bash
PYTHONPATH=src .venv/bin/python -m textproof.cli --help
PYTHONPATH=src .venv/bin/python -m textproof.cli version
```

### From the release wheel (offline)

```bash
python3 -m venv .venv-offline
.venv-offline/bin/python -m pip install --no-index \
    --find-links release/wheelhouse release/textproof-1.0.0-py3-none-any.whl
```

`release/wheelhouse/` holds every wheel pinned by `requirements.lock`
(37 packages), so this needs no network. `textproof --help` and
`textproof version` work standalone, and so do `check` and `serve`
once the dictionary has been rebuilt (see "Installing from the wheel"
below). Only `verify-s0` requires a source checkout (it exits 3
without one).

### Installing the package itself from source

`pip install .` in a fresh venv needs network once (pip fetches the
`setuptools>=69` build backend under build isolation). A fresh
`python3 -m venv` venv here ships pip but no setuptools, so
`pip install --no-build-isolation .` fails there unless setuptools was
installed into the venv first. The checkout workflow above does not
need the package installed at all.

Verify the install:

```bash
textproof --help
textproof version
```

## Quick start

### CLI

Check one image against the expected text:

```bash
printf '限时优惠' > expected.txt
textproof check --image ./poster.png --expected-file ./expected.txt --json ./report.json
echo $?   # 0 = MATCH, 1 = MISMATCH, 2 = REVIEW_REQUIRED, 3 = invalid input, 4 = OCR failed, 5 = internal error
```

`report.json` is a `textproof.report/v1` report: `verdict`, `errors` (each
with `type`, line indexes, spans and bounding box), `warnings`, `summary`,
plus the `tool_version`, `schema` and image SHA-256. The schema is
`schemas/textproof.report.v1.schema.json`.

Run the S0 acceptance gate (300 frozen fixtures):

```bash
textproof verify-s0 --manifest tests/fixtures/s0/manifest.json
```

Note: `verify-s0` has its own exit contract — 0 = gate passed, 1 = gate
failed — which is unrelated to the `check` exit-code table above
(PROJECT_BOOK.md §5.5).

### Local API and UI

```bash
textproof serve --host 127.0.0.1 --port 8765
```

Then open `http://127.0.0.1:8765` in a browser, or call the API:

- `GET /api/v1/health` — health status, no user data.
- `GET /api/v1/version` — versions (see below).
- `POST /api/v1/check` — JSON body `image_mime`, `image_base64`,
  `expected_text`; returns the same `textproof.report/v1` report as the CLI.

The server binds **only `127.0.0.1`**; any other host is refused at
start-up. CLI, API and UI use the same comparison core and the same JSON
schema, so the same input gives the same verdict on all three.

### Input limits (frozen, PROJECT_BOOK.md §4.2)

- Formats: PNG, JPEG, WEBP (checked by magic bytes, never by extension).
- Max file size 25 MiB; max dimension 8,192 px; max 40,000,000 pixels.
- Expected text: max 5,000 code points, max 100 lines.

## Version identity — three different numbers, not a bug

| Field | Value | Meaning |
|---|---|---|
| `tool_version` | `0.1.0` | Product version of the TextProof checker itself (`src/textproof/core/report.py`; PROJECT_BOOK.md §5.4 sample; IMPLEMENTATION_PLAN.md “产品版本初始目标：0.1.0”). It appears in every report. |
| `package_version` | `1.0.0` | Packaging version of the installable Python package (`pyproject.toml`). Shown by `textproof version` when the package is installed (`"not-installed"` otherwise). |
| `spec_version` | `1.0.0` | Version of the frozen specification the build implements (`src/textproof/api/routes.py`). |

These are three different dimensions by design. Do **not** “fix”
`tool_version` to `1.0.0`: the T012 independent review confirmed the
distinction (REVIEW_FINDINGS.md §3, item 1) and the frozen product version
is `0.1.0`.

## Offline-only

TextProof makes **zero network accesses at run time**: no PyPI, no
ModelScope, no Hugging Face, no telemetry, no external HTTP requests of
any kind (verified by the T010 privacy/offline test suite). Models,
dictionary and fonts are local files under `assets/ocr/` and
`tests/fixtures/`; the only network use in the whole project is the
one-time, human-driven `pip install` / `pip download` that fetches the
locked dependencies. The application itself never opens a network
connection — the loopback API on `127.0.0.1` is local inter-process
communication, not network access.

## Privacy

Images, expected text and OCR results are processed only in local process
and browser memory. Nothing is written to a database or `localStorage`,
no logs are uploaded, no telemetry is sent. Logs record only request
status, timing, error codes and software versions — never image bytes,
OCR text, expected text, absolute paths or user directories. See
PROJECT_BOOK.md §9 and `SECURITY.md`.

## Licensing and third-party notices

- TextProof's **own source code is MIT** — see `LICENSE`. The MIT licence
  covers only TextProof's own code.
- Dependencies, OCR models, the recognition dictionary and fonts each keep
  their own upstream licences. The full record — source URL, version,
  SHA-256 and licence status for every asset — is in
  [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md). Read it before
  redistributing anything.
- **Dictionary warning:** the recognition dictionary
  `ppocrv6_dict.txt` has **UNVERIFIED** licence status and is **not**
  redistributed in any public artifact (`source.zip`, wheel, GitHub
  snapshot). It must be rebuilt locally with
  `scripts/setup_dictionary.py` (see above).
- The locked dependency set (37 packages, 753 SHA-256 hashes) is in
  `requirements.lock`; per-package licence information is in
  `release/SBOM_LICENSES.md`.

## Repository layout

```
pyproject.toml  requirements.lock  LICENSE  README.md  SECURITY.md
THIRD_PARTY_NOTICES.md
src/textproof/        # CLI, API, comparison core, OCR adapter, UI
src/textproof/assets/ # verbatim model copies shipped in the wheel (dictionary rebuilt locally)
assets/ocr/           # ONNX models + SHA256SUMS.txt (dictionary rebuilt locally)
tests/                # unit / integration / e2e / privacy / offline / S0 (300 fixtures)
schemas/              # textproof.report/v1 JSON schema
scripts/              # verify_s0.py, verify_release.py, verify_review_pack.py, ...
oracle/               # independent reference implementation (S0 parity)
release/              # source.zip, wheel, wheelhouse/, SHA256SUMS.txt, RELEASE_MANIFEST.json
review/               # REVIEW_INDEX.md, REVIEW_PACK_T014.md
```

Full specification: `PROJECT_BOOK.md`; build plan: `IMPLEMENTATION_PLAN.md`;
API contract: `API_CONTRACT.md`; environment baseline: `ENVIRONMENT.md`.

## Installing from the wheel (no source checkout needed)

The wheel ships the report validator, the local UI and the three
frozen ONNX models (Apache-2.0, verbatim copies of
`assets/ocr/models/`), so an installed `textproof` runs `check` and
`serve` standalone, offline, with no checkout (PROJECT_BOOK.md
§11.2; fixed in the T013-U01 round — the previous release could not
do this, see `review/REVIEW_PACK_T014.md` §3, item U-01).  The
recognition dictionary is the one exception: its licence is
UNVERIFIED (`THIRD_PARTY_NOTICES.md` §4), so it is never shipped in
the wheel and must be rebuilt once, locally, from the model file
already inside the wheel:

```bash
python -m venv .venv && .venv/bin/activate
pip install --no-index --find-links release/wheelhouse \
    release/textproof-1.0.0-py3-none-any.whl
python -m textproof.setup_dictionary   # rebuilds ppocrv6_dict.txt (18,708 lines)
textproof check --image poster.png --expected-file expected.txt
textproof serve --port 8765            # UI at http://127.0.0.1:8765/
```

Asset boundary: models come from the wheel
(`textproof/assets/ocr/models/`); the dictionary is rebuilt next to
them (`textproof/assets/ocr/dictionaries/`).  In a source checkout
the checkout assets (`assets/ocr/`) win instead, so existing
checkout workflows are unchanged.  `TEXTPROOF_ASSETS_DIR` overrides
both locations when set.  `textproof verify-s0` is the exception to
standalone use: the S0 gate needs the checkout's fixtures, manifest
and runner scripts, which are not shipped in the wheel, so in an
installed layout it exits 3 with a defined message ("verify-s0
requires a source checkout") — run it from a checkout instead.

## Known limitations

(None currently recorded. The previous U-01 installed-wheel
limitation was fixed by the T013-U01 round; see "Installing from the
wheel" above.)

## Security

See [`SECURITY.md`](SECURITY.md) for how to report a vulnerability
(GitHub Security Advisory), the supported scope, and what data TextProof
does and does not collect.
