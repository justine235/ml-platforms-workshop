"""Part 3a: two reference architectures and two MLOps pillar tables (P3.31-P3.34)."""
from __future__ import annotations

from deck_core import (BODY, CTX, HEAD, LINT, add_icon, arrow, box, card, fill_text, label, num_badge, pill, rgb,
                       text, text_w)
from deck_lib import Deck

EYEBROW = "PART 3  \u00b7  MLOPS IN FABRIC AND AML"
TEAL, TEAL_SOFT = "0F7B6C", "E6F4F1"
BLUE, BLUE_SOFT = "005A9E", "E8F1FA"

ARCH_A_SRC = "Microsoft Learn: OneLake and AML bridge, Fabric CI/CD, verified 2026-10-18"
ARCH_B_SRC = "Microsoft Learn: Fabric ML models, endpoints, Git and deployment pipelines, verified 2026-10-18"
PILLARS_1_SRC = "Microsoft Learn: Fabric ML and CI/CD, Azure ML registries and environments, verified 2026-10-18"
PILLARS_2_SRC = "Microsoft Learn: Azure ML endpoints, monitoring; Fabric scoring, Activator, verified 2026-10-18"

LRN = "https://learn.microsoft.com/en-us/"
URL_AML_REG = LRN + "azure/machine-learning/concept-machine-learning-registries-mlops?view=azureml-api-2"
URL_AML_MON = LRN + "azure/machine-learning/concept-model-monitoring?view=azureml-api-2"
URL_FABRIC_PREDICT = LRN + "fabric/data-science/model-scoring-predict"
URL_FABRIC_ML = LRN + "fabric/data-science/machine-learning-model"
URL_FABRIC_ENDPOINTS = LRN + "fabric/data-science/model-endpoints"
URL_FABRIC_ML_CICD = LRN + "fabric/data-science/machine-learning-artifacts-git-deployment-pipelines"
URL_BRIDGE = LRN + "fabric/onelake/onelake-azure-machine-learning"
URL_FABRIC_GIT = LRN + "fabric/cicd/git-integration/intro-to-git-integration"
URL_FABRIC_CICD = "https://github.com/microsoft/fabric-cicd"
URL_AML_ROLLOUT = LRN + "azure/machine-learning/how-to-safely-rollout-online-endpoints?view=azureml-api-2"
URL_AML_GH = LRN + "azure/machine-learning/how-to-github-actions-machine-learning?view=azureml-api-2"


# ---------------------------------------------------------------- shared drawing helpers
def _step(s, x, y, n):
    return num_badge(s, x, y, n, size=0.3, fsize=12)


def _head(s, x, y, w, title, color, n, icon=None):
    """Header row of a container: step badge, product icon, platform name."""
    _step(s, x + 0.1, y + 0.1, n)
    tx = x + 0.46
    if icon:
        add_icon(s, icon, x + 0.46, y + 0.1, 0.3)
        tx = x + 0.84
    text(s, tx, y + 0.1, w - (tx - x) - 0.08, 0.3, [title], size=14, bold=True, font=HEAD, color=color, anchor="m",
         wrap=False, lint=False, name=f"head: {title}")


def _container(s, x, y, w, h, color, soft, name):
    return box(s, x, y, w, h, tone="paper", radius=0.14, line_w=1.5, fill_color=soft, line_color=color, name=name)


def _pnode(s, x, y, w, h, title, sub=None, color="node_line", icon=None, tone="paper", tsize=13, ssize=12,
           sub_color="muted"):
    """White node with a coloured outline: bold title and an optional 12 pt caption."""
    shp = card(s, x, y, w, h, title=title, body=sub, icon=icon, tone=tone, title_size=tsize, body_size=ssize, pad=0.1,
               icon_size=0.28, after=0, body_color=sub_color, icon_color="ink", line_w=1.25, radius=0.1,
               name=f"node: {title}")
    shp.line.color.rgb = rgb(color)
    return shp


