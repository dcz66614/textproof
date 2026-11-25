#!/usr/bin/env python3
"""Generate review/REVIEW_INDEX.md for a given anchor commit (FIX-R1).

Replicates the T014 R3 index format exactly, so that
``scripts/verify_review_pack.py`` passes on the output:

- one row per tracked file at the anchor commit (via ``git archive``,
  never the possibly dirty working tree): path, byte size, SHA-256,
  line count (``wc -l`` semantics: number of newline bytes);
- one aggregate row for the 300 S0 fixture PNGs
  (``tests/fixtures/s0/*.png``): total bytes, and SHA-256 of the
  joined ``"<sha256>  <path>"`` lines in path-sorted order;
- header records the anchor commit, coverage counts, the verification
  command, and the notes that the index itself and the review packs
  are not in the anchor commit (they are release evidence committed
  afterwards; their hashes are recorded in RELEASE_MANIFEST.json).

Usage::

    python task_handoffs/FIX-R1/generate_review_index.py <anchor-commit> \\
        --branch <branch> --out review/REVIEW_INDEX.md
"""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import io
import subprocess
import sys
import tarfile
from pathlib import Path

DICT_NAME = "ppocrv6_dict.txt"
PNG_GLOB = "tests/fixtures/s0/*.png"


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _lines(data: bytes) -> int:
    return data.count(b"\n")


def _tracked_files(root: Path, anchor: str) -> dict[str, bytes]:
    archive = subprocess.run(
        ["git", "archive", anchor], cwd=str(root), capture_output=True
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
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("anchor", help="anchor commit (full 40-hex SHA)")
    parser.add_argument("--branch", required=True, help="branch the anchor is on")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--root", type=Path, default=Path("."))
    args = parser.parse_args(argv)
    root = args.root.resolve()

    tracked = _tracked_files(root, args.anchor)
    if DICT_NAME in " ".join(tracked):
        print(f"FAIL: tracked tree contains excluded dictionary {DICT_NAME}")
        return 1
    pngs = sorted(p for p in tracked if fnmatch.fnmatch(p, PNG_GLOB))
    if len(pngs) != 300:
        print(f"FAIL: expected 300 S0 fixture PNGs, found {len(pngs)}")
        return 1
    plain = sorted(p for p in tracked if p not in pngs)

    total = len(tracked)
    agg_lines = [f"{_sha256(tracked[p])}  {p}\n" for p in pngs]
    agg_sha = _sha256("".join(agg_lines).encode("utf-8"))
    agg_size = sum(len(tracked[p]) for p in pngs)

    lines: list[str] = []
    lines.append("# P033 TextProof — FIX-R1 发布审查索引（REVIEW_INDEX.md)")
    lines.append("")
    lines.append(
        f"- 锚定 commit：`{args.anchor}`（分支 `{args.branch}`；FIX-R1 重冻源码 commit，含终审 R1 的 P1-01/P1-02/P1-03 与两项 P2 修复）"
    )
    lines.append(
        "- 审查报告：`review/REVIEW_PACK_FIXR1.md`（本次重冻的定稿说明；旧包 `review/REVIEW_PACK_T014.md`、`review/REVIEW_PACK_T014R2.md`、`review/REVIEW_PACK_T014R3.md` 原文保留，T014 包另有 §9 FIX-R1 增补）"
    )
    lines.append(
        "- 本表每行的字节数、SHA-256、行数均取自锚定 commit 本身（`git archive <commit>`），不受工作树脏文件影响；行数按 `wc -l` 口径（换行符个数）。"
    )
    lines.append(
        f"- 覆盖率：**全文列 {len(plain)} / 锚定 commit 追踪文件总数 {total}**；其余 300 张 fixture PNG 以一行聚合记录（逐文件 SHA 见 `tests/fixtures/s0/manifest.json`，由 `scripts/verify_s0.py` 全量重算验证）。"
    )
    lines.append(
        "- 校验命令：`python scripts/verify_review_pack.py review/REVIEW_INDEX.md`（逐行核对路径、字节数、SHA-256、行数，并核对覆盖完整性）。"
    )
    lines.append(
        "- 本索引本身与 `review/REVIEW_PACK_FIXR1.md` 不在锚定 commit 内（它们是 FIX-R1 发布证据，在随后的 release 提交中入库）；其哈希见 `release/RELEASE_MANIFEST.json`。`review/REVIEW_PACK_T014.md`（含 §9 FIX-R1 增补）在锚定 commit 内。"
    )
    lines.append(
        "- 字典 `assets/ocr/dictionaries/ppocrv6_dict.txt` 不在锚定 commit 内（T014/R-03 起不再追踪，见 `THIRD_PARTY_NOTICES.md` §4），故本表无此行；它是唯一被排除的源文件。"
    )
    lines.append(
        "- `release/` 生成物（source.zip、wheel、wheelhouse、清单）自 FIX-R1 起不再入库（终审 R1 P3：嵌套入库使 source.zip 达 512MB）；锚定 commit 的追踪文件不含 `release/`，故本表无此目录。"
    )
    lines.append("")
    lines.append("## 1. 覆盖表")
    lines.append("")
    lines.append("| 文件 | 字节数 | SHA-256 | 行数 | 读取状态 | 备注 |")
    lines.append("|---|---:|---|---|---|---|")
    for path in plain:
        data = tracked[path]
        lines.append(
            f"| `{path}` | {len(data)} | `{_sha256(data)}` | {_lines(data)} | 已列 | 冻结源码 commit 文件 |"
        )
    lines.append(
        f"| `{PNG_GLOB}` | {agg_size} | `{agg_sha}` | — | 聚合行 | 300 张 S0 fixture PNG 的聚合记录：字节数为合计，SHA-256 为按路径排序的 `\"<sha256>  <path>\"` 行的 SHA-256；逐文件 SHA 见 manifest.json |"
    )
    lines.append("")
    lines.append("## 2. 备注")
    lines.append("")
    lines.append(
        "- `review/` 与 `release/` 的生成物不在锚定 commit 内：它们由锚定 commit 的内容生成，其哈希由 `release/RELEASE_MANIFEST.json` 与 `verify_release.py` 校验。"
    )
    lines.append(
        "- DOCX 同步：结构（标题 67/40、表格 14/4、顺序）已核对同步；`PROJECT_BOOK.md` 的 7 处 T013 文字澄清已进 DOCX（FIX-R1 用 `scripts/md_to_docx.py` 从当前 MD 重新生成，见 REVIEW_PACK_T014 §9 与 REVIEW_PACK_FIXR1.md §1；终审 R1 P1-01 已关闭）。"
    )
    lines.append(
        "- source.zip 体积：锚定 commit 不再包含 `release/` 生成物，`git archive` 产物不再嵌套旧 release 快照（终审 R1 P3 已解决；见 REVIEW_PACK_FIXR1.md §1）。"
    )
    lines.append(
        "- U-03 已解决：`omegaconf` 2.4.0 按其 wheel 内附 LICENSE 文件记为 BSD-3-Clause（见 `release/SBOM_LICENSES.md`）。"
    )
    lines.append(
        "- 外部 URL 内容（RapidOCR 许可页、ModelScope、PaddleOCR 上游）未验证可达性——哈希与本地文件一致已核（T012 残余风险，原文保留）。"
    )
    lines.append("")
    args.out.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {args.out}: {len(plain)} plain rows + 1 aggregate row, "
          f"total tracked {total}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
