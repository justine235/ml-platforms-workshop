"""Assemble the W1 edition of the workshop deck from the presenter's edited copy.

Input : the presenter's edited .pptx (his own selection and order of slides, his own pasted slides and his sticky
        notes). It is a binary input and is not stored in the repo, so pass it with --src.
Output: 01-slides/ml-platforms-workshop-W1.pptx and 01-slides/slide-index-W1.md

What it does
  1. keeps the slides he selected and fixes them in place (typos, wording, sticky-note requests, eyebrows);
  2. rebuilds his own pasted slides as native, editable shapes in the same visual identity: the agenda, the divider
     slides, the open-talk slides and the Azure ML slide are authored here, the MLOps and Part 3 slides come from
     w1_part2a, w1_part2b, w1_part3a and w1_part3b;
  3. reorders everything, drops the replaced slides and the two imported slide masters.

The standard build (python build_deck.py) does not use any of this and is not affected.

    python build_w1.py --src "path\\to\\edited-deck.pptx" [--out ml-platforms-workshop-W1.pptx]
"""
from __future__ import annotations

import argparse
import importlib
import io
import re
import sys
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path

import pptx
from lxml import etree
from PIL import Image
from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE
from pptx.oxml.ns import qn
from pptx.util import Inches

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))

from content_p1 import AML_MLFLOW_URLS  # noqa: E402
from deck_core import HEAD, LINT, MONO, box, card, num_badge, pill, text  # noqa: E402
from deck_lib import Deck  # noqa: E402
from deck_theme import layout_by_name  # noqa: E402
from make_timeline import PARTS, hm, start_minutes  # noqa: E402

N_SRC_SLIDES = 66
MODULES = ["w1_part2a", "w1_part2b", "w1_part3a", "w1_part3b"]
EYEBROW = {
    1: "PART 1  \u00b7  FABRIC VS AZURE ML",
    2: "PART 2  \u00b7  MLOPS CONCEPTS",
    3: "PART 3  \u00b7  MLOPS IN FABRIC AND AML",
}

# Final order: ("U", n) keeps slide n of the edited deck, ("N", id) is a slide built here or by a module.
ORDER = [
    ("U", 1), ("N", "O2"), ("N", "O2b"),
    ("N", "P1.0"), ("U", 5), ("U", 6), ("N", "P1.3"), ("U", 8), ("U", 9), ("U", 10), ("U", 11), ("U", 12),
    ("U", 13), ("U", 14), ("U", 15), ("U", 16), ("U", 17), ("N", "P1.19"),
    ("N", "P2.0"), ("N", "P2.21"), ("N", "P2.22"), ("N", "P2.23"), ("N", "P2.24"), ("N", "P2.25"), ("U", 25),
    ("N", "P2.31"), ("N", "P2.32"), ("N", "P2.33"), ("U", 29), ("N", "P2.26"),
    ("N", "P2.34"), ("N", "P2.35"), ("N", "P2.36"), ("U", 33), ("N", "P2.19"),
    ("N", "P3.0"), ("N", "P3.31"), ("N", "P3.32"), ("N", "P3.33"), ("N", "P3.34"),
    ("N", "P3.41"), ("N", "P3.42"), ("N", "P3.43"), ("N", "P3.44"), ("N", "P3.45"), ("N", "P3.46"), ("N", "P3.47"),
    ("U", 46), ("U", 47), ("U", 48), ("U", 49), ("U", 53), ("N", "P3.19"), ("N", "P3.48"),
    ("N", "P4.0"), *[("U", n) for n in range(54, 67)],
]

LOG: list[str] = []


# ---------------------------------------------------------------------------------------------- patch helpers
def title_of(slide) -> str:
    t = slide.shapes.title
    return t.text_frame.text.strip() if t is not None else "?"


def find(slide, key):
    """One shape, by numeric id or exact name."""
    hits = [s for s in slide.shapes if (s.shape_id == key if isinstance(key, int) else s.name == key)]
    if len(hits) != 1:
        sys.exit(f"patch failed: {len(hits)} shapes match {key!r} on the slide titled {title_of(slide)!r}")
    return hits[0]