def _chip(s, x, y, w, h, txt, color, size=12, fill="FFFFFF", tcolor="ink", bold=False):
    if text_w(txt, BODY, size, bold) * 1.03 + 0.08 > w:
        LINT.append(f"[{CTX['slide']}] chip '{txt}' is wider than {w:.2f} in")
    shp = box(s, x, y, w, h, tone="paper", radius=min(0.12, h / 2), line_w=1.0, line_color=color, fill_color=fill,
              name=f"chip: {txt}")
    fill_text(shp.text_frame, [txt], size=size, color=tcolor, bold=bold, align="c", anchor="m",
              margins=(0.03, 0, 0.03, 0), wrap=False)
    return shp


def _caption(s, x, y, w, txt, color="muted", align="l", h=0.22):
    return label(s, x, y, w, txt, size=12, color=color, align=align, mono=False, h=h)


def _sources(s, x, y0, w, h, ra) -> None:
    """Step 1: the three source systems, drawn the same way on both architectures."""
    box(s, x, y0, w, h, tone="node", radius=0.14, name="group: sources")
    _head(s, x, y0, w, "Sources", "ink", 1)
    for i, t in enumerate(("Telematics events", "Work orders", "ERP assets")):
        _pnode(s, x + 0.1, ra + i * 0.76, w - 0.2, 0.62, t, tsize=12)


