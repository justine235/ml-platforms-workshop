"""Part 2 concept slides P2.21 to P2.26: barriers, lifecycle, practices, versioning, reproducibility, evaluation gate."""
from __future__ import annotations

from pptx.enum.shapes import MSO_SHAPE

from deck_core import HEAD, MONO, add_icon, arrow, box, card, fill_text, label, link, polyline, text
from deck_lib import Deck
from facts import F, d2

FAB, FAB_T = "0F7B6C", "E6F4F1"
AML, AML_T = "005A9E", "E8F1FA"


# ------------------------------------------------------------------ shared helpers
def _chip(s, x, y, w, h, icon, txt, color, line):
    """White rounded chip with a small icon and one short label."""
    box(s, x, y, w, h, tone="paper", radius=0.1, line_color=line, name=f"chip: {txt}")
    add_icon(s, icon, x + 0.13, y + (h - 0.3) / 2, 0.3, color=color)
    text(s, x + 0.52, y, w - 0.58, h, [txt], size=14, anchor="m", name=f"chip text: {txt}")


def _node(s, x, y, w, h, txt, tone="azure", line=None, size=15):
    b = box(s, x, y, w, h, tone=tone, radius=0.12, line_color=line, name=f"node: {txt}")
    fill_text(b.text_frame, [txt], size=size, bold=True, font=HEAD, align="c", anchor="m",
              margins=(0.08, 0.02, 0.08, 0.02))
    return b


# ------------------------------------------------------------------ P2.21 barriers
def _draw_barriers(f):
    s = f.s
    gap = 0.4
    pw = (f.w - gap) / 2
    groups = [
        (f.x, "BUILD SIDE", "Slow and manual to build", "workflow", "azure", "azure_line", "azure",
         [("clock", "Cycle time too high"), ("wrench", "Manual steps"), ("puzzle", "Lack of reusability"),
          ("repeat", "Lack of reproducibility"), ("copy", "Duplicated efforts"), ("users", "Limited collaboration")],
         "Months from idea to production, and every model is rebuilt by hand."),
        (f.x + pw + gap, "RUN SIDE", "Fragile once live", "alert-triangle", "amber", "amber_line", "amber",
         [("trending-down", "Model decay"), ("git-compare", "Training/serving skew"), ("scale", "Model bias"),
          ("eye", "Model transparency"), ("server", "Scalability")],
         "Quiet failures: predictions get worse and nobody notices until the business does."),
    ]
    for gx, tag, head, hicon, tone, line, color, chips, cost in groups:
        box(s, gx, f.y, pw, f.h, tone=tone, radius=0.16, name=f"panel: {head}")
        text(s, gx + 0.25, f.y + 0.16, pw - 0.5, 0.24, [tag], size=12, color=color, font=MONO, bold=True, track=1.2,
             anchor="m", wrap=False, lint=False, name=f"tag: {tag}")
        add_icon(s, hicon, gx + 0.25, f.y + 0.52, 0.42, color=color)
        text(s, gx + 0.85, f.y + 0.5, pw - 1.1, 0.46, [head], size=21, bold=True, font=HEAD, anchor="m",
             name=f"head: {head}")
        cw = (pw - 0.5 - 0.14) / 2
        ch, vg = 0.54, 0.1
        y1 = f.y + 1.2
        for i, (icon, txt) in enumerate(chips):
            r, c = divmod(i, 2)
            alone = i == len(chips) - 1 and len(chips) % 2 == 1
            _chip(s, gx + 0.25 + (0 if alone else c * (cw + 0.14)), y1 + r * (ch + vg), pw - 0.5 if alone else cw, ch,
                  icon, txt, color, line)
        ydiv = y1 + 3 * ch + 2 * vg + 0.14
        arrow(s, gx + 0.25, ydiv, gx + pw - 0.25, ydiv, color=line, w=1.0, tail=False, name="divider")
        text(s, gx + 0.25, ydiv + 0.1, pw - 0.5, f.b - ydiv - 0.2,
             [dict(text="WHAT IT COSTS", size=12, bold=True, font=MONO, color=color, after=3),
              dict(text=cost, size=15)], name=f"cost: {head}")
    mid = f.y + f.h / 2
    arrow(s, f.x + pw + 0.07, mid, f.x + pw + gap - 0.07, mid, color="muted", w=2.25, name="build to run")


