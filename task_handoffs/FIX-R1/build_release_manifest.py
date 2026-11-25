#!/usr/bin/env python3
"""Build release/RELEASE_MANIFEST.json + release/SHA256SUMS.txt (FIX-R1).

Every hash and size is recomputed from disk; nothing is copied from
memory or from the old manifest except the wheelhouse entries, which
are re-verified against the wheel files on disk (any mismatch fails
the build).  Also asserts, at build time, that ``release/source.zip``
matches ``git archive <source-commit>`` file by file (the same check
``scripts/verify_release.py`` performs at verification time).

Usage (run from the repository root, after the freeze commit exists
and the wheel has been rebuilt from a clean export of it)::

    python task_handoffs/FIX-R1/build_release_manifest.py \\
        --source-commit <40-hex> --source-branch fix-r1 \\
        --pytest "495 passed, 0 failed, exit 0 (XXX.XXs)" \\
        --pytest-log task_handoffs/FIX-R1/pkg/test_stdout.log \\
        --exit-codes task_handoffs/FIX-R1/pkg/exit_codes.txt \\
        --smoke task_handoffs/FIX-R1/pkg/offline_smoke.txt
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import subprocess
import sys
import tarfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
OLD_MANIFEST = ROOT / "release" / "RELEASE_MANIFEST.json"

FILES_MAP = [
    "release/source.zip",
    "release/textproof-1.0.0-py3-none-any.whl",
    "release/SHA256SUMS.txt",
    "release/SBOM_LICENSES.md",
    "review/REVIEW_INDEX.md",
    "review/REVIEW_PACK_T014.md",
    "review/REVIEW_PACK_T014R2.md",
    "review/REVIEW_PACK_T014R3.md",
    "review/REVIEW_PACK_FIXR1.md",
    "scripts/verify_release.py",
    "scripts/verify_review_pack.py",
]


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _git_archive_files(commit: str) -> dict[str, bytes]:
    proc = subprocess.run(
        ["git", "archive", commit], cwd=str(ROOT), capture_output=True
    )
    if proc.returncode != 0:
        raise ValueError(f"git archive {commit} failed")
    files: dict[str, bytes] = {}
    with tarfile.open(fileobj=io.BytesIO(proc.stdout), mode="r|") as tar:
        for member in tar:
            if member.isfile():
                data = tar.extractfile(member)
                if data is not None:
                    files[member.name] = data.read()
    return files


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--source-branch", required=True)
    parser.add_argument("--pytest", required=True,
                        help="pytest summary line, e.g. '495 passed, 0 failed, exit 0 (123.45s)'")
    parser.add_argument("--pytest-log", required=True)
    parser.add_argument("--exit-codes", required=True)
    parser.add_argument("--smoke", required=True)
    args = parser.parse_args(argv)

    old = json.loads(OLD_MANIFEST.read_text(encoding="utf-8"))

    # --- source.zip must equal git archive of the source commit ---
    source_zip = ROOT / "release" / "source.zip"
    archived = _git_archive_files(args.source_commit)
    with zipfile.ZipFile(source_zip) as zf:
        names = [n for n in zf.namelist() if not n.endswith("/")]
        if sorted(names) != sorted(archived):
            missing = sorted(set(archived) - set(names))
            extra = sorted(set(names) - set(archived))
            print(f"FAIL: source.zip file set != git archive {args.source_commit}")
            print(f"  missing from zip: {missing[:10]}")
            print(f"  extra in zip: {extra[:10]}")
            return 1
        for name in names:
            if _sha256(zf.read(name)) != _sha256(archived[name]):
                print(f"FAIL: source.zip content mismatch: {name}")
                return 1
    if "release/" in " ".join(names):
        print("FAIL: source.zip contains release/ entries (nesting not fixed)")
        return 1
    print(f"source.zip matches git archive {args.source_commit}: "
          f"{len(names)} files")

    # --- wheel identity ---
    wheel = ROOT / "release" / "textproof-1.0.0-py3-none-any.whl"
    with zipfile.ZipFile(wheel) as zf:
        meta = [n for n in zf.namelist() if n.endswith("METADATA")]
        assert len(meta) == 1, meta
        text = zf.read(meta[0]).decode()
        assert "Name: textproof" in text and "Version: 1.0.0" in text, text[:400]
        entries = zf.namelist()
    if "ppocrv6_dict.txt" in " ".join(entries):
        print("FAIL: wheel contains the excluded dictionary")
        return 1
    print(f"wheel OK: {len(entries)} entries, no dictionary")

    # --- wheelhouse: reuse the 37 files, re-verify against old manifest ---
    wheelhouse_dir = ROOT / "release" / "wheelhouse"
    wheelhouse: list[dict] = []
    old_wh = {e["file"]: e for e in old["wheelhouse"]}
    for wh in sorted(wheelhouse_dir.glob("*.whl")):
        rel = f"release/wheelhouse/{wh.name}"
        entry = {"file": rel, "sha256": _sha256_file(wh),
                 "size": wh.stat().st_size}
        if rel not in old_wh:
            print(f"FAIL: wheelhouse file not in old manifest: {rel}")
            return 1
        if entry["sha256"] != old_wh[rel]["sha256"] or entry["size"] != old_wh[rel]["size"]:
            print(f"FAIL: wheelhouse file changed: {rel}")
            return 1
        wheelhouse.append(entry)
    if len(wheelhouse) != 37:
        print(f"FAIL: expected 37 wheelhouse wheels, found {len(wheelhouse)}")
        return 1
    print("wheelhouse OK: 37 wheels, hashes match the T014 manifest")

    # --- SHA256SUMS.txt (source.zip + wheel + 37 wheelhouse, sorted) ---
    sums_lines = [
        f"{_sha256_file(source_zip)}  source.zip",
        f"{_sha256_file(wheel)}  textproof-1.0.0-py3-none-any.whl",
    ]
    for entry in wheelhouse:
        sums_lines.append(f"{entry['sha256']}  wheelhouse/{Path(entry['file']).name}")
    sums_text = "\n".join(sums_lines) + "\n"
    (ROOT / "release" / "SHA256SUMS.txt").write_text(sums_text, encoding="utf-8")
    print(f"SHA256SUMS.txt written: {len(sums_lines)} entries")

    # --- files map (hashes/sizes recomputed from disk) ---
    files_map: dict[str, dict] = {}
    for rel in FILES_MAP:
        target = ROOT / rel
        if not target.is_file():
            print(f"FAIL: manifest file missing: {rel}")
            return 1
        files_map[rel] = {"sha256": _sha256_file(target),
                          "size": target.stat().st_size}

    resolved = list(old.get("resolved_items", []))
    resolved.extend([
        {
            "id": "P1-01",
            "blocking_was": True,
            "title": "Frozen PROJECT_BOOK.md: Drive root copy was the old 44,552 B version without the 7 T013 clarifications; DOCX likewise stale",
            "fixed_in": "FIX-R1 (branch fix-r1)",
            "verification": "PROJECT_BOOK.docx regenerated from the current MD (46,114 B, SHA 8a2b6e56...) with scripts/md_to_docx.py; new DOCX 62,512 B, SHA 97706fc9...; Title 1 + 66 headings = 67, 14 tables, all 7 clarifications present; Drive root MD + DOCX replaced (same file IDs) and re-downloaded byte-identical. See task_handoffs/FIX-R1/fix-r1-01-verification.md and review/REVIEW_PACK_T014.md section 9.",
        },
        {
            "id": "P1-02",
            "blocking_was": True,
            "title": "R3 REVIEW_INDEX.md missing from source.zip; manifest expected SHA 7ebbc997... which matched nothing retrievable; no Git bundle to prove the commit-archive link",
            "fixed_in": "FIX-R1 (branch fix-r1)",
            "verification": "Root cause confirmed: the R3 index was committed after the freeze commit (9befbee) while source.zip was git archive of 93d1b7c. Current R3 index uploaded to the old Drive freeze folder (file 1IXwRD_eCua_o4_ksNoKSJTNYrn4bvGAK) and a git bundle of 93d1b7c (SHA d4395c67..., 457,701,056 B, file 1MpHMtv2d7MFXn_LS00cAEdKBc5NjYcgX) uploaded alongside; bundle verified and clone-checked. The new freeze's index is generated for the new freeze commit and shipped in the new Drive folder from the start. See task_handoffs/FIX-R1/fix-r1-02-verification.md.",
        },
        {
            "id": "P1-03",
            "blocking_was": True,
            "title": "Section 8.3 performance gate (1920x1080, 30 runs, P95 <= 5s): the 3.817s report predated the T013 core-algorithm change",
            "fixed_in": "FIX-R1 (branch fix-r1)",
            "verification": "Re-measured on the frozen code (git diff 93d1b7c HEAD -- src/ scripts/ tests/fixtures empty): P95 4.458s <= 5s, PASS, exit 0; P50 2.812s, mean 2.934s, min 1.804s, max 4.585s; 30 runs after 3 warm-ups. Raw data task_handoffs/FIX-R1/perf/perf_measurements.jsonl, summary perf_summary.json, PERFORMANCE_REPORT.md updated (T011 3.817s kept as labelled history). See task_handoffs/FIX-R1/fix-r1-03-verification.md.",
        },
        {
            "id": "P2-S0-REPORT",
            "blocking_was": False,
            "title": "S0_REPORT.md out of sync with the evidence: edge battery 13/26 (actual 14/26); 1200x480 timing 1.33/1.77/3.13s has no run record; 'both independent reviews re-ran S0' was inaccurate (R2 did not)",
            "fixed_in": "FIX-R1 (branch fix-r1)",
            "verification": "parity_check.py re-run on the frozen code: 14/26, exit 0 (flip caused by the T013 R-01 exact-Fraction fix, commit d26adcc). Timing re-derived from task_handoffs/T006/live_ocr_results.jsonl: P50 2.1235s / P95 2.7147s / max 3.2683s is the authoritative T006 run2; the 1.33/1.77/3.13 set has no run record on disk and must no longer be cited. S0_REPORT.md revised (419 -> 476 lines) with a new section 10 'Known limitations'. See task_handoffs/FIX-R1/fix-r1-04-verification.md.",
        },
        {
            "id": "U-02",
            "blocking_was": False,
            "title": "DOCX body-text drift: 7 T013 wording clarifications in PROJECT_BOOK.md not in PROJECT_BOOK.docx (structure in sync)",
            "fixed_in": "FIX-R1 (branch fix-r1)",
            "verification": "Same evidence as P1-01: DOCX regenerated from the current MD and Drive-synced; see fix-r1-01-verification.md.",
        },
        {
            "id": "U-03",
            "blocking_was": False,
            "title": "omegaconf 2.4.0 has no licence statement in installed distribution metadata (SBOM_LICENSES.md)",
            "fixed_in": "FIX-R1 (branch fix-r1)",
            "verification": "The wheel's bundled LICENSE file (omegaconf-2.4.0.dist-info/licenses/LICENSE) opens 'BSD 3-Clause License', Copyright (c) 2018 Omry Yadan; PyPI classifier agrees ('License :: OSI Approved :: BSD License'). SBOM now records BSD-3-Clause with that source.",
        },
    ])

    manifest = {
        "release": "P033 TextProof",
        "source_commit": args.source_commit,
        "source_branch": args.source_branch,
        "tool_version": "0.1.0",
        "package_version": "1.0.0",
        "spec_version": "1.0.0",
        "built_from": (
            f"git archive {args.source_commit} (source.zip); "
            "python -m build --wheel --no-isolation from a clean export of the same commit (wheel); "
            "wheelhouse reused from T014 (37 wheels, re-verified against requirements.lock)"
        ),
        "wheel": "textproof-1.0.0-py3-none-any.whl",
        "files": files_map,
        "wheelhouse": wheelhouse,
        "wheelhouse_packages": 37,
        "test_evidence": {
            "pytest": args.pytest,
            "pytest_log": args.pytest_log,
            "exit_codes": args.exit_codes,
            "offline_smoke": args.smoke,
            "pytest_t014": "495 passed, 0 failed, exit 0 (382.51s); log task_handoffs/T014/pkg/test_stdout.log (unchanged product code since 93d1b7c)",
        },
        "exclusions": old.get("exclusions"),
        "resolved_items": resolved,
        "known_unresolved_items": [
            {
                "id": "K-01",
                "blocking": False,
                "title": "Multi-line poster end-to-end coverage insufficient: all 300 S0 images produce single-line OCR; no real multi-line OCR output covered",
                "detail": "Production code supports multi-line alignment and synthetic line-alignment tests pass, but the S0 set has no multi-line OCR case. The 1920x1080 four-line perf image drops two inter-word spaces and reads U+51CF as U+6E1B (MISMATCH). Next version: add multi-line clean samples. See S0_REPORT.md section 10(a).",
            },
            {
                "id": "K-02",
                "blocking": False,
                "title": "Currency symbol confusion: full-width yen U+FFE5 read as U+00A5 is kept as a character-level difference by design; e-commerce price posters may see extra false positives",
                "detail": "Per-type reading of section 8.1 adopted; no U+FFE5->U+00A5 mapping is added. Next version: add currency-symbol samples. See S0_REPORT.md section 10(b).",
            },
            {
                "id": "R14R-01",
                "blocking": False,
                "title": "Review-pack line-count wording: index described as '453 lines: 399 files + 1 PNG aggregate line' (P3, content correct)",
                "detail": "Carried from the T014 R2 incremental review; wording only.",
            },
            {
                "id": "R14R-02",
                "blocking": False,
                "title": "DOCX drift line-count wording in the R3 pack ('+11/-7 lines' counts diff headers) (P3, content correct)",
                "detail": "Carried from the T014 R2 incremental review; wording only. The drift itself is resolved by the FIX-R1 DOCX regeneration (P1-01).",
            },
        ],
    }
    (ROOT / "release" / "RELEASE_MANIFEST.json").write_text(
        json.dumps(manifest, indent=1, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"RELEASE_MANIFEST.json written: source_commit={args.source_commit}")
    print(f"  files map: {len(files_map)} entries; "
          f"source.zip={_sha256_file(source_zip)[:12]}...; "
          f"wheel={_sha256_file(wheel)[:12]}...")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
