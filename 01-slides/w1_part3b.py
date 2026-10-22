"""Part 3, block B2: CT, drift and A/B focus slides, promotion and workspace patterns, lab (P3.41 to P3.48)."""
from __future__ import annotations

from pptx.enum.dml import MSO_LINE

from deck_core import (HEAD, MONO, add_icon, arrow, box, fill_text, label, lint_fit, num_badge, pill, polyline, text,
                       text_w)
from facts import F

EYEBROW = "PART 3  \u00b7  MLOPS IN FABRIC AND AML"
TEAL, TEAL_T = "0F7B6C", "E6F4F1"
BLUE, BLUE_T = "005A9E", "E8F1FA"
CHIPS = {"native": ("NATIVE", "success"), "preview": ("PREVIEW", "amber"), "build": ("BUILD IT", "muted")}


# ------------------------------------------------------------------ shared helpers
def _chip_w(lab, size=12):
    return text_w(lab, MONO, size, True) + len(lab) * 0.6 / 72 + 0.26


def _chip(s, cx, y, kind, h=0.27):
    lab, tone = CHIPS[kind]
    shp, _ = pill(s, cx - _chip_w(lab) / 2, y, lab, tone=tone, size=12, h=h, name=f"chip: {lab}")
    if kind == "build":
        shp.line.dash_style = MSO_LINE.DASH
    return shp


def _solid_tag(s, x, y, txt, color, h=0.27, size=12):
    w = _chip_w(txt, size) + 0.04
    shp = box(s, x, y, w, h, radius=h / 2, fill_color=color, line_color=color, name=f"tag: {txt}")
    fill_text(shp.text_frame, [txt], size=size, color="white", font=MONO, bold=True, align="c", anchor="m",
              margins=(0.04, 0, 0.04, 0), wrap=False, track=0.6)
    return w


def _panel(s, x, y, w, h, paras, tone, name, size=14, m=(0.16, 0.12, 0.12, 0.08), anchor="t", **boxkw):
    shp = box(s, x, y, w, h, tone=tone, radius=0.12, name=name, **boxkw)
    fill_text(shp.text_frame, paras, size=size, anchor=anchor, margins=m)
    lint_fit(name, paras, w - m[0] - m[2], h - m[1] - m[3], size=size)
    return shp


def _node(s, x, y, w, h, verb, obj, line_color, name):
    shp = box(s, x, y, w, h, tone="paper", radius=0.09, line_w=1.25, line_color=line_color, name=name)
    paras = [dict(text=verb, size=14, bold=True, after=2), dict(text=obj, size=12)]
    m = (0.09, 0.07, 0.06, 0.04)
    fill_text(shp.text_frame, paras, size=12, anchor="t", margins=m)
    lint_fit(name, paras, w - m[0] - m[2], h - m[1] - m[3], size=12)
    return shp


def _lane(s, x, y, w, h, name, color, tint, desc, steps):
    box(s, x, y, w, h, tone="paper", radius=0.12, line_w=1.0, fill_color=tint, line_color=color, name=f"lane: {name}")
    tag_w = _solid_tag(s, x + 0.12, y + 0.07, name, color)
    text(s, x + 0.12 + tag_w + 0.14, y + 0.07, w - tag_w - 0.4, 0.27, [desc], size=12, color="muted", anchor="m",
         wrap=False, lint=False, name=f"lane note: {name}")
    n, gap = len(steps), 0.25
    bw = (w - 0.24 - gap * (n - 1)) / n
    by = y + 0.07 + 0.27 + 0.07
    chip_y = y + h - 0.07 - 0.27
    bh = chip_y - 0.06 - by
    for i, (verb, obj, kind) in enumerate(steps):
        bx = x + 0.12 + i * (bw + gap)
        _node(s, bx, by, bw, bh, verb, obj, color, f"{name} step {i + 1}: {verb}")
        _chip(s, bx + bw / 2, chip_y, kind)
        if i < n - 1:
            arrow(s, bx + bw + 0.03, by + bh / 2, bx + bw + gap - 0.03, by + bh / 2, color=color, w=1.5,
                  name=f"arrow {name} {i + 1}")


def _watch(s, x, y, w, h, msg):
    box(s, x, y, w, h, tone="amber", radius=0.1, name="watch out strip")
    add_icon(s, "alert-triangle", x + 0.14, y + (h - 0.3) / 2, 0.3, color="amber")
    label(s, x + 0.52, y, 1.1, "WATCH OUT", size=12, color="amber", align="l", bold=True, h=h, name="watch out tag")
    text(s, x + 1.62, y, w - 1.62 - 0.14, h, [msg], size=14, anchor="m", name="watch out text")


def _lanes_slide(f, need, demo, fabric, aml, watch):
    s = f.s
    left_w, gap, need_h, watch_h = 2.5, 0.15, 2.5, 0.6
    paras = [dict(text="WHAT WE NEED", size=12, font=MONO, bold=True, color="azure", track=1.0, after=2)]
    for lab, stmt in need:
        paras.append(dict(text=lab, size=12, font=MONO, bold=True, color="muted", track=1.0, before=5))
        paras.append(dict(text=stmt, size=14))
    _panel(s, f.x, f.y, left_w, need_h, paras, "azure", "what we need")
    demo_paras = [dict(text="IN THE FLEET DEMO", size=12, font=MONO, bold=True, color="azure", track=1.0, after=3)]
    demo_paras += [dict(after=4) | (p if isinstance(p, dict) else dict(text=p)) for p in demo]
    _panel(s, f.x, f.y + need_h + 0.1, left_w, f.h - need_h - 0.1, demo_paras, "node", "fleet demo", size=12.5)
    lx = f.x + left_w + gap
    lw = f.r - lx
    lane_h = (f.h - watch_h - 0.2) / 2
    _lane(s, lx, f.y, lw, lane_h, "FABRIC", TEAL, TEAL_T, fabric["desc"], fabric["steps"])
    _lane(s, lx, f.y + lane_h + 0.1, lw, lane_h, "AZURE ML", BLUE, BLUE_T, aml["desc"], aml["steps"])
    _watch(s, lx, f.b - watch_h, lw, watch_h, watch)