NOTES_21 = (
    "Start with why MLOps exists: most machine learning projects stall before they reach production, and rarely "
    "because the model is bad. Two families of barriers explain it. On the build side the process is slow and "
    "manual: long cycle times, steps done by hand, nothing reusable, nobody able to reproduce last month's result, "
    "the same work done twice, and little collaboration beyond personal notebooks. On the run side the model is "
    "fragile once it is live: it decays as the world changes, the data at serving time differs from the data at "
    "training time, bias and opacity worry the business, and the setup does not scale. Every slide that follows in "
    "Part 2 answers one of these eleven boxes.\n\n"
    "ASK: Which of these have you already hit? Take two or three answers and come back to them at the recap.\n"
    "WATCH OUT: do not quote a precise percentage. Surveys on AI pilots report anything from about half to nine out "
    "of ten depending on how production is defined, and the often-repeated 87 percent figure has a disputed "
    "origin.\n"
    "VERIFY: I found no single authoritative statistic for classical ML projects specifically; the recent figures I "
    "found concern enterprise AI pilots and come from secondary reporting. That is why the slide carries no number. "
    "If you want one, open the original source and read how it defines production first.\n"
    "TRANSITION: To see where these barriers sit, look at the classical ML lifecycle."
)


# ------------------------------------------------------------------ P2.22 lifecycle
def _draw_lifecycle(f):
    s, x0, y0 = f.s, f.x, f.y
    nw, nh, step = 2.2, 0.66, 2.85
    xa, xb, xc = x0, x0 + step, x0 + 2 * step
    yb = y0 + 3.4
    a = _node(s, xa, y0, nw, nh, "Frame business needs")
    b = _node(s, xb, y0, nw, nh, "Gather insights")
    c = _node(s, xc, y0, nw, nh, "Productionalize model")
    d_ = _node(s, xc, yb, nw, nh, "Make predictions")
    e = _node(s, xb, yb, nw, nh, "Monitor model")
    link(s, a, b, "r", "l", w=1.75, name="frame to gather")
    link(s, b, c, "r", "l", w=1.75, name="gather to productionalize")
    link(s, c, d_, "b", "t", w=1.75, name="productionalize to predict")
    link(s, d_, e, "l", "r", w=1.75, name="predict to monitor")
    polyline(s, [(xb, yb + nh / 2), (xa + nw / 2, yb + nh / 2), (xa + nw / 2, y0 + nh)], w=1.75, name="monitor to frame")

    px, py, pw, ph = x0 + 1.42, y0 + 0.95, 5.1, 2.1
    box(s, px, py, pw, ph, tone="amber", radius=0.14, line_w=1.5, name="experiment loop")
    text(s, px + 0.2, py + 0.08, pw - 0.4, 0.34, ["Experiment: the inner loop"], size=15, bold=True, font=HEAD,
         color="amber", anchor="m", name="experiment title")
    iw, ih = 1.85, 0.52
    ix1, ix2 = px + 0.375, px + pw - 0.375 - iw
    iy1, iy2 = py + 0.52, py + ph - 0.16 - ih
    inner = {}
    for key, (ix, iy, txt) in dict(get=(ix1, iy1, "Get data"), prep=(ix2, iy1, "Prepare data"),
                                   train=(ix2, iy2, "Train models"), ev=(ix1, iy2, "Evaluate models")).items():
        inner[key] = _node(s, ix, iy, iw, ih, txt, tone="paper", line="amber_line", size=14)
    for k1, k2, s1, s2 in (("get", "prep", "r", "l"), ("prep", "train", "b", "t"), ("train", "ev", "l", "r"),
                           ("ev", "get", "t", "b")):
        link(s, inner[k1], inner[k2], s1, s2, color="amber", w=1.75, name=f"inner {k1} to {k2}")
    arrow(s, xb + nw / 2, y0 + nh, xb + nw / 2, py, color="amber", w=1.25, dash=True, tail=False, name="zoom")
    arrow(s, xb + nw / 2, yb, xb + nw / 2, py + ph, color="amber", w=2.25, name="retrain")
    label(s, xb + nw / 2 + 0.12, (yb + py + ph) / 2 - 0.12, 1.2, "retrain", size=12, color="amber", align="l",
          bold=True, name="retrain label")

    bullets = ["Experiment steps are run by hand", "Retraining runs on a fixed basis, not on need",
               "Go or no-go is a human reading of results", "Repetitive work, repeated every cycle",
               "Deployment is handed to a dedicated IT team", "Little tracking or versioning over time"]
    rx = x0 + 8.2
    card(s, rx, y0, f.r - rx, 4.06, "Why the retrain loop hurts", [dict(text=t, bullet=True) for t in bullets],
         tone="amber", title_size=17, body_size=14, after=8, pad=0.2, name="why it hurts")