# ---------------------------------------------------------------- P3.31 Architecture A
def _arch_a(f) -> None:
    s = f.s
    y0 = f.y
    head_h, node_h, gap, pad_b = 0.5, 1.05, 0.24, 0.1
    ra = y0 + head_h
    rb = ra + node_h + gap
    mb = rb + node_h + pad_b
    main_h = mb - y0
    lane_y = mb + 0.34
    lane_h = f.b - lane_y
    if lane_h < 1.1:
        LINT.append(f"[{CTX['slide']}] delivery lane is only {lane_h:.2f} in high")
    cy_a, cy_b = ra + node_h / 2, rb + node_h / 2

    src_x, src_w = f.x, 1.3
    fab_x, fab_w = src_x + src_w + 0.15, 3.7
    br_x, br_w = fab_x + fab_w + 0.25, 1.3
    aml_x = br_x + br_w + 0.25
    aml_w = f.r - aml_x

    _sources(s, src_x, y0, src_w, main_h, ra)

    # 2 Fabric
    _container(s, fab_x, y0, fab_w, main_h, TEAL, TEAL_SOFT, "container: Microsoft Fabric")
    _head(s, fab_x, y0, fab_w, "Microsoft Fabric", TEAL, 2, icon="microsoft-fabric")
    lc_x, lc_w = fab_x + 0.12, 1.45
    rc_x = lc_x + lc_w + 0.2
    rc_w = fab_x + fab_w - 0.12 - rc_x
    _pnode(s, lc_x, ra, lc_w, node_h, "Pipelines + notebooks", "ingest and transform", color=TEAL)
    _pnode(s, lc_x, rb, lc_w, node_h, "Power BI", "notebooks, data agent", color=TEAL, icon="power-bi")
    _pnode(s, rc_x, ra, rc_w, rb + node_h - ra, "OneLake lakehouse", color=TEAL, icon="lakehouse")
    for i, t in enumerate(("bronze, silver, gold", "ML feature table", "scores (files or Delta)")):
        _chip(s, rc_x + 0.06, ra + 0.7 + i * 0.5, rc_w - 0.12, 0.36, t, TEAL)
    arrow(s, src_x + src_w, cy_a, lc_x, cy_a, color="muted", w=1.75)
    arrow(s, lc_x + lc_w, cy_a, rc_x, cy_a, color=TEAL, w=1.75)
    arrow(s, rc_x, cy_b, lc_x + lc_w, cy_b, color=TEAL, w=1.75)

    # 3 and 5 Bridge
    _pnode(s, br_x, ra, br_w, node_h, "OneLake /Files", "ABFSS path, GA today", color="muted", tone="node")
    _pnode(s, br_x, rb, br_w, node_h, "Scores back", "files or Delta table", color="muted", tone="node")
    _step(s, br_x + br_w - 0.14, ra - 0.1, 3)
    _step(s, br_x + br_w - 0.14, rb - 0.1, 5)
    _caption(s, br_x - 0.05, rb + node_h + 0.06, br_w + 0.1, "/Tables: copy first", color="amber", align="c")

    # 4 Azure ML
    _container(s, aml_x, y0, aml_w, main_h, BLUE, BLUE_SOFT, "container: Azure Machine Learning")
    _head(s, aml_x, y0, aml_w, "Azure Machine Learning", BLUE, 4, icon="azure-machine-learning")
    g = 0.25
    c1, c2 = 1.55, 1.7
    c3 = aml_w - 0.24 - 2 * g - c1 - c2
    x1 = aml_x + 0.12
    x2 = x1 + c1 + g
    x3 = x2 + c2 + g
    _pnode(s, x1, ra, c1, node_h, "Data asset", "OneLake files", color=BLUE)
    _pnode(s, x2, ra, c2, node_h, "Training pipeline", "prepare, train, evaluate, register", color=BLUE)
    _pnode(s, x3, ra, c3, node_h, "Model monitoring", "drift and quality", color=BLUE)
    _pnode(s, x1, rb, c1, node_h, "Batch endpoint", "scheduled scoring", color=BLUE)
    _pnode(s, x2, rb, c2, node_h, "Model registry", "MLflow runs and versions", color=BLUE)
    _pnode(s, x3, rb, c3, node_h, "Online endpoint", "blue/green rollout", color=BLUE)
    arrow(s, x1 + c1, cy_a, x2, cy_a, color=BLUE, w=1.75)
    arrow(s, x2 + c2 / 2, ra + node_h, x2 + c2 / 2, rb, color=BLUE, w=1.75)
    arrow(s, x2, cy_b, x1 + c1, cy_b, color=BLUE, w=1.75)
    arrow(s, x2 + c2, cy_b, x3, cy_b, color=BLUE, w=1.75)
    arrow(s, x3 + c3 / 2, rb, x3 + c3 / 2, ra + node_h, color=BLUE, w=1.75)

    # bridge arrows: lakehouse to Azure ML (3) and scores back (5)
    arrow(s, rc_x + rc_w, cy_a, br_x, cy_a, color="azure", w=2)
    arrow(s, br_x + br_w, cy_a, x1, cy_a, color="azure", w=2)
    arrow(s, x1, cy_b, br_x + br_w, cy_b, color="azure", w=2)
    arrow(s, br_x, cy_b, rc_x + rc_w, cy_b, color="azure", w=2)

    # 6 Delivery lane
    box(s, f.x, lane_y, f.w, lane_h, tone="node", radius=0.14, name="lane: delivery")
    _head(s, f.x, lane_y, 1.9, "Delivery", "ink", 6)
    text(s, f.x + 0.12, lane_y + 0.48, 1.75, 0.5, ["One path for both platforms"], size=12, color="muted",
         name="lane caption")
    ny, nh = lane_y + 0.08, lane_h - 0.16
    cy_l = ny + nh / 2
    n1x, n1w = f.x + 1.95, 2.1
    n2x, n2w = n1x + n1w + 0.28, 2.85
    n3x, n3w = n2x + n2w + 0.28, 2.05
    n4x = n3x + n3w + 0.2
    n4w = f.r - 0.12 - n4x
    _pnode(s, n1x, ny, n1w, nh, "Git repo", "GitHub, GitLab or Azure DevOps", icon="git-branch")
    _pnode(s, n2x, ny, n2w, nh, "CI/CD pipeline", "GitHub Actions, GitLab CI or Azure Pipelines", icon="workflow")
    _pnode(s, n3x, ny, n3w, nh, "Environments", "dev \u2192 test \u2192 prod with approvals", icon="layers")
    card(s, n4x, ny, n4w, nh, body=["- Key Vault: secrets", "- OIDC: no stored keys", "- Azure Monitor: telemetry"],
         tone="paper", body_size=12, pad=0.1, after=0, body_color="ink", line_w=1.25, radius=0.1,
         name="node: guardrails")
    arrow(s, n1x + n1w, cy_l, n2x, cy_l, color="muted", w=1.75)
    arrow(s, n2x + n2w, cy_l, n3x, cy_l, color="muted", w=1.75)

    # deploy arrows from the lane into each platform
    fx = fab_x + 0.55
    ax = aml_x + 0.8
    arrow(s, fx, lane_y, fx, mb, color="azure", w=2)
    _caption(s, fx + 0.12, mb + 0.06, 2.6, "Git sync, pipelines, fabric-cicd", color="ink")
    arrow(s, ax, lane_y, ax, mb, color="azure", w=2)
    _caption(s, ax + 0.12, mb + 0.06, 2.6, "az ml CLI and SDK, registry", color="ink")