# ------------------------------------------------------------------ P3.41 to P3.44 content
P41 = dict(
    need=[("GOAL", "Fresh models, no manual runs"),
          ("TRIGGER", "Schedule, new data or drift alert"),
          ("SUCCESS", "Beats the champion")],
    demo=["Same gate in both demos: test PR-AUC at least **0.01** above the champion, precision at the top 5% no more "
          "than **0.02** below."],
    fabric=dict(desc="Demo 2a: pipeline `pl_fleet_daily`, notebooks, MLflow", steps=[
        ("Schedule", "Pipeline trigger or Activator rule", "native"),
        ("Validate", "ETL notebooks, quality checks", "build"),
        ("Train", "MLflow run, candidate version", "native"),
        ("Gate", "Challenger vs champion in `nb_08`", "build"),
        ("Promote", "Pointer table `ml.model_pointer`", "build"),
    ]),
    aml=dict(desc="Demo 2b: pipeline job `pipeline-train.yml`, weekday schedule", steps=[
        ("Schedule", "Job schedule or monitoring alert", "native"),
        ("Validate", "Prep component, contract check", "build"),
        ("Train", "Train component, MLflow run", "native"),
        ("Gate", "Challenger vs champion metrics", "build"),
        ("Register", "Version only if gate approves", "native"),
    ]),
    watch="A schedule retrains, it does not improve. Without the gate, a worse model can replace a good one.",
)

P42 = dict(
    need=[("GOAL", "Catch accuracy decay"),
          ("TRIGGER", "Labels arrive (Fleet: 7 days later)"),
          ("SUCCESS", "Alert before the business notices")],
    demo=["No October labels yet, so both demos watch the inputs first (next slide), not accuracy.",
          "Label `fail_next_7d` arrives 7 days later."],
    fabric=dict(desc="No managed monitor for classical models: you wire tables, notebooks and alerts", steps=[
        ("Log", "Scores in a Delta table", "native"),
        ("Join", "Notebook joins actuals after 7 days", "build"),
        ("Measure", "PR-AUC per week in a metrics table", "build"),
        ("Alert", "Pipeline email or Activator rule", "native"),
        ("Retrain", "Rule starts the training pipeline", "native"),
    ]),
    aml=dict(desc="Model monitoring: data collection plus a model performance signal", steps=[
        ("Collect", "Data collection on the endpoint", "native"),
        ("Join", "Ground truth with a shared ID", "build"),
        ("Measure", "Accuracy, precision, recall", "preview"),
        ("Alert", "Threshold, email or Event Grid", "native"),
        ("Retrain", "Event Grid starts the pipeline job", "native"),
    ]),
    watch="Labels lag, so accuracy always describes last week, not today.",
)

P43 = dict(
    need=[("GOAL", "Spot input change before accuracy falls"),
          ("TRIGGER", "Each new data batch"),
          ("SUCCESS", "PSI over the threshold raises an alert")],
    demo=[dict(text=f"**{F.drift_combinations}** class \u00d7 sensor pairs checked", size=14),
          dict(text=f"**{len(F.drift_major)}** major, **{len(F.drift_moderate)}** moderate, **{F.drift_stable}** stable",
               size=14)],
    fabric=dict(desc="Demo 2a: `nb_07_drift_monitor` writes `ml.drift_report`", steps=[
        ("Baseline", "September readings, 10 bins", "build"),
        ("Compare", "PSI per class and sensor", "build"),
        ("Threshold", "0.10 and 0.25 in a Variable Library", "native"),
        ("Alert", "Pipeline If activity, then email", "native"),
        ("Act", "Review the report, retrain if real", "build"),
    ]),
    aml=dict(desc="Demo 2b: `drift` job (PSI). The monitoring schedule is the managed option", steps=[
        ("Baseline", "Training data as the reference", "native"),
        ("Compare", "Built-in data drift signal", "native"),
        ("Threshold", "Set per metric and feature", "native"),
        ("Alert", "Alert email or Event Grid", "native"),
        ("Act", "Retrain job, or investigate", "build"),
    ]),
    watch=f"An alert is a question, not a verdict: the {len(F.drift_moderate)} moderate shifts are seasonal cooling, so "
          "investigate before you retrain.",
)