NOTES_22 = (
    "This is the classical lifecycle, and it is a loop, not a line. Frame the business need, gather insights, "
    "productionalize the model, make predictions, monitor, and go around again. Inside the insight phase sits the "
    "experiment loop every data scientist knows: get data, prepare it, train models, evaluate them. In most teams "
    "that inner loop is a notebook and a person.\n\n"
    "Take the Fleet example. The model predicts a corrective work order in the next 7 days, so the truth is only "
    "known a week later. New telematics and work orders keep arriving, so the model slowly goes stale. When "
    "retraining is manual, someone reruns the notebook when they remember, reads a table of metrics, decides alone "
    "that the new model is better, and hands a file to IT to deploy. Nothing is versioned, so nobody can say which "
    "data trained which model.\n\n"
    "ASK: How often does your team retrain today, and who decides to ship?\n"
    "WATCH OUT: the point is not that experimenting is bad. The point is that this loop repeats for the life of the "
    "product, and every manual step is a place to lose time or make a mistake.\n"
    "IF SHORT ON TIME: read the amber loop and the right panel only.\n"
    "VERIFY: the weekly arrival of new data is a storytelling assumption; the scenario contract only fixes the "
    "7-day label horizon.\n"
    "TRANSITION: So which practices automate this loop? Four of them."
)