def para_with(shape, needle):
    hits = [p for p in shape.text_frame.paragraphs if needle in "".join(r.text for r in p.runs)]
    if len(hits) != 1:
        sys.exit(f"patch failed: {len(hits)} paragraphs contain {needle!r} in shape {shape.name!r}")
    return hits[0]


def set_text(paragraph, new):
    """Replace the text of a paragraph and keep the formatting of its first run."""
    runs = paragraph.runs
    runs[0].text = new
    for r in runs[1:]:
        r._r.getparent().remove(r._r)


def set_runs(paragraph, texts):
    runs = paragraph.runs
    if len(runs) != len(texts):
        sys.exit(f"patch failed: expected {len(texts)} runs, found {len(runs)}")
    for r, t in zip(runs, texts):
        r.text = t


def patch_text(slide, key, needle, new):
    shape = find(slide, key)
    set_text(para_with(shape, needle), new)
    LOG.append(f"  text   {title_of(slide)[:40]!r}: {needle[:40]!r} -> {new[:60]!r}")


def patch_cell(slide, row, col, needle, new):
    para = find(slide, "table").table.cell(row, col).text_frame.paragraphs[0]
    old = "".join(r.text for r in para.runs)
    if needle not in old:
        sys.exit(f"patch failed: cell ({row},{col}) is {old!r}, expected {needle!r}")
    set_text(para, new)
    LOG.append(f"  cell   ({row},{col}): {old[:40]!r} -> {new[:60]!r}")


def drop_shape(slide, key, needle=None):
    shape = find(slide, key)
    if needle is not None and needle not in shape.text_frame.text:
        sys.exit(f"patch failed: shape {key!r} does not contain {needle!r}")
    LOG.append(f"  remove {title_of(slide)[:40]!r}: shape {shape.name!r} ({shape.text_frame.text.strip()[:40]!r})")
    shape._element.getparent().remove(shape._element)


def notes_text(slide) -> str:
    return slide.notes_slide.notes_text_frame.text


def notes_body(slide) -> str:
    parts = notes_text(slide).split("\n", 2)
    return parts[2].strip() if len(parts) > 2 else ""


def replace_in_notes(slide, old, new, count=1):
    text_now = notes_text(slide)
    if old not in text_now:
        sys.exit(f"patch failed: {old!r} not found in the notes of {title_of(slide)!r}")
    slide.notes_slide.notes_text_frame.text = text_now.replace(old, new, count)


def set_eyebrow(slide, new):
    set_text(find(slide, "eyebrow").text_frame.paragraphs[0], new)