P44 = dict(
    need=[("GOAL", "Try a challenger safely"),
          ("TRIGGER", "A new version passes the gate"),
          ("SUCCESS", "Challenger wins, or one-command rollback")],
    demo=["Demo 2b: `fleet-risk-online`, blue is live, green is the new version. Demo 2a scores in batch."],
    fabric=dict(desc="Model item versions, preview endpoints or batch scoring", steps=[
        ("Pick", "Champion and challenger", "native"),
        ("Score", "Same data, via preview endpoints", "preview"),
        ("Compare", "Route in your app, or score both", "build"),
        ("Decide", "Gate rule in `nb_08`", "build"),
        ("Switch", "Update the pointer table", "build"),
    ]),
    aml=dict(desc="Demo 2b: managed online endpoint with blue and green deployments", steps=[
        ("Deploy", "Green with 0% live traffic", "native"),
        ("Mirror", "10% shadow, clients get blue", "native"),
        ("Shift", "Live 90/10, then 50/50", "native"),
        ("Compare", "Logs, App Insights, labels later", "native"),
        ("Decide", "`green=100`, or back to blue", "native"),
    ]),
    watch="Azure ML: a deployment is live or mirrored, never both. Fabric: no traffic split is documented, so you "
          "design the comparison.",
)


# ------------------------------------------------------------------ P3.45: promote the code or the model
CODE_SIDE = dict(
    tag="CODE-CENTRIC", title="Promote the code and retrain", sub="Common when the workspace owns the data.",
    tone="node", boxes=[("Dev", 1.5), ("Test", 1.5), ("Prod", 1.5)], arrows=["code", "code"],
    chips=[("TRAIN", "azure"), ("RETRAIN", "azure"), ("RETRAIN", "azure")],
    bullets=["**What moves:** notebooks, pipelines and environment metadata. You retrain in each workspace.",
             "**Strength:** a strong fit for Fabric, where Git sync carries item metadata, not run history.",
             "**Tradeoff:** the prod model is reproducible from code, not byte-identical to dev."],
    when="**Choose when:** prod data stays in prod, the pipeline is cheap to rerun, you are Fabric-first.",
)
MODEL_SIDE = dict(
    tag="MODEL-CENTRIC", title="Train once, promote the model", sub="Common when serving discipline leads.",
    tone="azure", boxes=[("Dev", 1.1), ("Registry", 1.2), ("Test", 1.1), ("Prod", 1.1)],
    arrows=["model artifact", "", ""],
    chips=[("TRAIN ONCE", "azure"), ("REGISTER", "azure"), ("DEPLOY", "azure"), ("NO RETRAIN", "dark")],
    bullets=["**What moves:** one registered version, shared through an Azure ML registry, deployed with its environment.",
             "**Strength:** traceability, the artifact you serve is the artifact you approved.",
             "**Tradeoff:** registry access, approvals and rollout controls join the platform contract."],
    when="**Choose when:** audits need the exact artifact, training is costly or special, you use Azure ML.",
)


def _draw_promote(f):
    s = f.s
    gap = 0.2
    pw = (f.w - gap) / 2
    for i, sp in enumerate((CODE_SIDE, MODEL_SIDE)):
        x = f.x + i * (pw + gap)
        ix, iw = x + 0.16, pw - 0.32
        box(s, x, f.y, pw, f.h, tone=sp["tone"], radius=0.14, name=f"panel: {sp['tag']}")
        tw = _solid_tag(s, ix, f.y + 0.12, sp["tag"], "azure")
        text(s, ix + tw + 0.14, f.y + 0.12, iw - tw - 0.14, 0.27, [sp["sub"]], size=14, color="muted", anchor="m",
             wrap=False, lint=False, name="panel sub")
        text(s, ix, f.y + 0.46, iw, 0.36, [sp["title"]], size=18, bold=True, font=HEAD, anchor="m", wrap=False,
             lint=False, name="panel title")
        n = len(sp["boxes"])
        widths = [w for _, w in sp["boxes"]]
        g = (iw - sum(widths)) / (n - 1)
        yd = f.y + 0.84
        xs = [ix + sum(widths[:k]) + k * g for k in range(n)]
        for k, (nm, bw) in enumerate(sp["boxes"]):
            shp = box(s, xs[k], yd + 0.22, bw, 0.5, tone="paper", radius=0.1, line_w=1.25, line_color="azure",
                      name=f"{sp['tag']} stage: {nm}")
            fill_text(shp.text_frame, [nm], size=14, bold=True, align="c", anchor="m", margins=(0.04, 0, 0.04, 0),
                      wrap=False)
            lab, tone = sp["chips"][k]
            lw_ = _chip_w(lab)
            cx = min(max(xs[k] + bw / 2 - lw_ / 2, ix), ix + iw - lw_)
            pill(s, cx, yd + 0.76, lab, tone=tone, size=12, h=0.27, name=f"chip: {lab}")
            if k < n - 1:
                arrow(s, xs[k] + bw + 0.03, yd + 0.47, xs[k + 1] - 0.03, yd + 0.47, color="muted", w=1.5,
                      name=f"arrow {k + 1}")
                if sp["arrows"][k]:
                    label(s, xs[k] + bw + g / 2 - 0.7, yd, 1.4, sp["arrows"][k], size=10.5, color="muted",
                          name=f"label: {sp['arrows'][k]}")
        text(s, ix, f.y + 1.92, iw, 1.55, [dict(text=b, bullet=True, after=2) for b in sp["bullets"]], size=14,
             name=f"bullets {sp['tag']}")
        _panel(s, x + 0.12, f.y + f.h - 0.64, pw - 0.24, 0.56, [dict(text=sp["when"], size=14)], "paper",
               f"choose when {sp['tag']}", m=(0.14, 0.03, 0.1, 0.03), anchor="m")


# ------------------------------------------------------------------ P3.46: code-centric workspaces
WS_ITEMS = ("Data and storage", "Training pipeline and model", "Endpoint")