# ------------------------------------------------------------------ P2.23 practices
def _draw_practices(f):
    s = f.s
    lw, gap_mid = 5.1, 1.0
    gh = 0.14
    ch = (f.h - 3 * gh) / 4
    practices = [
        ("CI", "Continuous integration", "Test and validate code, data and models on every change"),
        ("CT", "Continuous training", "Retrain automatically when data or performance says so"),
        ("CD", "Continuous deployment", "Ship the model and its pipeline safely to each environment"),
        ("CM", "Continuous monitoring", "Watch data, model and service once they are live"),
    ]
    for i, (tag, name, definition) in enumerate(practices):
        y = f.y + i * (ch + gh)
        box(s, f.x, y, lw, ch, tone="azure", radius=0.12, name=f"practice: {name}")
        t = box(s, f.x + 0.16, y + (ch - 0.6) / 2, 0.82, 0.6, tone="solid", radius=0.1, name=f"tag {tag}")
        fill_text(t.text_frame, [tag], size=20, color="white", font=MONO, bold=True, align="c", anchor="m",
                  margins=(0, 0, 0, 0), wrap=False)
        text(s, f.x + 1.15, y, lw - 1.3, ch,
             [dict(text=name, size=16, bold=True, font=HEAD, color="azure", after=2), dict(text=definition, size=14)],
             anchor="m", name=f"practice text: {name}")

    ax = f.x + lw + 0.1
    ay = f.y + f.h / 2
    box(s, ax, ay - 0.3, gap_mid - 0.2, 0.6, tone="solid", shape=MSO_SHAPE.RIGHT_ARROW, name="leads to arrow")
    label(s, ax - 0.1, ay - 0.62, gap_mid, "leads to", size=12, color="azure", bold=True, name="leads to label")

    px = f.x + lw + gap_mid
    pw = f.r - px
    box(s, px, f.y, pw, f.h, tone="paper", radius=0.16, line_color="azure_line", line_w=1.25, name="capabilities panel")
    text(s, px + 0.28, f.y + 0.14, pw - 0.56, 0.4, ["Six capabilities: the next slides"], size=19, bold=True, font=HEAD,
         anchor="m", name="capabilities title")
    colw = (pw - 0.28 * 2 - 0.3) / 2
    cols = [
        ("BUILD SIDE", "azure", [("git-branch", "Versioning", "Code, data, models, runs"),
                                 ("clipboard-check", "Data validation", "Stop bad data early"),
                                 ("repeat", "Reproducibility", "Same inputs, same model")]),
        ("RUN SIDE", "amber", [("scale", "Responsible AI", "Fair, explainable, safe"),
                               ("radar", "Data drift", "Inputs move away from training"),
                               ("trending-down", "Model drift", "Predictions degrade over time")]),
    ]
    top = f.y + 0.72
    pitch = (f.h - 0.72 - 0.62) / 3
    for ci, (tag, color, rows) in enumerate(cols):
        cx = px + 0.28 + ci * (colw + 0.3)
        text(s, cx, top, colw, 0.26, [tag], size=12, color=color, font=MONO, bold=True, track=1.2, anchor="m",
             wrap=False, lint=False, name=f"column tag {tag}")
        arrow(s, cx, top + 0.3, cx + colw, top + 0.3, color="azure_line" if color == "azure" else "amber_line", w=1.0,
              tail=False, name="column rule")
        for ri, (icon, name, gloss) in enumerate(rows):
            ry = top + 0.42 + ri * pitch
            add_icon(s, icon, cx, ry + 0.02, 0.4, color=color)
            text(s, cx + 0.56, ry, colw - 0.56, pitch - 0.1,
                 [dict(text=name, size=16, bold=True, font=HEAD, after=1), dict(text=gloss, size=14)],
                 name=f"capability: {name}")


NOTES_23 = (
    "The four practices are the what. Continuous integration tests and validates code, data and models on every "
    "change. Continuous training retrains automatically when data or performance says so. Continuous deployment "
    "ships the model and its pipeline safely to each environment. Continuous monitoring watches data, model and "
    "service once they are live. Together they close the loop from the previous slide.\n\n"
    "Behind them sit six capabilities: three on the build side (versioning, data validation, reproducibility) and "
    "three on the run side (responsible AI, data drift, model drift). The next slides take them one at a time, each "
    "with the way Microsoft Fabric and Azure Machine Learning do it.\n\n"
    "ASK: Which of the four do you practice today, even partly? Most teams answer continuous integration, for code "
    "only.\n"
    "WATCH OUT: integration and deployment for ML are not the software versions. A change can be new code, new data "
    "or a new model, so the pipeline has to test data and models too, not only code. Keep tool names out of this "
    "slide; the mapping comes on the next ones.\n"
    "IF SHORT ON TIME: name the four, say they rest on six capabilities, and move on.\n"
    "TRANSITION: Start with the first capability: version everything that changes."
)


# ------------------------------------------------------------------ P2.24 versioning
def _map_cell(s, x, y, w, h, platform, txt):
    """Platform mapping cell: tinted, platform colour used only here and always with the platform name."""
    col, tint = (FAB, FAB_T) if platform == "Fabric" else (AML, AML_T)
    box(s, x, y, w, h, tone="node", radius=0.08, line_w=0.75, line_color=col, fill_color=tint,
        name=f"{platform}: {txt}")
    text(s, x + 0.1, y + 0.04, w - 0.2, h - 0.08,
         [dict(text=platform, size=12, bold=True, color=col, after=1), dict(text=txt, size=12)], anchor="m",
         name=f"{platform} text: {txt}")


