#!/usr/bin/env python3
"""Regenerate PROJECT_BOOK.docx from PROJECT_BOOK.md (P033 FIX-R1-01).

Replicates the conventions of the original DOCX (built 2026-11-25 from the
pre-T013 MD), verified against that file with python-docx before writing
this script:

- ``# ``    -> Title style; ``## `` -> Heading 2; ``### `` -> Heading 3.
  Heading text is plain (no inline parsing; MD headings contain no markers).
- ``> ...`` blockquote lines -> Normal paragraph, literal text, NO inline
  parsing (``**`` and backticks stay verbatim, as in the original file).
- Plain / bullet (``- ``) / numbered (``N. ``) lines -> Normal / List Bullet /
  List Number paragraph with inline parsing: ``**bold**`` -> bold YaHei run,
  ``` `code` ``` -> Consolas run, rest -> Microsoft YaHei run.
- ``---`` -> one empty Normal paragraph.
- Fenced code block -> ONE Normal paragraph, whole block joined with ``\\n``,
  single Consolas run (python-docx turns ``\\n`` into line breaks).
- Table (consecutive ``|`` lines): separator row skipped; first row is the
  header (bold runs); style ``Table Grid``; cell text uses the same inline
  parsing as body text. One empty Normal paragraph follows each table.
- Blank MD lines are skipped; every other non-blank line becomes exactly one
  paragraph; trailing whitespace is stripped.

Expected output for the frozen 1.0.0 MD (776 lines, 2026-11-25):
Title 1 + Heading 66 = 67 styled heading paragraphs, 14 tables, heading
texts in the same order as the MD's 67 ``#`` headings (sections 0-16).

Usage:
    python3 scripts/md_to_docx.py [MD_PATH] [DOCX_PATH]
Defaults: PROJECT_BOOK.md / PROJECT_BOOK.docx in the worktree root.
"""

import re
import sys
from pathlib import Path

from docx import Document
from docx.oxml.ns import qn

BODY_FONT = "Microsoft YaHei"
CODE_FONT = "Consolas"

INLINE_RE = re.compile(r"(\*\*.+?\*\*|`[^`]+`)")
TABLE_SEP_RE = re.compile(r"^:?-+:?$")
NUMBERED_RE = re.compile(r"^\d+\.\s+")


def set_run(run, font, bold=False):
    """Set latin + East-Asian font name on a run (CJK text needs eastAsia)."""
    run.font.name = font
    run.bold = bold
    r_pr = run._element.get_or_add_rPr()
    r_fonts = r_pr.find(qn("w:rFonts"))
    if r_fonts is None:
        r_fonts = r_pr.makeelement(qn("w:rFonts"), {})
        r_pr.append(r_fonts)
    r_fonts.set(qn("w:eastAsia"), font)


def add_inline(paragraph, text, base_bold=False):
    """Append runs for *text*, parsing ``**bold**`` and ``` `code` ```."""
    pos = 0
    for match in INLINE_RE.finditer(text):
        if match.start() > pos:
            run = paragraph.add_run(text[pos:match.start()])
            set_run(run, BODY_FONT, bold=base_bold)
        token = match.group(0)
        if token.startswith("**"):
            run = paragraph.add_run(token[2:-2])
            set_run(run, BODY_FONT, bold=True)
        else:
            run = paragraph.add_run(token[1:-1])
            set_run(run, CODE_FONT, bold=base_bold)
        pos = match.end()
    if pos < len(text):
        run = paragraph.add_run(text[pos:])
        set_run(run, BODY_FONT, bold=base_bold)


def parse_table_row(line):
    """Split a ``| a | b |`` line into stripped cell texts."""
    cells = line.strip().strip("|").split("|")
    return [cell.strip() for cell in cells]


def is_separator_row(cells):
    return cells and all(TABLE_SEP_RE.match(cell) for cell in cells)


def md_to_docx(md_path, docx_path):
    lines = Path(md_path).read_text(encoding="utf-8").split("\n")
    doc = Document()
    stats = {"title": 0, "heading": 0, "table": 0, "paragraph": 0}

    i = 0
    while i < len(lines):
        line = lines[i].rstrip()
        i += 1

        if not line:
            continue
        if line.strip() == "---":
            doc.add_paragraph(style="Normal")
            stats["paragraph"] += 1
            continue
        if line.startswith("```"):
            lang = line[3:].strip()
            buf = []
            while i < len(lines) and not lines[i].startswith("```"):
                buf.append(lines[i].rstrip())
                i += 1
            i += 1  # skip closing fence
            para = doc.add_paragraph(style="Normal")
            run = para.add_run("\n".join(buf))
            set_run(run, CODE_FONT)
            stats["paragraph"] += 1
            continue
        if line.startswith("# "):
            para = doc.add_paragraph(style="Title")
            run = para.add_run(line[2:].strip())
            set_run(run, BODY_FONT)
            stats["title"] += 1
            continue
        if line.startswith("## "):
            para = doc.add_paragraph(style="Heading 2")
            run = para.add_run(line[3:].strip())
            set_run(run, BODY_FONT)
            stats["heading"] += 1
            continue
        if line.startswith("### "):
            para = doc.add_paragraph(style="Heading 3")
            run = para.add_run(line[4:].strip())
            set_run(run, BODY_FONT)
            stats["heading"] += 1
            continue
        if line.startswith("|"):
            rows = []
            while True:
                rows.append(parse_table_row(line))
                if i < len(lines) and lines[i].strip().startswith("|"):
                    line = lines[i].rstrip()
                    i += 1
                else:
                    break
            rows = [r for r in rows if not is_separator_row(r)]
            table = doc.add_table(rows=0, cols=len(rows[0]))
            table.style = "Table Grid"
            for r_idx, row in enumerate(rows):
                cells = table.add_row().cells
                for c_idx, cell_text in enumerate(row):
                    para = cells[c_idx].paragraphs[0]
                    add_inline(para, cell_text, base_bold=(r_idx == 0))
            doc.add_paragraph(style="Normal")  # empty paragraph after table
            stats["table"] += 1
            stats["paragraph"] += 1
            continue
        if line.startswith("> "):
            para = doc.add_paragraph(style="Normal")
            run = para.add_run(line[2:])
            set_run(run, BODY_FONT)
            stats["paragraph"] += 1
            continue
        if line.startswith("- "):
            para = doc.add_paragraph(style="List Bullet")
            add_inline(para, line[2:])
            stats["paragraph"] += 1
            continue
        if NUMBERED_RE.match(line):
            para = doc.add_paragraph(style="List Number")
            add_inline(para, NUMBERED_RE.sub("", line, count=1))
            stats["paragraph"] += 1
            continue
        para = doc.add_paragraph(style="Normal")
        add_inline(para, line)
        stats["paragraph"] += 1

    doc.save(str(docx_path))
    return stats


def main(argv):
    root = Path(__file__).resolve().parent.parent
    md_path = Path(argv[1]) if len(argv) > 1 else root / "PROJECT_BOOK.md"
    docx_path = Path(argv[2]) if len(argv) > 2 else root / "PROJECT_BOOK.docx"
    stats = md_to_docx(md_path, docx_path)
    print(f"wrote {docx_path} ({docx_path.stat().st_size} bytes)")
    print(f"Title={stats['title']} Heading={stats['heading']} "
          f"tables={stats['table']} other_paragraphs={stats['paragraph']}")


if __name__ == "__main__":
    main(sys.argv)