# ---------------------------------------------------------------- P3.32 Architecture B
def _arch_b(f) -> None:
    s = f.s
    y0 = f.y
    head_h, node_h, gap, pad_b = 0.46, 1.0, 0.2, 0.08
    ra = y0 + head_h
    rb = ra + node_h + gap
    mb = rb + node_h + pad_b
    main_h = mb - y0
    lane_y = mb + 0.28
    lane_h = f.b - lane_y
    if lane_h < 1.4:
        LINT.append(f"[{CTX['slide']}] lanes are only {lane_h:.2f} in high")
    cy_a, cy_b = ra + node_h / 2, rb + node_h / 2

    src_x, src_w = f.x, 1.3
    gp_w = 3.3
    gp_x = f.r - gp_w
    fab_x = src_x + src_w + 0.15
    fab_w = gp_x - 0.2 - fab_x

    _sources(s, src_x, y0, src_w, main_h, ra)

    # 2 Everything in one Fabric container
    _container(s, fab_x, y0, fab_w, main_h, TEAL, TEAL_SOFT, "container: Microsoft Fabric")
    _head(s, fab_x, y0, fab_w, "Microsoft Fabric", TEAL, 2, icon="microsoft-fabric")
    g = 0.28
    cw = (fab_w - 0.24 - 3 * g) / 4
    cx = [fab_x + 0.12 + i * (cw + g) for i in range(4)]
    _pnode(s, cx[0], ra, cw, node_h, "OneLake lakehouse", "medallion tables", color=TEAL, icon="lakehouse")
    _pnode(s, cx[1], ra, cw, node_h, "Notebooks", "features, Spark training", color=TEAL)
    _pnode(s, cx[2], ra, cw, node_h, "Experiment + model", "MLflow, versions", color=TEAL)
    _pnode(s, cx[0], rb, cw, node_h, "Power BI", "reports on scores", color=TEAL, icon="power-bi")
    _pnode(s, cx[1], rb, cw, node_h, "Scores table", "Delta table in OneLake", color=TEAL)
    _pnode(s, cx[2], rb, cw, node_h, "Batch scoring", "PREDICT in a notebook", color=TEAL)
    eh = rb + node_h - ra
    ep = card(s, cx[3], ra, cw, eh, title="Model endpoint", body=["real-time scoring", "4 model flavors", "sleeps when idle"],
              tone="amber", title_size=13, body_size=12, pad=0.1, after=3, body_color="ink", line_w=1.25, radius=0.1,
              name="node: model endpoint")
    pill(s, cx[3] + 0.1, ra + eh - 0.42, "preview", tone="amber", size=12, h=0.28, w=1.0)
    arrow(s, src_x + src_w, cy_a, cx[0], cy_a, color="muted", w=1.75)
    for i in range(3):
        arrow(s, cx[i] + cw, cy_a, cx[i + 1], cy_a, color=TEAL, w=1.75)
    arrow(s, cx[2] + cw / 2, ra + node_h, cx[2] + cw / 2, rb, color=TEAL, w=1.75)
    arrow(s, cx[2], cy_b, cx[1] + cw, cy_b, color=TEAL, w=1.75)
    arrow(s, cx[1], cy_b, cx[0] + cw, cy_b, color=TEAL, w=1.75)
    del ep

    # gaps panel
    box(s, gp_x, y0, gp_w, main_h, tone="amber", radius=0.14, line_w=1.5, name="panel: gaps")
    add_icon(s, "alert-triangle", gp_x + 0.12, y0 + 0.07, 0.36, color="amber")
    text(s, gp_x + 0.56, y0 + 0.1, gp_w - 0.64, 0.3, ["Gaps to plan for"], size=14, bold=True, font=HEAD, color="amber",
         anchor="m", wrap=False, lint=False, name="head: gaps")
    gaps = (
        "**Drift:** no managed monitoring for classical ML",
        "**Serving:** endpoint is preview, no traffic split documented",
        "**Registry:** versions and tags, no stages documented",
        "**Promotion:** items sync as metadata, not model versions",
    )
    text(s, gp_x + 0.16, y0 + 0.5, gp_w - 0.3, main_h - 0.54,
         [dict(text=t, bullet=True, bullet_color="amber", after=4) for t in gaps], size=14, name="gaps list")

    # 6 Delivery and 7 Monitoring lanes
    d_w = 6.9
    m_x = f.x + d_w + 0.2
    m_w = f.r - m_x
    ny, nh = lane_y + 0.42, lane_h - 0.48
    cy_l = ny + nh / 2
    box(s, f.x, lane_y, d_w, lane_h, tone="node", radius=0.14, name="lane: delivery")
    _head(s, f.x, lane_y, d_w, "Delivery", "ink", 6)
    dn_w = (d_w - 0.2 - 3 * 0.22) / 4
    dx = [f.x + 0.1 + i * (dn_w + 0.22) for i in range(4)]
    for x_, t_, sub_ in zip(dx, ("Git integration", "Deployment pipelines", "fabric-cicd", "Variable library"),
                            ("workspace to repo", "dev, test, prod", "scripted deploys", "values per stage")):
        _pnode(s, x_, ny, dn_w, nh, t_, sub_)
    arrow(s, dx[0] + dn_w, cy_l, dx[1], cy_l, color="muted", w=1.75)
    box(s, m_x, lane_y, m_w, lane_h, tone="node", radius=0.14, name="lane: monitoring")
    _head(s, m_x, lane_y, m_w, "Monitoring: you build it", "ink", 7)
    mn_w = (m_w - 0.2 - 2 * 0.22) / 3
    mx = [m_x + 0.1 + i * (mn_w + 0.22) for i in range(3)]
    for x_, t_, sub_ in zip(mx, ("Scheduled notebook", "Metrics table", "Power BI + Activator"),
                            ("drift, metrics", "Delta, per run", "report and alerts")):
        _pnode(s, x_, ny, mn_w, nh, t_, sub_)
    arrow(s, mx[0] + mn_w, cy_l, mx[1], cy_l, color="muted", w=1.75)
    arrow(s, mx[1] + mn_w, cy_l, mx[2], cy_l, color="muted", w=1.75)

    # lane arrows into the container
    fx = fab_x + 0.55
    arrow(s, fx, lane_y, fx, mb, color="azure", w=2)
    _caption(s, fx + 0.12, mb + 0.03, 2.6, "Git sync, pipelines, fabric-cicd", color="ink")
    mxa = m_x + 0.8
    arrow(s, mxa, lane_y, mxa, mb, color="azure", w=2, head=True)
    _caption(s, mxa + 0.12, mb + 0.03, 2.8, "reads scores, writes metrics", color="ink")