def _map_card(s, x, y, w, h, icon, title, what, why, fab, aml, top_h, title_h=0.42, title_size=18):
    """Concept card: icon + title, what and why lines, then the Fabric and Azure ML mapping cells."""
    box(s, x, y, w, h, tone="node", radius=0.14, name=f"card: {title}")
    add_icon(s, icon, x + 0.18, y + 0.17, 0.36, color="azure")
    text(s, x + 0.66, y + 0.14, w - 0.8, title_h, [title], size=title_size, bold=True, font=HEAD, anchor="m",
         name=f"card title: {title}")
    ty = 0.22 + title_h
    paras = [dict(text=what, size=14, after=4)]
    if why:
        paras.append(dict(text=why, size=14, color="muted"))
    text(s, x + 0.18, y + ty, w - 0.36, top_h - ty - 0.04, paras, name=f"card text: {title}")
    ch = (h - top_h - 0.12 - 0.07) / 2
    _map_cell(s, x + 0.12, y + top_h, w - 0.24, ch, "Fabric", fab)
    _map_cell(s, x + 0.12, y + top_h + ch + 0.07, w - 0.24, ch, "Azure ML", aml)


def _draw_versioning(f):
    s = f.s
    gap = 0.2
    cw = (f.w - 3 * gap) / 4
    strip_h = 0.68
    ch = f.h - strip_h - 0.14
    cols = [
        ("git-branch", "Code", "Notebooks, pipelines, config", "Revert a bad change",
         "Git integration: GitHub or Azure DevOps", "Any Git repo, commit SHA kept with the job"),
        ("database", "Data", "Training and test snapshots", "Rebuild with the same data",
         "Delta table versions (time travel)", "Versioned data assets"),
        ("package", "Model", "Each registered model", "Roll back or compare",
         "ML model item versions", "Registered model versions, workspace or registry"),
        ("flask-conical", "Experiments", "Runs: params, metrics, artifacts", "Compare and audit attempts",
         "MLflow runs in an Experiment item", "MLflow jobs and runs in the workspace"),
    ]
    for i, (icon, title, what, why, fab, aml) in enumerate(cols):
        _map_card(s, f.x + i * (cw + gap), f.y, cw, ch, icon, title, what, why, fab, aml, top_h=1.64)

    sy = f.y + ch + 0.14
    box(s, f.x, sy, f.w, strip_h, tone="azure", radius=0.12, name="lineage strip")
    text(s, f.x + 0.22, sy, 2.6, strip_h, ["WHAT TIES IT TOGETHER"], size=12, color="azure", font=MONO, bold=True,
         track=1.0, anchor="m", wrap=False, lint=False, name="lineage label")
    cy, chh = sy + (strip_h - 0.44) / 2, 0.44
    m = box(s, f.x + 2.95, cy, 1.75, chh, tone="solid", radius=0.1, name="chip: Model version")
    fill_text(m.text_frame, ["Model version"], size=14, color="white", bold=True, align="c", anchor="m",
              margins=(0.05, 0, 0.05, 0), wrap=False)
    label(s, f.x + 4.75, cy, 1.2, "points to →", size=12, color="azure", bold=True, h=chh, name="points to")
    cx = f.x + 6.0
    for icon, txt, w in (("git-branch", "Code commit", 1.8), ("database", "Data version", 1.8),
                         ("flask-conical", "Run and metrics", 2.1)):
        _chip(s, cx, cy, w, chh, icon, txt, "azure", "azure_line")
        cx += w + 0.12


