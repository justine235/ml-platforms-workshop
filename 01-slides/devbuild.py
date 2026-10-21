"""Build one or more content modules on their own (fast loop while authoring).

    python devbuild.py content_p2            # -> out\\dev\\content_p2\\content_p2.pptx + slide-index.md
    python devbuild.py content_open content_close

Prints the slides built, the minutes per part (core / optional), the layout lint warnings and the problems that
would break the final assembly (wrong part prefix, missing notes, duplicate ids).
Every module gets its own folder under out\\dev, so several authors can work at the same time.
"""
from __future__ import annotations

import importlib
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
from deck_core import LINT  # noqa: E402
from deck_lib import PARTS, Deck  # noqa: E402

OWNS = {
    "content_open": {"O"},
    "content_p1": {"P1"},
    "content_p2": {"P2"},
    "content_p3": {"P3"},
    "content_p3b": {"P3"},
    "content_p4": {"P4"},
    "content_close": {"C", "A"},
}

# Part 3 is written by two modules: each may only create the ids of its own range, and has its own minutes target.
RANGES = {"content_p3": (0, 14), "content_p3b": (15, 25)}
TARGETS = {"content_p3": (55, 55), "content_p3b": (60, 5)}  # (total minutes, core minutes)


def check(name: str, d: Deck) -> list[str]:
    problems = []
    owned = OWNS.get(name)
    for slide, rec in zip(d.prs.slides, d.index):
        if owned and rec["part"] not in owned:
            problems.append(f"{rec['id']}: this module may only create slides of {sorted(owned)}")
        if name in RANGES and rec["part"] == "P3":
            lo, hi = RANGES[name]
            try:
                num = int(str(rec["id"]).split(".")[1])
            except (IndexError, ValueError):
                num = -1
            if not lo <= num <= hi:
                problems.append(f"{rec['id']}: this module may only create P3.{lo} to P3.{hi}")
        notes = slide.notes_slide.notes_text_frame.text.split("\n", 2)
        body = notes[2].strip() if len(notes) > 2 else ""
        if len(body.split()) < 40:
            problems.append(f"{rec['id']}: speaker notes are missing or too short ({len(body.split())} words)")
        if rec["minutes"] <= 0:
            problems.append(f"{rec['id']}: minutes must be > 0")
    return problems


def main(names: list[str]) -> int:
    bad = 0
    for name in names:
        LINT.clear()
        mod = importlib.import_module(name)
        d = Deck()
        mod.build(d)
        out = HERE / "out" / "dev" / name
        out.mkdir(parents=True, exist_ok=True)
        path = d.save(out / f"{name}.pptx")
        print(f"\n=== {name}: {len(d.index)} slides -> {path}")
        for part, rep in d.minutes_report().items():
            budget = PARTS[part][1]
            tot = rep["core"] + rep["optional"]
            if name in TARGETS:
                t_tot, t_core = TARGETS[name]
                print(f"    part {part}: {rep['slides']} slides, core {rep['core']:g} min + optional {rep['optional']:g} min "
                      f"= {tot:g} min (module target: total {t_tot} +-2, core {t_core} +-5)")
                continue
            print(f"    part {part}: {rep['slides']} slides, core {rep['core']:g} min + optional {rep['optional']:g} min "
                  f"= {tot:g} min (agenda {budget if budget else '-'})")
        problems = check(name, d)
        for line in LINT:
            print("    LINT", line)
        for line in problems:
            print("    PROBLEM", line)
        bad += len(LINT) + len(problems)
        if not LINT and not problems:
            print("    clean: no lint warnings, no problems")
    return 1 if bad else 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    sys.exit(main(sys.argv[1:]))