# ---------------------------------------------------------------------------------------------- slides built here
def agenda(d: Deck) -> None:
    rows = [
        ("1", "Fabric vs Azure ML", "The two ML platforms and the MLflow concepts behind both.", ["Demo 1  MLflow tour"]),
        ("2", "MLOps concepts", "Versioning, reproducibility, monitoring and automatic retraining.", []),
        ("3", "MLOps in Fabric and Azure ML", "Architectures, MLOps pillars, then two end-to-end demos.",
         ["Demo 2a  Fabric", "Demo 2b  Azure ML"]),
        ("4", "Foundry and the data agent", "Reconcile logs from several sources, then ask questions on top.",
         ["Demo 3  Data agent"]),
    ]

    def draw(f):
        s = f.s
        gap = 0.17
        h = (f.h - gap * (len(rows) - 1)) / len(rows)
        for k, (no, head, sub, demos) in enumerate(rows):
            y = f.y + k * (h + gap)
            box(s, f.x, y, f.w, h, tone="node", radius=0.12, name=f"agenda row {no}")
            num_badge(s, f.x + 0.3, y + (h - 0.5) / 2, no, size=0.5, fsize=20, name=f"agenda number {no}")
            text(s, f.x + 1.1, y + 0.1, 7.6, 0.4, [head], size=21, bold=True, font=HEAD, anchor="m",
                 name=f"agenda part {no}")
            text(s, f.x + 1.1, y + 0.5, 7.6, 0.34, [sub], size=15.5, color="muted", anchor="m",
                 name=f"agenda subtitle {no}")
            ph, pgap = 0.26, 0.08
            py = y + (h - (len(demos) * ph + (len(demos) - 1) * pgap)) / 2
            for i, label in enumerate(demos):
                pill(s, f.r - 0.3, py + i * (ph + pgap), label, tone="amber", size=10.5, h=ph, right=True,
                     name=f"demo pill {no}.{i + 1}")

    d.custom(
        "O2", "Today in four parts, with three demos you can rebuild", draw, kind="agenda",
        takeaway="Parts 1 and 2 give you the vocabulary. Parts 3 and 4 put it to work.", minutes=3,
        notes="""Here is the rhythm of the day. We alternate between short concept blocks and live demos.

Part 1 is about the platforms: what Fabric is, what Azure Machine Learning is, and why MLflow is the common language between them. You will see the first demo there, a short MLflow tour with one script running in three places.

Part 2 is about MLOps as a set of ideas, independent of any product: versioning, reproducibility, monitoring, and when to retrain automatically.

Part 3 maps those ideas to both platforms. We look at two architectures, then at the MLOps pillars, and then we take one use case from raw logs to a scored, monitored model, first on Fabric and then on Azure ML.

Part 4 puts an agent on the reconciled data, so people can ask questions in plain language.

If we run late, I will cut optional slides, never the demos. The speaker notes say which slides are core.

TRANSITION: Before the content, let me play back what we heard from you.""",
    )


def heard(d: Deck) -> None:
    d.cards(
        "O2b", "What we heard from you",
        [
            dict(title="Reconciling sources is the number one pain point",
                 body="Demo 2 reconciles three sources in silver and gold. Demo 3 queries the result with an agent."),
            dict(title="Move from hand-built ETL to automatic pipelines",
                 body="Part 3 shows scheduled pipelines and release automation, in Fabric and in Azure ML."),
            dict(title="Choose the right ML platform: Fabric or Azure ML",
                 body="Parts 1 and 3 show where each platform starts and which architecture fits which team."),
            dict(title="Put agents on top of the data",
                 body="Part 4 builds a data agent and a Foundry agent, with evaluation and guardrails."),
        ],
        cols=2, numbered=True, tone="node",
        takeaway="These four points shaped the agenda: each one has a part and a demo.", minutes=2,
        notes="""Before the content, I want to play back what we heard from you. Four points came up again and again.

First, reconciling data from several sources is the number one pain point. Demo 2 reconciles three sources in a silver and a gold layer, and Demo 3 queries the result with an agent.

Second, you want to move from hand-built ETL to automatic pipelines. Part 3 shows scheduled pipelines and release automation, in Fabric and in Azure ML.

Third, you need to choose the right ML platform. Parts 1 and 3 show where each one starts and which architecture fits which team.

Fourth, you want to put agents on top of the data. Part 4 builds a data agent and a Foundry agent, with evaluation and guardrails.

ASK: Did we miss something? Is there a fifth point you want to add before we start?
TRANSITION: Let us start with the map of the ML platforms.""",
    )


def divider(d: Deck, sid, no, title, subtitle, goals, notes):
    f = d.section(sid, no, title, subtitle, goals, ("", ""), notes=notes, minutes=1)
    for name in ("section time", "section length"):
        shape = next(s for s in f.s.shapes if s.name == name)
        shape._element.getparent().remove(shape._element)
    return f