NOTES_24 = (
    "Everything that can change a model's behavior must be versioned, or you cannot reproduce it, compare it or "
    "roll it back. Four things change: the code (notebooks, pipelines, configuration), the data (training and "
    "test snapshots), the model (each registered version) and the experiments (runs with their parameters, metrics "
    "and artifacts). Look at the bottom strip: the point is the links, not four separate histories. A model "
    "version should point to the code commit, the data version and the run that produced it.\n\n"
    "Fleet example: in the Azure ML demo the registered model fleet-failure-7d carries tags for the data version, "
    "the Git commit and the source run. In the Fabric demo the model version keeps its source run, and the "
    "notebooks live in Git.\n\n"
    "ASK: If a model misbehaves today, can you tell which data and which code produced it?\n"
    "WATCH OUT: in Fabric, Git integration and deployment pipelines for ML experiment and ML model items are in "
    "preview and carry metadata only, not the runs or the model versions. Say so if asked.\n"
    "VERIFY: Azure ML data asset versions appear in the demo but not in our fact sheet. Azure ML records the repo "
    "and commit only for jobs submitted from a local Git repository; the demo also logs the commit as a tag. Delta "
    "time travel reaches back only as far as table retention (VACUUM) allows.\n"
    "SOURCE: https://learn.microsoft.com/en-us/fabric/data-engineering/delta-lake-time-travel\n"
    "SOURCE: https://learn.microsoft.com/en-us/fabric/data-science/machine-learning-artifacts-git-deployment-pipelines\n"
    "SOURCE: https://learn.microsoft.com/en-us/azure/machine-learning/concept-train-model-git-integration\n"
    "TRANSITION: Versioned inputs are what make a run reproducible."
)


# ------------------------------------------------------------------ P2.25 reproducibility
def _draw_reproducible(f):
    s = f.s
    gap = 0.2
    cw = (f.w - 3 * gap) / 4
    strip_h = 0.62
    ch = f.h - strip_h - 0.14
    levers = [
        ("package", "Pin the environment", "Packages, runtime and image fixed and versioned",
         "Environment item: libraries and Spark runtime version", "Environment: curated, or custom image with conda"),
        ("cpu", "Control the compute", "Same runtime, same size, every run",
         "Spark compute settings in the Environment item", "Compute cluster or serverless compute, same size"),
        ("layers", "Keep assets central", "Code, data, models and docs in one governed place",
         "Workspace and OneLake, items synced to Git", "Workspace and shared registries"),
        ("workflow", "Run as a pipeline", "Steps as code, parameters and seeds logged",
         "Notebooks run by a pipeline, stored in Git", "Pipeline jobs built from components"),
    ]
    for i, (icon, title, what, fab, aml) in enumerate(levers):
        _map_card(s, f.x + i * (cw + gap), f.y, cw, ch, icon, title, what, None, fab, aml, top_h=1.62, title_h=0.62,
                  title_size=17)
    sy = f.y + ch + 0.14
    box(s, f.x, sy, f.w, strip_h, tone="amber", radius=0.12, name="randomness strip")
    add_icon(s, "lock", f.x + 0.25, sy + (strip_h - 0.38) / 2, 0.38, color="amber")
    text(s, f.x + 0.85, sy, f.w - 1.1, strip_h,
         ["**And fix the randomness:** log the random seed and the data version of every run."], size=16, anchor="m",
         name="randomness text")


