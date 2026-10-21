"""Assemble the whole workshop deck from the content modules, check it and write the outputs.

    python build_deck.py              strict: every module must exist and every check must pass (exit 1 otherwise)
    python build_deck.py --draft      build with the modules that exist so far; what is missing is reported, not fatal
    python build_deck.py --out DIR    write the files into DIR (default: this folder)

Writes
    ml-platforms-workshop.pptx            the full-day deck
    ml-platforms-workshop-halfday.pptx    the same slides with the optional ones hidden (core path only)
    slide-index.md                        one row per slide (id, layout, minutes, core/optional, headline)
    build-report.md                       minutes per part, problems, lint warnings, numbers to double-check
"""
from __future__ import annotations

import argparse
import importlib
import re
import sys
import traceback
from pathlib import Path
from types import SimpleNamespace

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import facts  # noqa: E402
from deck_core import LINT  # noqa: E402
from deck_lib import PARTS, Deck  # noqa: E402
from devbuild import OWNS, RANGES  # noqa: E402
from pptx.enum.shapes import MSO_SHAPE_TYPE  # noqa: E402

MODULES = ["content_open", "content_p1", "content_p2", "content_p3", "content_p3b", "content_p4", "content_close"]
EXPECTED = {
    "O": [f"O{i}" for i in range(1, 6)],
    "P1": [f"P1.{i}" for i in range(0, 20)],
    "P2": [f"P2.{i}" for i in range(0, 21)],
    "P3": [f"P3.{i}" for i in range(0, 26)],
    "P4": [f"P4.{i}" for i in range(0, 18)],
    "C": [f"C{i}" for i in range(1, 5)],
    "A": [f"A{i}" for i in range(0, 11)],
}
CORE_TARGET = {"O": 16, "P1": 45, "P2": 30, "P3": 60, "P4": 50, "C": 10}
TOTAL_TOL, CORE_TOL = 3, 5
FORBIDDEN = {
    "customer name": re.compile(r"\b" + "vi" + "nci" + r"\b", re.I),
    "mojibake": re.compile("\ufffd|\u00c3[\u00a0-\u00bf]|\u00e2\u20ac"),
    "placeholder text": re.compile(r"\b(TODO|TBD|FIXME|lorem ipsum)\b", re.I),
}
NUMBER = re.compile(r"(?<![\d.,])(?:\d{1,3}(?:,\d{3})+|\d{4,})(?![\d.]*\d)")


def shape_texts(shapes):
    for sh in shapes:
        try:
            is_group = sh.shape_type == MSO_SHAPE_TYPE.GROUP
        except NotImplementedError:
            is_group = False
        if is_group:
            yield from shape_texts(sh.shapes)
            continue
        if sh.has_text_frame:
            yield sh.text_frame.text
        if getattr(sh, "has_table", False) and sh.has_table:
            for row in sh.table.rows:
                for cell in row.cells:
                    yield cell.text


def canonical_numbers():
    vals: set[str] = set()

    def walk(x):
        if isinstance(x, SimpleNamespace):
            walk(vars(x))
        elif isinstance(x, dict):
            for v in x.values():
                walk(v)
        elif isinstance(x, (list, tuple)):
            for v in x:
                walk(v)
        elif isinstance(x, int) and not isinstance(x, bool):
            vals.update({str(abs(x)), f"{abs(x):,}"})

    walk(facts.GT)
    walk(facts.F)
    return vals


def slide_no(sid: str) -> int:
    return int(re.search(r"(\d+)$", sid).group(1))


def check_module(name, d, lo, hi):
    out = []
    owned = OWNS.get(name)
    for i in range(lo, hi):
        rec, slide = d.index[i], d.prs.slides[i]
        if owned and rec["part"] not in owned:
            out.append(f"{rec['id']}: module {name} may only create slides of {sorted(owned)}")
        if name in RANGES and rec["part"] == "P3":
            a, b = RANGES[name]
            if not a <= slide_no(rec["id"]) <= b:
                out.append(f"{rec['id']}: module {name} may only create P3.{a} to P3.{b}")
        notes = slide.notes_slide.notes_text_frame.text.split("\n", 2)
        words = len(notes[2].split()) if len(notes) > 2 else 0
        if words < 40:
            out.append(f"{rec['id']}: speaker notes are missing or too short ({words} words)")
        if rec["minutes"] <= 0:
            out.append(f"{rec['id']}: minutes must be > 0")
    return out


def build_all(draft):
    d = Deck()
    problems, warnings, lint, built = [], [], [], []
    for name in MODULES:
        try:
            mod = importlib.import_module(name)
        except Exception as e:  # noqa: BLE001 - a module being edited may not even import
            (warnings if draft else problems).append(f"{name}: cannot be imported ({type(e).__name__}: {e})")
            continue
        LINT.clear()
        start = len(d.index)
        try:
            mod.build(d)
        except Exception as e:  # noqa: BLE001
            traceback.print_exc()
            problems.append(f"{name}: build() raised {type(e).__name__}: {e}")
            break
        lint += [f"{name}: {line}" for line in LINT]
        problems += check_module(name, d, start, len(d.index))
        built.append(name)
    return d, problems, warnings, lint, built