def dividers(d: Deck, orig) -> None:
    divider(
        d, "P1.0", 1, "Part 1: Understanding the ML platforms at Microsoft",
        "Two ML platforms, but they start from different operating models.",
        ["See where Fabric starts", "See where Azure ML starts", "Reuse one MLflow mental model in both"],
        notes_body(orig[3]),
    )
    divider(
        d, "P2.0", 2, "Part 2: MLOps from notebook to reliable product",
        "The concepts stay the same whether you run in Fabric, Azure Machine Learning, or both.",
        ["Name the practices that make ML a reliable product", "Version and reproduce everything that changes",
         "Monitor data and models, and decide when to retrain"],
        notes_body(orig[18]),
    )
    divider(
        d, "P3.0", 3, "Part 3: MLOps in Fabric and AML",
        "The same MLOps concepts in Fabric and Azure ML, then one scenario end to end.",
        ["Choose an architecture", "Map each MLOps pillar to a platform feature",
         "Rebuild a complete pipeline on both platforms"],
        """Part 3 turns the concepts into practice. We use the same MLOps ideas as in Part 2, and we show how each one is implemented in Fabric and in Azure Machine Learning.

First, two reference architectures: one where the data stays in Fabric and the rest runs in Azure ML, and one where everything stays in Fabric, with its gaps. Then the MLOps pillars mapped to platform features, and four focus topics: continuous training, model drift, data drift and A/B testing.

Then we build the same scenario twice, end to end: raw logs to a scored, monitored model, once on Fabric and once on Azure ML. There is no winner here. The question is which operating model fits your team.

TRANSITION: Let us start with the two architectures.""",
    )
    divider(
        d, "P4.0", 4, "Part 4: Ask the data, in plain language",
        "We now have reconciled gold tables and frozen risk scores, so we can put a query assistant on top.",
        ["See the Fabric data-agent building blocks", "Connect it to Foundry with guardrails",
         "Evaluate answers and refusals before a live demo"],
        notes_body(orig[51]),
    )


def aml_cards(d: Deck) -> None:
    d.cards(
        "P1.3", "Azure Machine Learning is an ML platform that connects to your data",
        [
            dict(title="Data assets", tone="node",
                 body="Data usually stays in ADLS, Blob, or OneLake `/Files`, then AML reads it."),
            dict(title="Compute + jobs", tone="azure",
                 body="You choose clusters, environments, schedules, and command or pipeline jobs."),
            dict(title="Experiments + models", tone="azure",
                 body="MLflow tracking is built in: runs, metrics and artifacts live in the workspace, and models "
                      "go to the registry."),
            dict(title="Pipelines", tone="azure",
                 body="Reusable components prepare, train, evaluate and register. They run on a schedule or on an "
                      "event."),
            dict(title="Registry + endpoints", tone="azure",
                 body="Models, environments and components are versioned assets. Managed online and batch endpoints "
                      "serve them."),
            dict(title="Data and model drift", tone="azure",
                 body="Model monitoring tracks data drift, prediction drift and data quality, with alerts."),
        ],
        cols=3, core=False, minutes=3, source="Microsoft Learn: Azure ML MLflow and monitoring docs, verified 2026-10-18",
        notes="""Azure Machine Learning starts from a different question: how do I run and operate models with explicit control?

The workspace is an ML control plane. Compute, jobs, environments, model registration, endpoints, schedules, and monitoring are front and center. That suits teams who separate data engineering from ML engineering, or who need stronger operational boundaries around training and serving.

The data usually lives elsewhere. AML connects to it through datastores, data assets, direct paths, or shared storage patterns. Pipelines chain reusable components for preparation, training, evaluation and registration, and they run on a schedule or on an event. Model monitoring tracks data drift, prediction drift and data quality, with alerts.

The important practical point for today is that AML still speaks MLflow. The same training and model-logging concepts remain recognizable even when the surrounding platform is different.

IF SHORT ON TIME: Skip this slide and use the lifecycle table on the next slides as the main comparison.
SOURCE: """ + " ; ".join(AML_MLFLOW_URLS),
    )