def _draw_workspaces(f):
    s = f.s
    gap = 0.2
    pw = (f.w - gap) / 2
    heads = [("2 WORKSPACES", "A workspace is a Fabric or an Azure ML workspace"),
             ("1 WORKSPACE", "Same repo and pipelines, one place to run")]
    stages = [("Dev", "node"), ("Prod", "azure")]
    pipes = (("Dev pipeline", "trigger: dev branch"), ("Release pipeline", "trigger: production branch"))
    captions = ["**Stronger isolation:** each stage gets its own data, compute, permissions and endpoints.",
                "**Simpler and cheaper:** one set of resources, but isolation depends on naming and discipline."]
    for i, (tag, note) in enumerate(heads):
        x = f.x + i * (pw + gap)
        ix, iw = x + 0.16, pw - 0.32
        box(s, x, f.y, pw, f.h, tone="paper", radius=0.14, name=f"panel: {tag}")
        tw = _solid_tag(s, ix, f.y + 0.1, tag, "azure")
        text(s, ix + tw + 0.14, f.y + 0.1, iw - tw - 0.14, 0.27, [note], size=12, color="muted", anchor="m",
             wrap=False, lint=False, name="panel note")
        ry, rh = f.y + 0.46, 0.78
        box(s, ix, ry, iw, rh, tone="node", radius=0.1, name="git repo")
        add_icon(s, "git-branch", ix + 0.12, ry + 0.07, 0.3, color="azure")
        text(s, ix + 0.5, ry + 0.07, 1.0, 0.3, ["Git repo"], size=14, bold=True, anchor="m", wrap=False, lint=False,
             name="git repo title")
        text(s, ix + 1.5, ry + 0.07, iw - 1.5 - 0.12, 0.3, ["pull request + branch protection"], size=12,
             color="muted", align="r", anchor="m", wrap=False, lint=False, name="git repo caption")
        cx = ix + 0.12
        for br in ("main", "production", "dev", "experimentation"):
            _, w_ = pill(s, cx, ry + 0.43, br, tone="azure", size=12, h=0.27, caps=False, name=f"branch: {br}")
            cx += w_ + 0.08
        pw2 = (iw - 0.2) / 2
        py, ph = ry + rh + 0.22, 0.6
        wy, wh = py + ph + 0.22, 1.5
        for j, (nm, trig) in enumerate(pipes):
            px = ix + j * (pw2 + 0.2)
            arrow(s, px + pw2 / 2, ry + rh + 0.02, px + pw2 / 2, py - 0.02, color="muted", w=1.5,
                  name=f"arrow repo to {nm}")
            _node(s, px, py, pw2, ph, nm, trig, "azure", f"{tag} {nm}")
            arrow(s, px + pw2 / 2, py + ph + 0.02, px + pw2 / 2, wy - 0.02, color="muted", w=1.5,
                  name=f"arrow {nm} to workspace")
        if i == 0:
            for j, (stage, tone) in enumerate(stages):
                body = [dict(text=f"{stage} workspace", size=14, bold=True, after=3)]
                body += [dict(text=t, size=12, bullet=True) for t in WS_ITEMS]
                body.append(dict(text="Own access and compute", size=12, color="muted", before=5))
                _panel(s, ix + j * (pw2 + 0.2), wy, pw2, wh, body, tone, f"{stage} workspace", size=12,
                       m=(0.14, 0.1, 0.1, 0.05), line_w=1.25, line_color="azure")
        else:
            box(s, ix, wy, iw, wh, tone="paper", radius=0.12, line_w=1.25, line_color="muted", name="one workspace")
            sw = (iw - 0.3) / 2
            for j, (stage, tone) in enumerate(stages):
                body = [dict(text=f"{stage} stage", size=14, bold=True, after=3)]
                body += [dict(text=t, size=12, bullet=True) for t in WS_ITEMS]
                _panel(s, ix + 0.1 + j * (sw + 0.1), wy + 0.08, sw, 1.05, body, tone, f"{stage} stage", size=12,
                       m=(0.14, 0.06, 0.1, 0.03))
            label(s, ix + 0.1, wy + 1.17, iw - 0.2, "Naming, folders and permissions keep the stages apart", size=12,
                  color="muted", mono=False, h=0.25)
        text(s, ix, wy + wh + 0.08, iw, 0.5, [captions[i]], size=14, anchor="t", name=f"caption {tag}")

# ------------------------------------------------------------------ P3.47: model-centric workspaces
def _stage(s, x, y, w, h, title, lines, tone="node", name=None):
    shp = box(s, x, y, w, h, tone=tone, radius=0.12, line_w=1.25, line_color="azure", name=name or f"stage: {title}")
    paras = [dict(text=title, size=15, bold=True, font=HEAD, after=3)] + [dict(text=t, size=12) for t in lines]
    m = (0.14, 0.1, 0.1, 0.05)
    fill_text(shp.text_frame, paras, size=12, margins=m)
    lint_fit(name or title, paras, w - m[0] - m[2], h - m[1] - m[3], size=12)
    return shp


def _info_box(s, x, y, w, h, title, sub, icon, name):
    shp = box(s, x, y, w, h, tone="node", radius=0.1, line_w=1.25, line_color="azure", name=name)
    fill_text(shp.text_frame, [dict(text=title, size=14, bold=True, after=1), dict(text=sub, size=12)], size=12,
              anchor="m", margins=(0.52, 0.02, 0.06, 0.02))
    add_icon(s, icon, x + 0.12, y + (h - 0.3) / 2, 0.3, color="azure")
    return shp