NOTES_25 = (
    "Reproducible means that when the model is passed the same input data, the reproduced model returns the same "
    "output. It comes from a few levers. Pin the environment, so packages, runtime and image are "
    "fixed and versioned. Control the compute, so the same runtime and the same size run every time. Keep assets "
    "central, so code, data, models and documentation live in one governed place. Run as a pipeline: steps as "
    "code, parameters and seeds logged, no manual clicks. On top, fix the randomness by logging the random seed "
    "and the data version.\n\n"
    "Fleet example: the Azure ML demo uses a named environment (env-fleet-sklearn), a named compute cluster "
    "(cpu-cluster) and a fixed random seed in the model parameters. The Fabric demo keeps its notebooks and the "
    "daily pipeline in a Git-connected workspace.\n\n"
    "ASK: Could a colleague rebuild last quarter's model from scratch and get the same metrics?\n"
    "WATCH OUT: bit-for-bit identical results are not always possible, for example with some parallel or GPU "
    "training. The goal is a rebuild you can explain and compare, with the randomness controlled where it can be.\n"
    "IF SHORT ON TIME: skip the mapping cells and keep the four levers and the seed.\n"
    "VERIFY: the fact sheet only covers the Environment item's libraries and runtime version; the compute settings "
    "come from Microsoft Learn, so check that screen before you show it.\n"
    "SOURCE: https://learn.microsoft.com/en-us/fabric/data-engineering/environment-manage-library\n"
    "SOURCE: https://learn.microsoft.com/en-us/fabric/data-engineering/create-and-use-environment\n"
    "TRANSITION: With versions and reproducible runs in place, the next question is when to retrain."
)


# ------------------------------------------------------------------ P2.26 evaluation gate
def _map_row(s, x, y, w, h, platform, txt):
    col, tint = (FAB, FAB_T) if platform == "Fabric" else (AML, AML_T)
    box(s, x, y, w, h, tone="node", radius=0.08, line_w=0.75, line_color=col, fill_color=tint,
        name=f"{platform} row")
    text(s, x + 0.14, y, 1.0, h, [platform], size=12, bold=True, color=col, anchor="m", wrap=False, lint=False,
         name=f"{platform} label")
    text(s, x + 1.15, y, w - 1.3, h, [txt], size=12, anchor="m", name=f"{platform} mapping")


def _draw_gate(f):
    s = f.s
    gap = 0.3
    cw = (f.w - 4 * gap) / 5
    chh = 1.45
    steps = [
        ("Trigger", "Schedule, drift alert or a drop in performance", "azure"),
        ("Train", "Several candidates, every run logged with MLflow", "azure"),
        ("Evaluate", "Same holdout, versus baseline and champion", "azure"),
        ("Gate", "Must beat the champion and pass the checks", "success"),
        ("Promote", "Register, mark the champion, roll out safely", "success"),
    ]
    cards = []
    for i, (title, body, tone) in enumerate(steps):
        cards.append(card(s, f.x + i * (cw + gap), f.y, cw, chh, title, [body], tone=tone, badge=str(i + 1),
                          title_size=16, body_size=14, pad=0.16, after=2, name=f"step {i + 1}: {title}"))
    for a, b in zip(cards, cards[1:]):
        link(s, a, b, "r", "l", w=1.75, name="step arrow")

    extra = max(0.0, f.h - 4.15)
    band, lh = 0.5 + extra * 0.2, 1.42 + extra * 0.25
    yr = f.y + chh + band / 2
    x1, x5 = f.x + cw / 2, f.x + 4 * (cw + gap) + cw / 2
    polyline(s, [(x5, f.y + chh), (x5, yr), (x1, yr), (x1, f.y + chh)], color="muted", w=1.75, dash=True,
             name="monitor loop")
    _chip(s, (x1 + x5) / 2 - 1.5, yr - 0.19, 3.0, 0.38, "eye", "Monitor the live model", "azure", "azure_line")

    ly = f.y + chh + band
    lw = 6.9
    card(s, f.x, ly, lw, lh, "The gate in both demos",
         ["PR-AUC at least 0.01 above the champion (frozen test split)",
          "Top 5 percent precision within 0.02 of the champion",
          f"Fleet: about {d2(F.pr_auc_test['hgb'])} vs about {d2(F.pr_auc_test['logistic'])}, "
          "so the challenger is promoted"],
         icon="shield-check", tone="success", title_size=16, body_size=14, pad=0.16, after=2, name="gate rule")
    card(s, f.x + lw + 0.25, ly, f.w - lw - 0.25, lh, "What stays human",
         ["First release or regulated use: a person approves", "Gate thresholds: the team agrees, then codes them",
          "Fabric demo: a person applies the pointer update"],
         icon="user", tone="amber", title_size=16, body_size=14, pad=0.16, after=2, name="human step")

    my = ly + lh + 0.1
    mh = (f.b - my - 0.06) / 2
    _map_row(s, f.x, my, f.w, mh, "Fabric",
             "Pipeline schedule or Activator, notebooks to train and gate, model version and tag to promote")
    _map_row(s, f.x, my + mh + 0.06, f.w, mh, "Azure ML",
             "Job schedule or monitor alert, pipeline job components to train and gate, registry version or tag")