def open_talk(d: Deck, sid, part, question, more, notes):
    def draw(f):
        s = f.s
        top, bar_h = f.y + 0.4, 1.6
        box(s, f.x, top, f.w, bar_h, tone="amber", radius=0.14, name="question bar")
        tag, width = pill(s, f.x, top - 0.14, "Question for the room", tone="amber_solid", size=11, h=0.28,
                          name="question tag")
        tag.left = Inches(f.x + (f.w - width) / 2)
        text(s, f.x + 0.5, top + 0.25, f.w - 1.0, bar_h - 0.4, [question], size=28, bold=True, font=HEAD, align="c",
             anchor="m", name="question")
        label_y = top + bar_h + 0.4
        text(s, f.x, label_y, 6.0, 0.26, ["MORE QUESTIONS TO DISCUSS"], size=11, color="azure", font=MONO, bold=True,
             track=1.2, wrap=False, lint=False, name="more questions label")
        gap = 0.25
        cw = (f.w - 2 * gap) / 3
        for k, q in enumerate(more):
            card(s, f.x + k * (cw + gap), label_y + 0.4, cw, 1.9, title=q, tone="node", title_size=18, badge=k + 1,
                 name=f"question {k + 1}")

    d.custom(sid, f"Part {part}: open talk", draw, kind="discuss", notes=notes, minutes=5, eyebrow=EYEBROW[part])


def open_talks(d: Deck) -> None:
    open_talk(
        d, "P1.19", 1, "Which of these architectures is closest to the one you would choose?",
        ["Where is the friction today: data preparation, deployment or monitoring?",
         "Who builds and who operates the models: one team or two?",
         "What would you need to see before using MLflow tracking everywhere?"],
        """This is the first open conversation of the day, and it lands Part 1.

Both platforms speak real MLflow, so the mental model transfers. What differs is the wrapper around it: where the tracking URI comes from, how the registry behaves, and how serving works. A hybrid setup, with Fabric for the data and Azure ML for the model lifecycle, is realistic for many teams.

Let the room pick the architecture that feels closest to their own, then use the extra questions to find the real friction. Do not push for a winner.

ASK: Which of these architectures is closest to the one you would choose, and why?
TRANSITION: Part 2 is about MLOps concepts that sit above both platforms.""",
    )
    open_talk(
        d, "P2.19", 2, "Which of these concepts and pillars should be part of your blueprint?",
        ["Which model do you retrain by hand today, and what triggers it?",
         "Which drift signal could you compute tomorrow with data you already have?",
         "Who owns the promotion decision: the data scientist, the platform team, or a gate?"],
        """This is the open conversation that lands Part 2.

We covered versioning, reproducibility, drift monitoring and the CI, CT and CD flow. None of it depended on a product. That is deliberate: the blueprint you draw now has to survive a change of platform.

Ask the room to pick the two or three concepts they would put in a first blueprint, and to be honest about what they do by hand today. Part 3 maps each pillar to Fabric and to Azure ML.

ASK: Which of these concepts and pillars should be part of your blueprint?
TRANSITION: Now let us see how the two platforms implement these ideas.""",
    )
    open_talk(
        d, "P3.19", 3, "Which of the two platforms seems more appropriate for your V2?",
        ["Where would retraining run: in the data workspace or in a dedicated ML workspace?",
         "Which part would you rebuild first on your own data?",
         "What would change in your release process to promote the model, not only the code?"],
        """This is the open conversation that lands Part 3.

We built the same scenario twice. Both paths work, and there is no winner. The useful question is which operating model fits your team: the data workspace as the center of gravity, or a dedicated ML workspace with its own release controls.

Let people answer for their own V2, and note which concern comes up first: data, release process, or monitoring. That answer tells you where to start in the lab.

ASK: Which of the two platforms seems more appropriate for your V2?
TRANSITION: The last part puts an agent on top of the reconciled data.""",
    )