# ---------------------------------------------------------------- P3.33 / P3.34 pillar tables
PILL_TONE = {"Native": "success", "Preview": "amber", "Build it": "muted"}
CELL_TONE = {"Native": "paper", "Preview": "amber", "Build it": "node"}
PILL_W = 1.06

# (pillar, lucide icon, (Azure ML status, how), (Fabric status, how))
ROWS_BUILD = [
    ("Git integration / CI", "git-branch",
     ("Native", "Code in Git; GitHub Actions run jobs with the az ml CLI"),
     ("Native", "Git sync with GitHub or Azure DevOps; deploy with fabric-cicd")),
    ("Environment", "layers",
     ("Native", "Curated or custom environments, Docker plus conda, versioned"),
     ("Native", "Environment item: libraries and Spark settings for notebooks")),
    ("Experiment tracking", "flask-conical",
     ("Native", "Managed MLflow tracking; jobs log without setup"),
     ("Native", "MLflow preconfigured; autologging on in notebooks")),
    ("Model comparison", "git-compare",
     ("Native", "Compare runs in studio or MLflow; hyperparameter sweeps"),
     ("Native", "Compare runs in the Experiment item or with search_runs")),
    ("Model promotion", "badge-check",
     ("Native", "Versions, tags, shared registries; add an approval gate"),
     ("Build it", "Retrain or re-register in each workspace; item sync is preview")),
    ("Lineage / artifact store", "network",
     ("Native", "Jobs record code, data and environment; artifacts per run"),
     ("Native", "Artifacts stay with the run; workspace lineage view")),
    ("Infrastructure as code and secrets", "key-round",
     ("Native", "Bicep or Terraform; Key Vault and managed identity"),
     ("Build it", "Variable library, fabric-cicd or Fabric CLI; Key Vault via NotebookUtils")),
]