def check_ids(d, draft, problems, warnings):
    present: dict[str, list[str]] = {}
    for rec in d.index:
        present.setdefault(rec["part"], []).append(rec["id"])
    for part, want in EXPECTED.items():
        got = present.get(part, [])
        extra = [s for s in got if s not in want]
        missing = [s for s in want if s not in got]
        if extra:
            problems.append(f"part {part}: unexpected slide ids {extra}")
        if got != sorted(got, key=slide_no):
            problems.append(f"part {part}: slides are not in id order ({', '.join(got)})")
        if missing:
            (warnings if draft else problems).append(f"part {part}: missing slide ids {missing}")


def check_minutes(d, draft, problems, warnings):
    rows, rep = [], d.minutes_report()
    sink = warnings if draft else problems
    for part, (_, agenda) in PARTS.items():
        r = rep.get(part)
        target = CORE_TARGET.get(part)
        if not r:
            rows.append((part, 0, 0.0, 0.0, agenda, target, "missing"))
            continue
        total, status = r["core"] + r["optional"], []
        if agenda and abs(total - agenda) > TOTAL_TOL:
            status.append("total off")
            sink.append(f"part {part}: {total:g} min in the deck, {agenda} in the agenda (tolerance +-{TOTAL_TOL})")
        if target and abs(r["core"] - target) > CORE_TOL:
            status.append("core off")
            sink.append(f"part {part}: core path is {r['core']:g} min, target {target} (tolerance +-{CORE_TOL})")
        rows.append((part, r["slides"], r["core"], r["optional"], agenda, target, ", ".join(status) or "ok"))
    return rows


def scan_text(d, problems):
    known, review = canonical_numbers(), []
    for rec, slide in zip(d.index, d.prs.slides):
        blob = "\n".join(list(shape_texts(slide.shapes)) + [slide.notes_slide.notes_text_frame.text])
        for label, rx in FORBIDDEN.items():
            m = rx.search(blob)
            if m:
                problems.append(f"{rec['id']}: {label} found ({m.group(0)!r})")
        odd = sorted({t for t in NUMBER.findall(blob)
                      if t not in known and t.replace(",", "") not in known and not re.fullmatch(r"(19|20)\d\d", t)})
        if odd:
            review.append((rec["id"], odd))
    return review


def write_report(path, d, rows, problems, warnings, lint, review, built):
    L = ["# Build report", "", f"- Modules built: {', '.join(built) or 'none'}", f"- Slides: {len(d.index)}",
         f"- Problems: {len(problems)}   Lint warnings: {len(lint)}   Warnings: {len(warnings)}", "",
         "## Minutes per part", "", "| part | slides | core min | optional min | total | agenda | core target | status |",
         "|---|---|---|---|---|---|---|---|"]
    for part, n, core, opt, agenda, target, status in rows:
        L.append(f"| {part} | {n} | {core:g} | {opt:g} | {core + opt:g} | {agenda or '-'} | {target or '-'} | {status} |")
    for title, items in (("Problems (must be fixed)", problems), ("Lint warnings", lint), ("Warnings", warnings)):
        L += ["", f"## {title}", ""] + ([f"- {x}" for x in items] or ["none"])
    L += ["", "## Numbers with 4+ digits that are not in ground_truth.json or facts.py (check each one by hand)", ""]
    L += [f"- {sid}: {', '.join(odd)}" for sid, odd in review] or ["none"]
    path.write_text("\n".join(L) + "\n", encoding="utf-8", newline="\n")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--draft", action="store_true", help="tolerate missing modules, slides and minutes")
    ap.add_argument("--out", default=str(HERE), help="output folder (default: this folder)")
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)

    d, problems, warnings, lint, built = build_all(a.draft)
    check_ids(d, a.draft, problems, warnings)
    rows = check_minutes(d, a.draft, problems, warnings)
    review = scan_text(d, problems)

    full = d.save(out / "ml-platforms-workshop.pptx")
    for slide, rec in zip(d.prs.slides, d.index):
        if not rec["core"]:
            slide._element.set("show", "0")
    half = out / "ml-platforms-workshop-halfday.pptx"
    d.prs.save(str(half))
    write_report(out / "build-report.md", d, rows, problems, warnings, lint, review, built)

    hidden = sum(1 for r in d.index if not r["core"])
    print(f"{len(d.index)} slides ({hidden} optional) from {len(built)} modules -> {full.name}, {half.name}")
    for part, n, core, opt, agenda, target, status in rows:
        print(f"  {part:<3} {n:>3} slides  core {core:>5g}  optional {opt:>5g}  total {core + opt:>5g}  "
              f"(agenda {agenda or '-'}, core target {target or '-'})  {status}")
    for label, items in (("PROBLEM", problems), ("LINT", lint), ("WARNING", warnings)):
        for x in items:
            print(f"  {label}: {x}")
    print(f"  {len(review)} slides have numbers to double-check, see build-report.md")
    clean = not problems and (a.draft or not lint)
    print("  RESULT: " + ("clean" if clean and not warnings else "clean with warnings" if clean else "NOT CLEAN"))
    return 0 if clean else 1


if __name__ == "__main__":
    sys.exit(main())