# ---------------------------------------------------------------------------------------------- edits to kept slides
def patch_kept(orig) -> None:
    s5, s6, s8, s12, s15, s17, s29 = (orig[i - 1] for i in (5, 6, 8, 12, 15, 17, 29))

    patch_text(s5, 20, "Microsoft Fabric \u2014 Data Science", "Microsoft Fabric Data Science")
    patch_text(s5, 24, "published to Teams",
               "Models, agents and tools with evaluations and tracing, published to Teams and Microsoft 365 Copilot")
    replace_in_notes(
        s5, "Fabric starts from shared data work.",
        "The three cards show three starting points. Fabric Data Science sits on Fabric capacity, Azure Machine "
        "Learning is a service in your own subscription, and Microsoft Foundry is the pro-code layer for models and "
        "agents. They share four foundations: OneLake, Microsoft Entra ID, MLflow and Microsoft Purview.\n\n"
        "Fabric starts from shared data work.")

    patch_text(s6, 10, "Batch / Online prediction", "Batch and online scoring")
    set_runs(para_with(find(s6, 10), "Registered models can score with"),
             ["Native integration with Power BI. ", "PREDICT",
              " scores registered models in batch when the signature is valid; real-time endpoints are in preview."])
    drop_shape(s6, 12, "A VERIFIER")

    cells = [
        (1, 2, "outside AML", "Read data assets or storage paths; prep can stay outside AML."),
        (2, 1, "accelerators", "Notebook next to the lake, with Copilot and Power BI as accelerators."),
        (2, 2, "Notebook", "Notebook or compute instance with an explicit environment."),
        (3, 2, "Pipeline job", "Command or pipeline job; MLflow tracking is preconfigured."),
        (4, 2, "lineage", "Same run comparison, plus a workspace tracking server with job lineage."),
        (6, 2, "Managed online", "Managed online and batch endpoints are the production path; Kubernetes (AKS or "
                                 "Azure Arc) is supported."),
        (7, 2, "model monitoring", "Managed endpoint logs and model monitoring are built in."),
    ]
    for row, col, needle, new in cells:
        patch_cell(s8, row, col, needle, new)
    patch_text(s8, "takeaway text", "Fabric keeps more of the lifecycle",
               "Fabric keeps more of the lifecycle in the data workspace; Azure ML has more MLOps built in.")
    for shape_id in (7, 8, 9):
        find(s8, shape_id).top += Inches(0.42)
    LOG.append("  move   takeaway bar of the platform table down 0.42 in (longer cells make the table taller)")

    patch_text(s12, "title", "five questions",
               "How to choose: four questions usually point to Fabric, Azure ML, or both")
    patch_text(s12, "return label", "", "YOU CAN USE BOTH, OR PICK ONE")
    replace_in_notes(s12, "five questions", "four questions", count=5)

    patch_text(s15, "panel items: Fabric", "Cross-workspace logging can be used", "Cross-workspace logging is supported.")
    patch_text(s15, "panel items: Azure ML", "Experiment items show params",
               "The Azure ML studio shows params, metrics, artifacts and run comparison.")

    drop_shape(s17, 34, "A deployer")
    replace_in_notes(
        s17, "\nDEMO: ",
        "\nPREP: Before the day, deploy the Azure ML workspace and the Fabric capacity (infra folder, see "
        "VERIFY-BEFORE-FRIDAY.md), then run the script once on each platform so the leaderboard and the registered "
        "model already exist.\nDEMO: ")

    drop_shape(s29, 16, "A int")

    for n in (46, 48):
        set_eyebrow(orig[n - 1], "LIVE DEMO  \u00b7  " + EYEBROW[3])
    for n in (47, 49, 53):
        set_eyebrow(orig[n - 1], EYEBROW[3])


# ---------------------------------------------------------------------------------------------- assembly
def assemble(prs, ordered) -> None:
    lst = prs.slides._sldIdLst
    els = {s.slide_id: el for s, el in zip(prs.slides, list(lst))}
    order_ids = [s.slide_id for s in ordered]
    first = prs.slide_masters[0]
    bad = [title_of(s) for s in ordered if s.slide_layout.slide_master is not first]
    if bad:
        sys.exit(f"slides still use an imported master: {bad}")
    keep = set(order_ids)
    for slide_id, el in els.items():
        lst.remove(el)
        if slide_id not in keep:
            prs.part.drop_rel(el.rId)
    for slide_id in order_ids:
        lst.append(els[slide_id])
    masters = prs._element.find(qn("p:sldMasterIdLst"))
    for el in list(masters)[1:]:
        masters.remove(el)
        prs.part.drop_rel(el.get(qn("r:id")))