def _draw_model_centric(f):
    s = f.s
    widths = [3.0, 2.3, 2.5, 2.7]
    gap = (f.w - sum(widths)) / 3
    xs = [f.x + sum(widths[:k]) + k * gap for k in range(4)]
    cxs = [xs[k] + widths[k] / 2 for k in range(4)]
    wy, wh = f.y + 1.25, 1.5
    gw, px, pw = 2.6, f.x + 3.15, 3.4
    _info_box(s, f.x, f.y, gw, 0.6, "Git repo", "Code and pipelines", "git-branch", "git repo")
    _info_box(s, px, f.y, pw, 0.6, "CI/CD pipeline", "Train job, tests, deploy steps", "workflow", "ci cd pipeline")
    arrow(s, f.x + gw + 0.03, f.y + 0.3, px - 0.03, f.y + 0.3, color="muted", w=1.5, name="arrow repo to pipeline")
    pcx, bus = px + pw / 2, f.y + 0.95
    for k in (0, 2, 3):
        polyline(s, [(pcx, f.y + 0.62), (pcx, bus), (cxs[k], bus), (cxs[k], wy - 0.02)], color="muted", w=1.5,
                 name=f"path pipeline to stage {k + 1}")
    label(s, (cxs[0] + pcx) / 2 - 0.6, bus - 0.25, 1.2, "train job", size=10.5, name="label train job")
    label(s, (cxs[2] + cxs[3]) / 2 - 0.6, bus - 0.25, 1.2, "deploy", size=10.5, name="label deploy")
    _stage(s, xs[0], wy, widths[0], wh, "Dev workspace",
           ["Data and features", "Training pipeline, experiments", "Evaluation against the champion"])
    _stage(s, xs[1], wy, widths[1], wh, "Model registry",
           ["Model versions and tags", "Approval status", "Environment goes with it"], tone="azure")
    _stage(s, xs[2], wy, widths[2], wh, "Test workspace",
           ["Deploy the exact version", "Smoke test and load test", "Results feed the gate"])
    _stage(s, xs[3], wy, widths[3], wh, "Prod workspace", ["Serve and monitor", "Drift and performance checks"])
    pill(s, xs[3] + 0.14, wy + wh - 0.4, "NO RETRAINING", tone="dark", size=12, h=0.27, name="chip: no retraining")
    add_icon(s, "package", xs[1] + widths[1] - 0.46, wy + 0.1, 0.3, color="azure")
    for k in (0, 1):
        arrow(s, xs[k] + widths[k] + 0.03, wy + wh / 2, xs[k + 1] - 0.03, wy + wh / 2, color="muted", w=1.5,
              name=f"arrow stage {k + 1}")
    low = wy + wh + 0.42
    polyline(s, [(cxs[1], wy + wh + 0.02), (cxs[1], low), (cxs[3], low), (cxs[3], wy + wh + 0.03)], color="amber",
             w=1.75, name="path registry to prod")
    aw = _chip_w("APPROVAL GATE")
    pill(s, (cxs[1] + cxs[3]) / 2 - aw / 2, low - 0.135, "APPROVAL GATE", tone="amber", size=12, h=0.27,
         name="chip: approval gate")
    _panel(s, f.x, f.b - 0.5, f.w, 0.5, [dict(text="**Same artifact everywhere:** model `fleet-failure-7d` version N "
                                              "and its environment `env-fleet-sklearn`, promoted as one unit.",
                                              size=14)],
           "success", "same artifact strip", m=(0.2, 0.04, 0.12, 0.04), anchor="m")

# ------------------------------------------------------------------ P3.48: lab
PIECES = [
    ("Reconcile two sources", "Key match, dedupe, one data-quality check", "FABRIC"),
    ("Train, track and compare", "Baseline and challenger in MLflow, one table", "EITHER"),
    ("Add a promotion gate", "Champion vs challenger rule as code, tagged version", "EITHER"),
    ("Add a drift check and an alert", "One PSI table, one threshold, one notification", "EITHER"),
    ("Deploy and score", "Batch or online endpoint, plus one smoke test", "AZURE ML"),
]
FIELDS = ["Use case and owner", "Data sources and their keys", "Platform choice and why", "Pillars you need first",
          "First milestone and success metric"]
STARTS = [
    ("microsoft-fabric", "`04-demo-fabric-e2e`: start with its `rebuild-guide.md`"),
    ("azure-machine-learning", "`05-demo-azureml-e2e`: same, `rebuild-guide.md` first"),
    ("shield-check", "No capacity yet? Each kit has pre-baked fallbacks."),
    ("cloud", "Need a workspace? `infra` has the Bicep, `deploy` has the steps."),
]


