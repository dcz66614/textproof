"""Verify a TextProof review index against its anchor commit (T014, R-30).

Usage::

    python scripts/verify_review_pack.py review/REVIEW_INDEX.md [--root DIR]

The index (``review/REVIEW_INDEX.md``) lists every tracked file of the
frozen source commit it anchors, with byte size, SHA-256 and line count
per file, plus one aggregate row for the 300 S0 fixture PNGs (whose
per-file hashes live in ``tests/fixtures/s0/manifest.json`` and are
re-verified by ``scripts/verify_s0.py``).

This script checks, against the anchor commit itself (read through
``git show`` / ``git archive``, never the possibly dirty working tree):

1. every listed file exists at the anchor commit and its byte size,
   SHA-256 and line count (``wc -l`` semantics: number of newline bytes)
   match the index;
2. the aggregate PNG row matches the recomputed total size and aggregate
   hash (SHA-256 of the sorted ``"<sha256>  <path>"`` lines);
3. completeness: every tracked file at the anchor commit is either listed
   or covered by the aggregate row; nothing is missing and nothing extra
   is listed.

Local-only: reads files from the local git object store. No network
access, no writes outside a temporary directory. Exit 0 = PASS,
exit 1 = FAIL (any mismatch, missing file, or coverage gap).
"""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import io
import re
import subprocess
import sys
import tarfile
from pathlib import Path

DICT_NAME = "ppocrv6_dict.txt"

# Row: | `path` | bytes | `sha256` | lines | status | notes |
_ROW_RE = re.compile(
    r"^\|\s*`([^`]+)`\s*\|\s*(\d+)\s*\|\s*`([0-9a-f]{64})`\s*\|\s*(\d+|—)\s*\|"
)
_ANCHOR_RE = re.compile(r"commit[:：]\s*`?([0-9a-f]{40})`?")


def _run(argv: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(argv, cwd=str(cwd), text=True, capture_output=True)


def _fail(errors: list[str], message: str) -> None:
    errors.append(message)
    print(f"  FAIL: {message}")


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _lines(data: bytes) -> int:
    return data.count(b"\n")


def _parse_index(path: Path) -> tuple[str, list[dict]]:
    text = path.read_text(encoding="utf-8")
    anchor = None
    for line in text.splitlines():
        if "commit" in line:
            match = _ANCHOR_RE.search(line)
            if match:
                anchor = match.group(1)
                break
    if anchor is None:
        raise ValueError("no anchor commit found in index header")
    rows: list[dict] = []
    for line in text.splitlines():
        match = _ROW_RE.match(line)
        if match:
            rows.append(
                {
                    "path": match.group(1),
                    "size": int(match.group(2)),
                    "sha256": match.group(3),
                    "lines": None if match.group(4) == "—" else int(match.group(4)),
                }
            )
    if not rows:
        raise ValueError("no coverage-table rows found in index")
    return anchor, rows


def _tracked_files(root: Path, anchor: str) -> dict[str, bytes]:
    """Return {path: content} for every tracked file at the anchor commit."""
    archive = subprocess.run(
        ["git", "archive", anchor],
        cwd=str(root),
        capture_output=True,
    )
    if archive.returncode != 0:
        raise ValueError(f"git archive {anchor} failed")
    files: dict[str, bytes] = {}
    with tarfile.open(fileobj=io.BytesIO(archive.stdout), mode="r|") as tar:
        for member in tar:
            if member.isfile():
                data = tar.extractfile(member)
                if data is not None:
                    files[member.name] = data.read()
    return files


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Verify review/REVIEW_INDEX.md against its anchor commit."
    )
    parser.add_argument("index", type=Path, help="Path to REVIEW_INDEX.md")
    parser.add_argument(
        "--root",
        type=Path,
        default=None,
        help="Repository root (default: parent of scripts/).",
    )
    args = parser.parse_args(argv)

    script_dir = Path(__file__).resolve().parent
    root = args.root.resolve() if args.root else script_dir.parent
    index_path = args.index if args.index.is_absolute() else root / args.index
    if not index_path.is_file():
        print(f"VERIFY_REVIEW_PACK: FAIL — index not found: {index_path}")
        return 1

    try:
        anchor, rows = _parse_index(index_path)
    except ValueError as exc:
        print(f"VERIFY_REVIEW_PACK: FAIL — {exc}")
        return 1

    print(f"anchor commit: {anchor}")
    print(f"index rows:    {len(rows)}")
    errors: list[str] = []

    check = _run(["git", "cat-file", "-t", anchor], cwd=root)
    if check.returncode != 0 or check.stdout.strip() != "commit":
        print(f"VERIFY_REVIEW_PACK: FAIL — anchor is not a commit: {anchor}")
        return 1

    try:
        tracked = _tracked_files(root, anchor)
    except ValueError as exc:
        print(f"VERIFY_REVIEW_PACK: FAIL — {exc}")
        return 1

    if DICT_NAME in " ".join(tracked):
        _fail(errors, f"tracked tree contains the excluded dictionary {DICT_NAME}")
    listed: set[str] = set()
    aggregate_rows = [r for r in rows if "*" in r["path"]]
    plain_rows = [r for r in rows if "*" not in r["path"]]

    for row in plain_rows:
        path = row["path"]
        listed.add(path)
        if path not in tracked:
            _fail(errors, f"listed file absent at anchor commit: {path}")
            continue
        data = tracked[path]
        if len(data) != row["size"]:
            _fail(
                errors,
                f"size mismatch: {path} (index {row['size']}, actual {len(data)})",
            )
        if _sha256(data) != row["sha256"]:
            _fail(errors, f"sha256 mismatch: {path}")
        if row["lines"] is not None and _lines(data) != row["lines"]:
            _fail(
                errors,
                f"line-count mismatch: {path} "
                f"(index {row['lines']}, actual {_lines(data)})",
            )

    # Aggregate rows: path is a glob over tracked files (fixture PNGs).
    covered_by_glob: set[str] = set()

    for row in aggregate_rows:
        pattern = row["path"]
        matched = sorted(p for p in tracked if fnmatch.fnmatch(p, pattern))
        if not matched:
            _fail(errors, f"aggregate row matches nothing: {pattern}")
            continue
        covered_by_glob.update(matched)
        total = sum(len(tracked[p]) for p in matched)
        # Lines in path order (matched is path-sorted); do not re-sort
        # the lines themselves — that would order by hash, not by path.
        agg_lines = [f"{_sha256(tracked[p])}  {p}\n" for p in matched]
        agg_sha = _sha256("".join(agg_lines).encode("utf-8"))
        if total != row["size"]:
            _fail(
                errors,
                f"aggregate size mismatch: {pattern} "
                f"(index {row['size']}, actual {total})",
            )
        if agg_sha != row["sha256"]:
            _fail(errors, f"aggregate sha256 mismatch: {pattern}")

    covered = listed | covered_by_glob
    missing = sorted(set(tracked) - covered)
    for path in missing:
        _fail(errors, f"tracked file not covered by index: {path}")
    extra = sorted(listed - set(tracked))
    for path in extra:
        _fail(errors, f"listed file is not tracked at anchor: {path}")

    if DICT_NAME in " ".join(listed):
        _fail(errors, "index lists the excluded dictionary")

    print(f"tracked files at anchor: {len(tracked)}")
    print(f"files covered:           {len(covered)}")
    if errors:
        print(f"VERIFY_REVIEW_PACK: FAIL ({len(errors)} problem(s))")
        return 1
    print("VERIFY_REVIEW_PACK: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