def write_index(prs, path: Path) -> dict[str, float]:
    lines = ["# Slide index, W1 edition", "", "| # | id | min | core | headline |", "|---|---|---|---|---|"]
    minutes: dict[str, float] = {}
    for n, s in enumerate(prs.slides, 1):
        head = notes_text(s).split("\n", 1)[0]
        m = re.match(r"\[(.+?)\s+\u00b7\s+~(\S+) min\s+\u00b7\s+(CORE|OPTIONAL)\]", head)
        sid, mins, core = (m.group(1), float(m.group(2)), m.group(3)) if m else ("?", 0.0, "?")
        part = re.match(r"(P\d|O|C|A)", sid)
        key = part.group(1) if part else "?"
        minutes[key] = minutes.get(key, 0.0) + mins
        hidden = "  (hidden)" if s._element.get("show") == "0" else ""
        lines.append(f"| {n} | {sid} | {mins:g} | {core.lower()} | {title_of(s).replace('|', '/')}{hidden} |")
    lines += ["", "## Minutes per part", "",
              "Talk minutes come from the speaker notes. The windows are those of the day plan: what is left in a "
              "window is for the demos, the labs and the questions.", "",
              "| part | window | talk min | left in the window |", "|---|---|---:|---:|"]
    for key, label, start, budget in PARTS:
        talk = minutes.get(key, 0.0)
        lines.append(f"| {label} | {start} to {hm(start_minutes(start) + budget)} | {talk:g} | {budget - talk:g} |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    return minutes


ICON_COLORS = {"amber": (166, 75, 0), "azure": (15, 108, 189), "ink": (22, 32, 47), "muted": (83, 97, 122),
               "success": (31, 122, 85), "white": (255, 255, 255)}


def _pictures(shapes):
    for sh in shapes:
        if sh.shape_type == MSO_SHAPE_TYPE.GROUP:
            yield from _pictures(sh.shapes)
        elif sh.shape_type == MSO_SHAPE_TYPE.PICTURE:
            yield sh


def refresh_icons(prs) -> int:
    """The kept slides embed the hairline icon PNGs of the first build. Swap each generic icon (picture named
    'icon: <name>') for the current PNG of the same name and color. Product icons have no counterpart and stay."""
    root = HERE / "assets" / "icons" / "png"
    done: set[int] = set()
    swapped = 0
    for slide in prs.slides:
        for pic in _pictures(slide.shapes):
            m = re.fullmatch(r"icon: (\S+)", pic.name or "")
            if not m:
                continue
            part = slide.part.related_part(pic._element.blip_rId)
            if id(part) in done:
                continue
            done.add(id(part))
            old = Image.open(io.BytesIO(part.blob)).convert("RGBA")
            mask = old.getchannel("A").point(lambda a: 255 if a > 60 else 0)
            pixels = [p[:3] for p, keep in zip(old.getdata(), mask.getdata()) if keep]
            if not pixels:
                continue
            mean = [sum(c) / len(pixels) for c in zip(*pixels)]
            color = min(ICON_COLORS, key=lambda k: sum((a - b) ** 2 for a, b in zip(ICON_COLORS[k], mean)))
            new = root / color / f"{m.group(1)}.png"
            if new.is_file() and Image.open(new).size == old.size:
                part._blob = new.read_bytes()
                swapped += 1
    LOG.append(f"  icons: {swapped} embedded icon images refreshed")
    return swapped


APP_XML = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
    '<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties" '
    'xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">'
    "<TotalTime>0</TotalTime><Application>Microsoft Office PowerPoint</Application>"
    "<PresentationFormat>Widescreen</PresentationFormat><Slides>{slides}</Slides><Notes>{notes}</Notes>"
    "<HiddenSlides>{hidden}</HiddenSlides><MMClips>0</MMClips><ScaleCrop>false</ScaleCrop>"
    "<LinksUpToDate>false</LinksUpToDate><SharedDoc>false</SharedDoc><HyperlinksChanged>false</HyperlinksChanged>"
    "<AppVersion>16.0000</AppVersion></Properties>"
)


