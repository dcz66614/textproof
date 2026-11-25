# Security Policy

## Reporting a vulnerability

**Do not open a public issue for a security vulnerability.**

Report it through a **GitHub Security Advisory** on this repository
(Repository → Security → Advisories → New draft advisory). The advisory
stays private until a fix is ready, so the report and any discussion are
not visible to anyone else in the meantime.

Please include, where you can:

- what you did (steps to reproduce),
- what you expected to happen and what happened instead,
- the TextProof version (`textproof version` output) and how you installed
  it (wheel, `source.zip`, or a git checkout),
- whether any user data (an image, expected text, or a report) left the
  local machine — by design it should never do so.

There is no dedicated security contact email for this project. The GitHub
Security Advisory channel above is the only reporting route; do not send
reports to any personal address found in commit history.

## Supported scope

Security reports are accepted for the current release (the `release/`
bundle of the latest frozen commit) and for the current `main` branch.
Only TextProof's own code is in scope: the comparison core, CLI, local
API, UI, image loader and OCR adapter under `src/`, plus the packaging
and verification scripts under `scripts/`.

Out of scope: vulnerabilities in upstream dependencies (RapidOCR, ONNX
Runtime, FastAPI, Pillow, and the other locked packages — report those
to their own upstreams), in the OCR model files themselves, and in the
test fixtures (synthetic images only, no real user data).

## What TextProof does and does not collect

Consistent with PROJECT_BOOK.md §9:

- **No user data leaves the machine.** Images, expected text, OCR
  results and reports are processed only in local process and browser
  memory. TextProof writes no database, uses no `localStorage`, uploads
  no logs, sends no telemetry and makes no external network connection
  at run time (zero network accesses, verified by the T010 privacy /
  offline test suite).
- **Local-only service.** The API binds only `127.0.0.1`; any other bind
  host is refused at start-up. There is no public listener, no CORS
  allow-list for external origins, and no external callback.
- **Logs** record only request status, timing, error codes and software
  versions — never image bytes, OCR text, expected text, absolute paths
  or user directories. JSON reports are written only when the user
  explicitly asks for them (`--json`, or the UI download button), and the
  UI warns that an exported report may contain sensitive text.
- **No credentials exist in this project.** There is no account, API key,
  token or password anywhere in the code or configuration. Nothing in
  TextProof needs one.
- **No memory-erasure claim.** Clearing the UI revokes the image preview
  and drops the application's references to the image, text and report.
  That does not guarantee the operating system, swap, crash dumps or the
  browser process have erased their copies.

## Known non-issues (documented design limits)

- The recognition dictionary `assets/ocr/dictionaries/ppocrv6_dict.txt`
  is rebuilt locally from the shipped model file and is not redistributed;
  its licence status is recorded as UNVERIFIED in
  `THIRD_PARTY_NOTICES.md` §4. That is a licensing status, not a
  vulnerability, and it is handled by exclusion from public artifacts
  rather than by a code fix.
- `textproof verify-s0` exits 1 when the S0 gate fails; that exit code is
  the gate's own pass/fail contract and is unrelated to the `check`
  exit-code table (PROJECT_BOOK.md §5.5).
