"""Build the presenter's slide-by-slide clock from slide-index.md.

    python make_timeline.py [--index slide-index.md] [--out ..\\00-presenter-guide\\02-slide-timeline.md]

The clock is the full-day plan: each part starts at its fixed time and each slide takes the minutes in the index.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent

PARTS = [
    ("O", "Opening", "09:00", 20),
    ("P1", "Part 1: Fabric vs Azure ML, MLflow in both", "09:20", 90),
    ("P2", "Part 2: MLOps concepts", "11:05", 75),
    ("P3", "Part 3: End to end on Fabric, then on Azure ML", "13:20", 115),
    ("P4", "Part 4: Foundry and the data agent", "15:30", 75),
    ("C", "Wrap-up", "16:45", 15),
]
AFTER_PART = {"P1": ("10:50", 15, "Break"), "P2": ("12:20", 60, "Lunch"), "P3": ("15:15", 15, "Break")}
MARKS = {"P3.15": "Azure ML and bridge block starts. Target clock: 14:15"}
ROW = re.compile(r"^\|\s*(\d+)\s*\|\s*([A-Z]+\d*(?:\.\d+)?)\s*\|\s*(\w+)\s*\|\s*([\d.]+)\s*\|\s*(yes|optional)\s*\|\s*(.*?)\s*\|\s*$")


def hm(minutes: float) -> str:
    m = int(round(minutes))
    return f"{m // 60:02d}:{m % 60:02d}"


def start_minutes(text: str) -> int:
    h, m = text.split(":")
    return int(h) * 60 + int(m)


def part_of(slide_id: str) -> str:
    return slide_id.split(".")[0] if slide_id.startswith("P") else slide_id[0]


def fmt(x: float) -> str:
    return f"{x:g}"


def parse(index: Path) -> dict[str, list[dict]]:
    slides: dict[str, list[dict]] = {}
    for line in index.read_text(encoding="utf-8").splitlines():
        m = ROW.match(line)
        if not m:
            continue
        num, sid, layout, minutes, core, headline = m.groups()
        slides.setdefault(part_of(sid), []).append(
            dict(n=int(num), id=sid, layout=layout, min=float(minutes), core=core == "yes", headline=headline))
    return slides


def render(slides: dict[str, list[dict]]) -> str:
    out = [
        "# Slide-by-slide clock",
        "",
        "Generated from `01-slides/slide-index.md` by `01-slides/make_timeline.py`. Do not edit by hand: rebuild the deck, then run the script again.",
        "",
        "How to read it",
        "- **Start** is the clock time if every slide takes its planned minutes. Parts have fixed start times, so a slide that overruns eats the next one, not the break.",
        "- **Core** slides are the half-day path. **Optional** slides are the first to cut (`01-day-plan.md`, section 4).",
        "- **Demo** slides are bold. Their minutes are the budget in the full-day plan; the short paths are in `01-day-plan.md`, section 3.",
        "",
    ]
    half_rows = []
    for key, label, start, budget in PARTS:
        rows = slides.get(key, [])
        t0 = start_minutes(start)
        total = sum(r["min"] for r in rows)
        core_total = sum(r["min"] for r in rows if r["core"])
        out += [f"## {label}", "", f"Starts {start}, ends {hm(t0 + budget)} (budget {budget} min).", "",
                "| Start | Slide | Min | Core | What it says |", "|---|---|---:|---|---|"]
        t = float(t0)
        for r in rows:
            if r["id"] in MARKS:
                out.append(f"| | | | | *{MARKS[r['id']]}* |")
            sid = f"**{r['id']}**" if r["layout"] == "demo" else r["id"]
            out.append(f"| {hm(t)} | {sid} | {fmt(r['min'])} | {'core' if r['core'] else 'optional'} | {r['headline']} |")
            t += r["min"]
        flag = "" if abs(total - budget) <= 3 else f"  **Check: budget is {budget}.**"
        out += ["", f"{len(rows)} slides, {fmt(total)} min in total, {fmt(core_total)} min core, "
                f"{fmt(total - core_total)} min optional.{flag}", ""]
        half_rows.append((label, sum(1 for r in rows if r["core"]), core_total))
        if key in AFTER_PART:
            at, length, name = AFTER_PART[key]
            out += [f"**{at}: {name} ({length} min).**", ""]
    out += ["## Half-day path (core slides only)", "", "| Block | Core slides | Core min |", "|---|---:|---:|"]
    m_total = 0.0
    for label, n_core, minutes in half_rows:
        out.append(f"| {label} | {n_core} | {fmt(minutes)} |")
        m_total += minutes
    out += [f"| **Total** | | **{fmt(m_total)}** |", "",
            "Add one break of about 15 minutes. Use `ml-platforms-workshop-halfday.pptx`.", ""]
    appendix = slides.get("A", [])
    if appendix:
        out += ["## Appendix (not on the clock)", "", "Open these only to answer a question.", "",
                "| Slide | What it says |", "|---|---|"]
        out += [f"| {r['id']} | {r['headline']} |" for r in appendix]
        out.append("")
    return "\n".join(out)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--index", default=str(HERE / "slide-index.md"))
    ap.add_argument("--out", default=str(HERE.parent / "00-presenter-guide" / "02-slide-timeline.md"))
    args = ap.parse_args()
    slides = parse(Path(args.index))
    text = render(slides)
    Path(args.out).write_text(text, encoding="utf-8", newline="\n")
    print(f"wrote {args.out}: {sum(len(v) for v in slides.values())} slides")


if __name__ == "__main__":
    main()