def scrub_package(prs) -> None:
    """The edited deck carries the editor's name, PowerPoint's change tracking and the titles of the slides that were
    dropped. Neutralize the document properties, drop the tracking parts, rewrite app.xml for the final slides."""
    now = datetime.now(timezone.utc).replace(microsecond=0, tzinfo=None)
    cp = prs.core_properties
    cp.author = cp.last_modified_by = "Workshop team"
    cp.title = title_of(prs.slides[0])
    cp.comments = "ML platforms on Microsoft workshop deck, W1 edition"
    cp.created = cp.modified = now
    cp.revision = 1
    rels = prs.part.rels
    for rid, rel in list(rels.items()):
        if rel.reltype.endswith(("/changesInfo", "/revisionInfo")):
            rels.pop(rid)
    slides = list(prs.slides)
    app = APP_XML.format(
        slides=len(slides),
        notes=sum(1 for s in slides if s.has_notes_slide),
        hidden=sum(1 for s in slides if s._element.get("show") == "0"),
    )
    for part in prs.part.package.iter_parts():
        if str(part.partname) == "/docProps/app.xml":
            part._blob = app.encode("utf-8")
    LOG.append("  package: author, change tracking and stale slide titles removed")


def repair_notes_master(prs) -> None:
    """The edited deck carries an empty notes master, so python-pptx cannot create notes for new slides. Restore the
    standard placeholders (slide image, notes body, slide number) from the python-pptx template."""
    master = prs.notes_master._element
    if master.xpath(".//p:ph"):
        return
    tpl = etree.parse(str(Path(pptx.__file__).parent / "templates" / "notesMaster.xml")).getroot()
    csld = master.find(qn("p:cSld"))
    csld.replace(csld.find(qn("p:spTree")), deepcopy(tpl.find(qn("p:cSld")).find(qn("p:spTree"))))
    LOG.append("  notes master: restored the standard placeholders")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--src", required=True, type=Path, help="the presenter's edited deck (66 slides)")
    ap.add_argument("--out", type=Path, default=HERE / "ml-platforms-workshop-W1.pptx")
    args = ap.parse_args()

    prs = Presentation(str(args.src))
    orig = list(prs.slides)
    if len(orig) != N_SRC_SLIDES:
        sys.exit(f"expected {N_SRC_SLIDES} slides in {args.src}, found {len(orig)}")
    repair_notes_master(prs)

    d = Deck()
    d.prs, d.index = prs, []
    d.layout = layout_by_name(prs, "Title Only")

    agenda(d)
    heard(d)
    dividers(d, orig)
    aml_cards(d)
    open_talks(d)
    for name in MODULES:
        try:
            mod = importlib.import_module(name)
        except ModuleNotFoundError as exc:
            if exc.name != name:
                raise
            print(f"warning: module {name} not found, its slides are skipped")
            continue
        mod.build(d)

    patch_kept(orig)
    print("\n".join(LOG))

    added = list(prs.slides)[N_SRC_SLIDES:]
    new = {rec["id"]: s for rec, s in zip(d.index, added)}
    wanted = {key for kind, key in ORDER if kind == "N"}
    extra = sorted(set(new) - wanted)
    if extra:
        sys.exit(f"built slides that are not in ORDER: {extra}")
    ordered = []
    for kind, key in ORDER:
        if kind == "U":
            ordered.append(orig[key - 1])
        elif key in new:
            ordered.append(new[key])
        else:
            print(f"warning: slide {key} was not built, skipped")
    assemble(prs, ordered)
    refresh_icons(prs)
    print(LOG[-1])
    scrub_package(prs)
    print(LOG[-1])

    prs.save(str(args.out))
    minutes = write_index(Presentation(str(args.out)), args.out.with_name("slide-index-W1.md"))
    print(f"\n{len(ordered)} slides -> {args.out}")
    print("minutes per part: " + ", ".join(f"{k} {v:g}" for k, v in sorted(minutes.items())))
    for line in LINT:
        print("LINT", line)
    return 1 if LINT else 0


if __name__ == "__main__":
    sys.exit(main())