ROWS_RUN = [
    ("Batch scoring", "table",
     ("Native", "Batch endpoint; MLflow models deploy without scoring code"),
     ("Native", "PREDICT or MLFlowTransformer in a scheduled notebook")),
    ("Real-time endpoint", "zap",
     ("Native", "Managed online endpoint: autoscale, key or Entra auth, logs"),
     ("Preview", "ML model endpoint: four model flavors, sleeps when idle")),
    ("Continuous training (CT)", "repeat",
     ("Native", "Schedule or Event Grid trigger starts a pipeline job"),
     ("Build it", "Scheduled pipeline retrains; you add the promotion gate")),
    ("Data drift", "bar-chart-3",
     ("Native", "Model monitoring: data drift and data quality signals"),
     ("Build it", "Scheduled notebook computes PSI into a drift table")),
    ("Model drift", "trending-down",
     ("Native", "Prediction drift, plus performance with ground truth"),
     ("Build it", "Scheduled notebook writes metrics to a table; Power BI shows trends")),
    ("A/B testing / canary", "split",
     ("Native", "Blue/green deployments: traffic split and mirrored traffic"),
     ("Build it", "No traffic split documented; split in your own app")),
    ("Alerting and automation", "bell",
     ("Native", "Monitoring alerts, Event Grid events, schedules"),
     ("Native", "Activator rules run pipelines, notebooks, Teams or email")),
]


def _status_cell(s, x, y, w, h, status, how) -> None:
    box(s, x, y, w, h, tone=CELL_TONE[status], radius=0.1, line_w=1.0, name=f"cell: {how[:30]}")
    pill(s, x + 0.1, y + (h - 0.28) / 2, status, tone=PILL_TONE[status], size=12, h=0.28, w=PILL_W)
    tx = x + 0.2 + PILL_W
    text(s, tx, y, w - (tx - x) - 0.08, h, [how], size=13, anchor="m", name=f"how: {how[:30]}")


def _pillar_grid(rows):
    """Pillar | Azure ML | Fabric grid: a status pill and a short 'how' in every platform cell."""
    def draw(f) -> None:
        s = f.s
        hdr_h, hgap, rgap, pw, cgap = 0.42, 0.06, 0.05, 2.7, 0.08
        row_h = (f.b - f.y - hdr_h - hgap - (len(rows) - 1) * rgap) / len(rows)
        cw = (f.w - pw - 2 * cgap) / 2
        ax = f.x + pw + cgap
        fx = ax + cw + cgap
        box(s, f.x, f.y, pw, hdr_h, tone="node", radius=0.1, name="header: pillar")
        text(s, f.x + 0.14, f.y, pw - 0.2, hdr_h, ["Pillar"], size=14, bold=True, font=HEAD, color="muted", anchor="m",
             wrap=False, lint=False, name="head: pillar")
        for x, nm, icon, col, soft in ((ax, "Azure Machine Learning", "azure-machine-learning", BLUE, BLUE_SOFT),
                                       (fx, "Microsoft Fabric", "microsoft-fabric", TEAL, TEAL_SOFT)):
            _container(s, x, f.y, cw, hdr_h, col, soft, f"header: {nm}")
            add_icon(s, icon, x + 0.14, f.y + (hdr_h - 0.3) / 2, 0.3)
            text(s, x + 0.54, f.y, cw - 0.6, hdr_h, [nm], size=14, bold=True, font=HEAD, color=col, anchor="m",
                 wrap=False, lint=False, name=f"head: {nm}")
        y = f.y + hdr_h + hgap
        for pillar, icon, aml, fab in rows:
            box(s, f.x, y, pw, row_h, tone="node", radius=0.1, name=f"pillar: {pillar}")
            add_icon(s, icon, f.x + 0.12, y + (row_h - 0.32) / 2, 0.32, color="ink")
            text(s, f.x + 0.54, y, pw - 0.6, row_h, [pillar], size=13, bold=True, font=HEAD, anchor="m",
                 name=f"pillar label: {pillar}")
            _status_cell(s, ax, y, cw, row_h, *aml)
            _status_cell(s, fx, y, cw, row_h, *fab)
            y += row_h + rgap
    return draw