def _draw_lab(f):
    s = f.s
    strip_h = 0.95
    main_h = f.h - strip_h - 0.12
    lw = 6.7
    rx = f.x + lw + 0.17
    rw = f.r - rx
    text(s, f.x, f.y, lw, 0.3, ["Pick one piece (30 to 40 minutes)"], size=16, bold=True, font=HEAD, anchor="m",
         wrap=False, lint=False, name="pick heading")
    ch = (main_h - 0.36 - 4 * 0.05) / 5
    for i, (ttl, deliv, tag) in enumerate(PIECES):
        y = f.y + 0.36 + i * (ch + 0.05)
        box(s, f.x, y, lw, ch, tone="node", radius=0.1, name=f"piece {i + 1}")
        num_badge(s, f.x + 0.12, y + (ch - 0.32) / 2, i + 1, size=0.32, fsize=13)
        text(s, f.x + 0.58, y, lw - 0.58 - 1.4, ch, [dict(text=ttl, size=14, bold=True),
                                                    dict(text=deliv, size=12, color="muted")],
             anchor="m", name=f"piece text {i + 1}")
        tw = _chip_w(tag) + 0.04
        tx, ty = f.x + lw - tw - 0.12, y + (ch - 0.27) / 2
        if tag == "EITHER":
            pill(s, tx, ty, tag, tone="muted", size=12, h=0.27, name=f"tag: {tag}")
        else:
            _solid_tag(s, tx, ty, tag, TEAL if tag == "FABRIC" else BLUE)
    text(s, rx, f.y, rw, 0.3, ["Your one-page blueprint"], size=16, bold=True, font=HEAD, anchor="m", wrap=False,
         lint=False, name="blueprint heading")
    fy = 0.37
    for j, fld in enumerate(FIELDS):
        y = f.y + 0.36 + j * (fy + 0.05)
        shp = box(s, rx, y, rw, fy, tone="paper", dash=True, radius=0.08, line_w=1.25, line_color="sand",
                  name=f"blueprint field {j + 1}")
        fill_text(shp.text_frame, [f"{j + 1}.  {fld}"], size=14, anchor="m", margins=(0.14, 0.02, 0.1, 0.02),
                  wrap=False)
    ry = f.y + 0.36 + 5 * (fy + 0.05) + 0.05
    _panel(s, rx, ry, rw, f.y + main_h - ry, [dict(text="**Readout, 3 minutes per group:** what you built, what "
                                                   "blocked you, what you would standardize.", size=14)],
           "success", "readout", m=(0.14, 0.03, 0.1, 0.03), anchor="m")
    sy = f.b - strip_h
    box(s, f.x, sy, f.w, strip_h, tone="azure", radius=0.12, name="where to start strip")
    label(s, f.x + 0.16, sy + 0.05, 2.0, "WHERE TO START", size=12, color="azure", align="l", bold=True, h=0.24)
    cw_ = (f.w - 0.32 - 3 * 0.15) / 4
    for k, (icon, txt) in enumerate(STARTS):
        cx = f.x + 0.16 + k * (cw_ + 0.15)
        add_icon(s, icon, cx, sy + 0.38, 0.3, color="azure")
        text(s, cx + 0.4, sy + 0.3, cw_ - 0.4, 0.62, [txt], size=12.5, name=f"start {k + 1}")