NOTES_26 = (
    "This closes the loop. A trigger fires: a schedule, a drift alert or a drop in performance. The pipeline "
    "trains several candidates, logs every run, evaluates them on the same holdout and compares them with a "
    "baseline and the current champion. A gate then decides: the challenger must beat the champion and pass the "
    "other checks, such as fairness and latency. If it passes, the model is registered, marked as champion and "
    "rolled out safely, for example as a canary. Nobody runs a notebook by hand, and monitoring starts "
    "the next cycle.\n\n"
    "Fleet example: in both demos the gate promotes only if test PR-AUC is at least 0.01 above the champion and "
    "precision in the top 5 percent is within 0.02 of it. Here the challenger scores about 0.38 against about "
    "0.29, so it is promoted. In the Fabric demo the pipeline runs the gate, but a person applies the pointer "
    "update.\n\n"
    "ASK: Which of these decisions could you automate, and which must stay human?\n"
    "WATCH OUT: automate the low-risk path first. A first release or regulated use case still needs human "
    "approval; the team owns the thresholds.\n"
    "VERIFY: registry aliases are unconfirmed for Azure ML, so the slide says version or tag. An Azure ML monitor "
    "alert reaches a pipeline only through custom routing such as Event Grid. Activator parameters to a Fabric "
    "pipeline are preview.\n"
    "SOURCE: demo code 05-demo-azureml-e2e\\src\\gate.py and notebook nb_08_promotion_gate.\n"
    "TRANSITION: The gate is only as good as its inputs: next, data validation."
)


def build(d: Deck):
    d.custom(
        "P2.21", "Most ML projects stall before they reach production", _draw_barriers,
        notes=NOTES_21, minutes=2.5, core=True,
        takeaway="MLOps exists to remove these barriers: build fast and repeatably, then keep models healthy once live.",
    )
    d.custom(
        "P2.22", "The ML lifecycle is a loop, and retraining is where manual work piles up", _draw_lifecycle,
        notes=NOTES_22, minutes=4, core=True,
        takeaway="Automate the loop (version, validate, gate, deploy, monitor), do not just run it faster.",
    )
    d.custom(
        "P2.23", "Four continuous practices lead to six capabilities", _draw_practices,
        notes=NOTES_23, minutes=3, core=True,
        takeaway="The four practices are the 'what', the six capabilities are the 'how' you will see next.",
    )
    d.custom(
        "P2.24", "Version everything that changes: code, data, models and experiments", _draw_versioning,
        notes=NOTES_24, minutes=3, core=True,
        takeaway="Version it all, so you can revert to a known state or see exactly where a problem was introduced and fixed.",
        source="Microsoft Learn: Fabric Delta time travel, Fabric Git integration for ML items, Azure ML Git integration, "
               "verified 2026-10-22",
    )
    d.custom(
        "P2.25", "Reproducible means the same inputs give the same model and outputs",
        _draw_reproducible, notes=NOTES_25, minutes=3, core=False,
        takeaway="Reduce the randomness of machine learning so that any run can be repeated by someone else.",
    )
    d.custom(
        "P2.26", "Evaluate every candidate, then promote automatically", _draw_gate,
        notes=NOTES_26, minutes=4, core=True,
        takeaway="A trigger should end in a registered, gated, promoted model, without anyone running a notebook.",
    )