def build(d: Deck) -> None:
    d.custom(
        "P3.31", "Architecture A: Fabric for data, Azure ML for the models", _arch_a,
        notes="""Fabric owns the data and its consumers; Azure ML owns training, registry and serving. One: telematics, work orders and asset data land through Fabric pipelines. Two: notebooks build bronze, silver, gold and the ML feature table in the OneLake lakehouse. Three: Azure ML reads those files through an ABFSS path, the documented, generally available route. Four: a pipeline job prepares, trains, evaluates and registers the model with MLflow; serve it from a managed online endpoint with blue/green rollout, or score in bulk with a batch endpoint, with monitoring on top. Five: scores return to OneLake as files or a Delta table for Power BI, notebooks and the Part 4 data agent. Six: one Git repo and one CI/CD pipeline deploy both sides.

WHEN TO CHOOSE IT: your data lives in Fabric and you want managed endpoints, safe rollout and drift monitoring. The price: two platforms, plus identity and network setup.
ASK: Who already runs an Azure ML workspace next to Fabric?
WATCH OUT: Fabric Git integration supports Azure DevOps and GitHub, not GitLab. With GitLab, deploy from the CI runner: fabric-cicd for Fabric, az ml for Azure ML.
IF SHORT ON TIME: read the takeaway, skip the delivery lane.
SOURCE: """ + URL_BRIDGE + "\n" + URL_FABRIC_GIT + "\n" + URL_AML_GH + """
VERIFY: Git providers re-checked 2026-10-22 (Azure DevOps, GitHub, GitHub Enterprise; no GitLab). OneLakeDatastore is experimental, so only ABFSS is shown. fabric-cicd support for ML items: not confirmed.
TRANSITION: Now the same flow entirely inside Fabric, and the gaps you accept.""",
        minutes=4, core=False, eyebrow=EYEBROW,
        takeaway="Fabric owns the data and the consumers; Azure ML owns training, registry and serving; Git and CI/CD tie both.",
        source=ARCH_A_SRC,
    )
    d.custom(
        "P3.32", "Architecture B: everything in Fabric, with known gaps", _arch_b,
        notes="""Same flow, one platform: one identity, one copy of the data, no bridge. Walk it left to right. One: the same three sources. Two: the lakehouse feeds notebooks, notebooks train and log to an Experiment item with MLflow, and PREDICT in a notebook scores into a Scores table that Power BI reads. Real-time serving is the Fabric ML model endpoint: preview, four model flavors, and it sleeps when idle. Six: delivery uses Git integration, deployment pipelines, fabric-cicd and a variable library. Seven: monitoring is something you build: a scheduled notebook writes drift metrics to a table, and Power BI and Activator report and alert.

Now read the amber panel aloud. These four gaps come back as rows in the next two tables. Decision rule: if three or more of them would hurt your first release, choose Architecture A.
ASK: Which of these four gaps would block your first release?
WATCH OUT: ML items in Git and deployment pipelines are preview and carry metadata, not versions or run history. Promote by retraining or re-registering in the target workspace.
IF SHORT ON TIME: skip the two lower lanes, read the amber panel and the decision rule.
SOURCE: """ + URL_FABRIC_ML + "\n" + URL_FABRIC_ENDPOINTS + "\n" + URL_FABRIC_ML_CICD + """
VERIFY: Endpoint preview, auto-sleep and the four flavors (Keras, LightGBM, scikit-learn, XGBoost) re-checked 2026-10-22; no traffic split documented. The model page documents versions and tags only. fabric-cicd coverage of ML model items: not confirmed.
TRANSITION: Next, the same comparison as two tables, pillar by pillar.""",
        minutes=4, core=False, eyebrow=EYEBROW,
        takeaway="One platform is the shortest path from data to score; plan for gaps in serving, drift monitoring and promotion.",
        source=ARCH_B_SRC,
    )
    d.custom(
        "P3.33", "Pillars 1 of 2: build and release", _pillar_grid(ROWS_BUILD),
        notes="""How to read this table: each row is one MLOps pillar, in the order you meet them from first commit to release. Azure ML on the left, Fabric on the right. The chip says how you get it. Native means built in and documented. Preview means Microsoft labels it preview. Build it means no managed feature: you assemble it from notebooks, pipelines and scripts.

Read down the rows. Git, environments, experiment tracking and run comparison are native on both platforms. The difference is promotion. Azure ML gives you versions, tags and registries you can share across workspaces, and your CI pipeline adds the approval. In Fabric you retrain or re-register the model in each workspace, because ML items move through deployment pipelines as preview metadata only.
ASK: Which of these rows is your biggest gap today?
WATCH OUT: do not promise model stages or aliases in Fabric, they are not documented.
IF SHORT ON TIME: read only the promotion row and the question.
IF ASKED: security and governance and cost control exist on both platforms; we cut those rows for room.
SOURCE: """ + URL_FABRIC_ML_CICD + "\n" + URL_AML_REG + "\n" + URL_FABRIC_GIT + """
VERIFY (checked 2026-10-22): Fabric lineage view coverage of ML items and the exact Azure ML lineage wording: not confirmed. Key Vault from Fabric notebooks via NotebookUtils: confirm the call before showing code. fabric-cicd support for ML items: not confirmed. Azure ML model aliases: not claimed.
TRANSITION: Same table for the run-and-improve pillars.""",
        minutes=4, core=False, eyebrow=EYEBROW,
        takeaway="The build-and-release pillars are largely native on both sides; the difference is where promotion works.",
        source=PILLARS_1_SRC,
    )
    d.custom(
        "P3.34", "Pillars 2 of 2: run and improve", _pillar_grid(ROWS_RUN),
        notes="""Same chips: Native, Preview, Build it. This table is about what happens after the model exists. Start with the top two rows. Batch scoring is native on both sides: a batch endpoint in Azure ML, PREDICT in a scheduled notebook in Fabric. Real-time serving is native in Azure ML and preview in Fabric, where the endpoint supports four model flavors and sleeps when idle.

Now the four rows we zoom into next: continuous training, data drift, model drift and A/B testing. Azure ML has a managed answer for each: schedules and Event Grid triggers, monitoring signals, traffic split with mirroring. In Fabric you build them: a scheduled pipeline, a notebook that writes drift metrics to a table, Power BI on top, and your own routing for A/B tests. That is not a criticism, it is what the demo does.
ASK: Which of these rows is your biggest gap today?
WATCH OUT: Fabric has no first-party managed drift monitoring for classical ML, so never say that Fabric monitors drift for you.
IF SHORT ON TIME: read the Fabric column only, from the bottom up.
SOURCE: """ + URL_AML_MON + "\n" + URL_AML_ROLLOUT + "\n" + URL_FABRIC_PREDICT + """
VERIFY (checked 2026-10-22): Azure ML mirrored traffic is documented without a preview label. Fabric endpoint is preview, and no traffic split is documented. Azure ML alert wiring through Event Grid and the exact monitoring signal names: check in studio before the session.
TRANSITION: Four of these rows deserve a closer look, starting with continuous training.""",
        minutes=4, core=False, eyebrow=EYEBROW,
        takeaway="The run-and-improve pillars are where Azure ML is deeper and where Fabric asks you to assemble parts.",
        source=PILLARS_2_SRC,
    )