# ------------------------------------------------------------------ build
def build(d):
    d.custom(
        "P3.41", "Continuous training: the same loop, two ways to run it",
        lambda f: _lanes_slide(f, **P41),
        eyebrow=EYEBROW,
        takeaway="Continuous training is a loop with a gate: retrain on a trigger, but only a version that beats the "
                 "champion ships.",
        minutes=3, core=False,
        notes="""Continuous training is the same loop on both platforms: a trigger starts a run, the data is checked, a model is trained and logged, a gate compares it with the champion, and only a winner moves on. What differs is who owns each step. Read the chips: native means the platform gives you the piece, build it means you write it.

In Fabric you compose the loop: a pipeline trigger, notebooks, an MLflow run, a model item with versions. In Demo 2a, pl_fleet_daily runs nb_05, which registers a candidate tagged pending_gate, then nb_08 decides. It is report only: the pointer table changes when a person re-runs the gate with the update switch on.

In Azure ML the loop is one pipeline job: prepare, train, evaluate, gate, register. A weekday 06:00 schedule runs it, and a version is registered only if the gate approves.

The gate rule is the same in both: test PR-AUC at least 0.01 above the champion, precision at the top 5 percent no more than 0.02 below.

ASK: What starts retraining in your team: a calendar, new data, or a person?
WATCH OUT: a schedule retrains, it does not improve.
IF SHORT ON TIME: read only the chips.
SOURCE: https://learn.microsoft.com/en-us/azure/machine-learning/how-to-schedule-pipeline-job?view=azureml-api-2
SOURCE: https://learn.microsoft.com/en-us/fabric/real-time-intelligence/data-activator/activator-introduction
VERIFY: an Activator rule that starts a pipeline from a Delta table is not exercised in the demo; check the source binding first.
TRANSITION: The best trigger is a decay signal, so next is model drift.""",
    )

    d.custom(
        "P3.42", "Model drift: you need labels, so plan the join",
        lambda f: _lanes_slide(f, **P42),
        eyebrow=EYEBROW,
        takeaway="Plan the label join on day one: without actuals you can watch the inputs, but you cannot measure "
                 "accuracy.",
        minutes=3, core=False,
        notes="""Model drift means the quality of the model decays, and you only see it when you know the true answer. In the Fleet scenario the label, a failure in the next 7 days, arrives a week after the prediction. So store every prediction, join the actuals when they land, and measure by week.

In Azure ML this is model monitoring: enable production data collection on the endpoint, supply ground truth data with a shared ID, and add a model performance signal for accuracy, precision and recall. Say preview out loud: that signal is marked preview on Microsoft Learn. Alerts go out by email or Event Grid, and Event Grid can start retraining.

Fabric has no first-party managed monitor for classical ML models, so you build it: scores in a Delta table (ml.failure_risk_score in Demo 2a), a notebook that joins actuals and writes PR-AUC per week, then a pipeline alert or an Activator rule.

Neither demo has October labels, so they monitor inputs first.

ASK: How long does your ground truth take to arrive, and who owns the join?
WATCH OUT: labels lag, so accuracy always describes last week.
IF SHORT ON TIME: say "store, join, measure" and move on.
SOURCE: https://learn.microsoft.com/en-us/azure/machine-learning/concept-model-monitoring?view=azureml-api-2
VERIFY: the performance signal is still preview; ground truth join mechanics and data collection for batch endpoints; whether Activator can bind to a Delta table.
TRANSITION: Until labels arrive, the inputs are the early warning: data drift.""",
    )

    d.custom(
        "P3.43", "Data drift: compare today's inputs with the training baseline",
        lambda f: _lanes_slide(f, **P43),
        eyebrow=EYEBROW,
        takeaway="Drift says the world changed, not that the model is wrong: treat an alert as a prompt to investigate.",
        minutes=3, core=False,
        notes=f"""Data drift is the early warning: compare today's inputs with the baseline the model learned from, feature by feature, before any label exists. The usual statistic is the population stability index, PSI. A common rule of thumb: below 0.10 stable, 0.10 to 0.25 moderate, above 0.25 major.

In Fabric, Demo 2a does this in nb_07_drift_monitor: PSI per equipment class and sensor, against decile bins from September readings. The thresholds 0.10 and 0.25 come from the Variable Library, the result lands in ml.drift_report, and the pipeline emails only for major drift. Of {F.drift_combinations} pairs, {len(F.drift_major)} are major, {len(F.drift_moderate)} moderate and {F.drift_stable} stable; the moderate ones are seasonal cooling.

In Azure ML, the model monitoring data drift signal compares production data with a reference such as the training data, with PSI, Jensen-Shannon, Wasserstein, KS and chi-squared metrics. The kit's monitoring schedule is flagged preview, so Demo 2b guarantees the path with a drift job that runs drift.py (PSI).

ASK: Which three features would you monitor first, and who gets the alert?
WATCH OUT: an alert is a question, not a verdict.
IF SHORT ON TIME: skip the metric names and show the 4, 3 and 40.
SOURCE: https://learn.microsoft.com/en-us/azure/machine-learning/concept-model-monitoring?view=azureml-api-2
VERIFY: the IfDriftAlert condition reads the notebook exit value (output.result.exitValue); GA or preview status of the monitoring schedule; Activator binding to ml.drift_report.
TRANSITION: When a candidate is ready, how do we test it on live traffic?""",
    )

    d.custom(
        "P3.44", "A/B testing: Azure ML splits traffic, in Fabric you design the comparison",
        lambda f: _lanes_slide(f, **P44),
        eyebrow=EYEBROW,
        takeaway="Shadow first, a small live share next, and always keep a one-command way back to the champion.",
        minutes=3, core=False,
        notes="""A/B testing here means testing a challenger on real traffic before it replaces the champion. Azure ML gives you the traffic controls. In Fabric you design the comparison.

In Azure ML, one managed online endpoint holds several deployments. In Demo 2b, fleet-risk-online has blue, live, and green, the new version, created with 0 percent traffic so you can call it by name. Then mirror 10 percent of live requests to green: clients still get blue's answer and you read green's logs. Clear the mirror, shift live traffic 90/10, then 50/50, then green=100. Rollback is blue=100, green=0 (minutes 26 to 29).

Fabric ML model endpoints are preview and can serve several versions of a model, but I found no documented traffic split. So there are three honest options: batch score both versions on the same data and compare against labels; split in the calling application; or serve from an Azure ML endpoint, the hybrid pattern.

ASK: Who decides that a challenger has won, and on which metric?
WATCH OUT: a deployment is live or mirrored, never both, and mirroring is capped at 50 percent.
IF SHORT ON TIME: show the Azure ML lane only and name the three Fabric options.
SOURCE: https://learn.microsoft.com/en-us/azure/machine-learning/how-to-safely-rollout-online-endpoints?view=azureml-api-2
SOURCE: https://learn.microsoft.com/en-us/fabric/data-science/model-endpoints
VERIFY: whether Fabric model endpoints offer any traffic split between versions (none documented); mirroring availability for your endpoint type.
TRANSITION: Once a version wins, the question is how it travels from dev to test to prod.""",
    )

    d.custom(
        "P3.45", "Dev, test, prod: you either promote the code or promote the model",
        _draw_promote,
        eyebrow=EYEBROW,
        takeaway="Many teams mix both: decide per use case and write it down in the platform contract.",
        minutes=4, core=False,
        notes="""There are two ways to get from dev to prod, and you should choose on purpose: promote the code and retrain, or train once and promote the model.

On the left, code-centric. Notebooks, pipelines and environment metadata move through dev, test and prod, and each workspace trains on the data it owns. This fits Fabric well, because Git integration and deployment pipelines carry item definitions, not model run history. The tradeoff: the prod model is reproducible from code, not byte-identical to dev.

On the right, model-centric. You train once, register the version, and share that same version through an Azure ML registry, with its environment, into test and prod. Traceability is strong: you serve the artifact you approved. The tradeoff: registry access, approvals and rollout controls join the platform contract.

In our demos, Fabric moves code (Demo 2a, the cicd folder) and Azure ML moves the model (Demo 2b, GitHub Actions, minutes 37 to 41). Most teams mix both.

ASK: In your last release, did you ship code or did you ship a model?
WATCH OUT: the same code does not give the same model when data or library versions differ.
IF SHORT ON TIME: read the two "choose when" lines and skip the bullets.
SOURCE: https://learn.microsoft.com/en-us/fabric/data-science/machine-learning-artifacts-git-deployment-pipelines
SOURCE: https://learn.microsoft.com/en-us/azure/machine-learning/concept-machine-learning-registries-mlops?view=azureml-api-2
VERIFY: Git integration and deployment pipelines for Fabric ML experiments and models are preview and metadata only; check the current status.
TRANSITION: Next, both views as workspaces, starting with code-centric.""",
    )

    d.custom(
        "P3.46", "Code-centric view: one workspace or two?",
        _draw_workspaces,
        eyebrow=EYEBROW,
        takeaway="Two workspaces give stronger isolation and permissions; one is simpler and cheaper but relies on "
                 "discipline.",
        minutes=3, core=False,
        notes="""Code-centric means the Git repo is the source of truth and the workspaces are only targets. The question is how many workspaces you give it.

Two workspaces, dev and prod, give the strongest isolation: separate data, compute, permissions and endpoints, so a bad run in dev cannot touch prod. One workspace is simpler and cheaper, but dev and prod are separated only by naming, folders and permissions, which means by discipline.

The Git side is the same in both: feature branches, a pull request with branch protection, then a branch per stage.

In Fabric, the usual shape is one workspace per stage, each connected to a Git branch, with deployment pipelines or the fabric-cicd library promoting. Demo 2a ships that in its cicd folder with DEV, TEST and PROD value sets. In Azure ML it is a workspace per stage, and the pipeline deploys jobs and endpoints with the CLI or SDK.

ASK: Who can write to prod today, and how many of them are data scientists?
WATCH OUT: with one workspace, a loose naming rule is how a dev job ends up serving prod.
IF SHORT ON TIME: say "two for isolation, one for simplicity" and move on.
SOURCE: https://learn.microsoft.com/en-us/fabric/cicd/deployment-pipelines/intro-to-deployment-pipelines
SOURCE: https://microsoft.github.io/fabric-cicd/latest/
VERIFY: which Fabric ML items fabric-cicd can publish today; Fabric ML experiments and models in Git are preview and metadata only.
TRANSITION: Same repo and pipelines, but now the model itself travels.""",
    )

    d.custom(
        "P3.47", "Model-centric view: train once, then promote the model, never retrain in prod",
        _draw_model_centric,
        eyebrow=EYEBROW,
        takeaway="The registry is the contract between the teams that train and the teams that serve.",
        minutes=3, core=False,
        notes="""Model-centric means you train once, in dev, and the model itself travels. Dev holds the data, training and evaluation. The winner goes into a model registry with versions, tags and an approval status. Test deploys that exact version and smoke tests it. After an approval gate, prod deploys the same version and only serves and monitors it. Prod never retrains.

In Azure ML this is a shared registry. In Demo 2b the GitHub Actions workflow runs az ml model share from the dev workspace to the registry mlr-fleet-shared, then deploys from the registry to the prod workspace. It signs in with OIDC, and a GitHub environment called prod is the approval gate (minutes 37 to 41).

Fabric is different: I found no documented cross-workspace model registry, and Git and deployment pipelines carry item metadata only. The working patterns are to retrain from code, or to re-register the logged artifact in the target workspace with MLflow. Say plainly that you build this.

ASK: Who owns the registry in your organization: platform team, data science team, or nobody?
WATCH OUT: a registry protects you only if prod can deploy nothing else.
IF SHORT ON TIME: read the takeaway.
SOURCE: https://learn.microsoft.com/en-us/azure/machine-learning/how-to-share-models-pipelines-across-workspaces-with-registries?view=azureml-api-2
SOURCE: https://learn.microsoft.com/en-us/fabric/data-science/machine-learning-cross-workspace-logging
VERIFY: no cross-workspace model registry for Fabric is documented; fabric-cicd support for ML models is unverified; the roles the demo workflow needs.
TRANSITION: Now it is your turn: pick one piece of this pipeline and rebuild it.""",
    )

    d.custom(
        "P3.48", "Lab: rebuild one piece of the pipeline on your own use case",
        _draw_lab,
        eyebrow="HANDS-ON LAB  \u00b7  PART 3  \u00b7  END-TO-END DEMO",
        takeaway="One small piece, rebuilt end to end on your data, teaches more than a perfect plan.",
        minutes=5, core=False,
        notes="""This is the hands-on part, and it is deliberately small: rebuild one piece of the pipeline on your own use case, with a result you can check.

In the room: 30 to 40 minutes in groups of three or four, mixing data scientists and data engineers. Or as a take-home, one piece per sprint.

To facilitate: each group picks one of the five pieces, fills in the one-page blueprint, and builds. Walk the room at about minute 15 and ask what is blocking them. Success is a result you can show: a table, a tagged version, a drift row, or a scored sample.

If capacity is not ready, nobody waits. Each kit has pre-baked outputs and break-glass paths: in the Fabric kit, nb_10_load_gold_break_glass loads the gold table, and the Azure ML run of show lists its fallbacks. For a workspace, the infra folder has the Bicep and the deploy folder has the steps.

ASK: Which piece would you try first, and what data would you use?
WATCH OUT: do not start with the platform; start with the use case and its owner.
IF SHORT ON TIME: skip the cards and ask for a show of hands.
SOURCE: rebuild-guide.md in each demo kit.
VERIFY: the kits were validated offline and in CI, not in a real tenant yet; read VERIFY-BEFORE-FRIDAY.md in each kit first.
TRANSITION: That closes Part 3; next, the bridge between the two platforms.""",
    )
