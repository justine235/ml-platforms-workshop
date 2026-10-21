"""Dump every slide's text and speaker notes to Markdown, for proofreading and number checks.

    python dump_text.py out\\dev\\content_p2\\content_p2.pptx [out.md]

Also flags: broken characters (mojibake), double spaces, very dense slides (> 70 body words outside tables and code),
and numbers with more than 4 digits that are not written with a thousands separator.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

from pptx import Presentation
from pptx.util import Emu

SKIP = ("footer", "eyebrow", "takeaway tag")
MOJIBAKE = re.compile("[\u00c2\u00c3\u00e2][\u0080-\u00bf\u20ac\u2122\u0153\u00a0-\u00bf]|\ufffd")


def shape_text(sh) -> str:
    if sh.has_text_frame:
        return "\n".join(p.text for p in sh.text_frame.paragraphs if p.text.strip())
    if getattr(sh, "has_table", False) and sh.has_table:
        rows = [" | ".join(c.text.replace("\n", " / ") for c in r.cells) for r in sh.table.rows]
        return "\n".join(rows)
    return ""


def main(path: str, out: str | None) -> None:
    prs = Presentation(path)
    lines = [f"# Text dump of {Path(path).name}", ""]
    warnings = []
    for n, slide in enumerate(prs.slides, 1):
        notes = slide.notes_slide.notes_text_frame.text if slide.has_notes_slide else ""
        head = notes.split("\n", 1)[0]
        title = slide.shapes.title.text_frame.text if slide.shapes.title is not None else ""
        lines += [f"## {n}. {head}  {title}", ""]
        shapes = [s for s in slide.shapes if shape_text(s) and not s.name.startswith(SKIP) and s != slide.shapes.title]
        shapes.sort(key=lambda s: (round(Emu(s.top).inches, 1), Emu(s.left).inches))
        body_words = 0
        for s in shapes:
            t = shape_text(s)
            is_dense_exempt = s.name.startswith(("code", "table")) or getattr(s, "has_table", False)
            if not is_dense_exempt:
                body_words += len(t.split())
            lines.append(f"- **{s.name}**: " + t.replace("\n", " / "))
        notes_body = notes.split("\n", 2)[2].strip() if notes.count("\n") >= 2 else ""
        lines += ["", "Notes:", "", notes_body or "(none)", ""]
        everything = "\n".join([title] + [shape_text(s) for s in shapes] + [notes])
        if MOJIBAKE.search(everything):
            warnings.append(f"slide {n} ({head}): broken characters")
        if "  " in title or re.search(r"[^\s]  [^\s]", "\n".join(shape_text(s) for s in shapes if s.name.startswith("bullet"))):
            warnings.append(f"slide {n} ({head}): double space")
        if body_words > 70:
            warnings.append(f"slide {n} ({head}): dense slide, {body_words} body words")
        if re.search(r"(?<![\d,.])\d{5,}(?![\d,])", everything):
            warnings.append(f"slide {n} ({head}): number with 5+ digits and no thousands separator")
        if len(notes_body.split()) < 40:
            warnings.append(f"slide {n} ({head}): notes shorter than 40 words")
    lines += ["", "## Warnings", ""] + (["- " + w for w in warnings] or ["none"])
    text = "\n".join(lines) + "\n"
    if out:
        Path(out).write_text(text, encoding="utf-8", newline="\n")
        print(f"wrote {out}")
    print("\n".join(warnings) if warnings else "no text warnings")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
