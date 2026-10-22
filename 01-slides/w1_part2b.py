"""Workshop 1, part 2b: monitoring, data validation, responsible AI and the complete CI/CT/CD flow (P2.31 to P2.36)."""
from __future__ import annotations

from deck_core import (BODY, HEAD, MONO, add_icon, arrow, box, card, fill_text, label, lint_fit, num_badge, pill,
                       polyline, text, text_w)
from deck_lib import Deck
from facts import F, d2, n, pct
from pptx.enum.shapes import MSO_SHAPE

TEAL, TEAL_SOFT = "0F7B6C", "E6F4F1"   # Fabric
BLUE, BLUE_SOFT = "005A9E", "E8F1FA"   # Azure ML

# Real bins for the P2.31 chart, computed on 2026-10-22 with the reference pipeline (fleet_reference_pipeline:
# silver telemetry, RUN readings, Excavator engine_temp_c). Reference = September 2026, new batch = 2026-10-01 to
# 2026-10-14. By construction each September decile holds 10 % of the readings; EXC_NEW is the share of the new
# batch in each of those deciles. The PSI of these bins is 0.8804, the value in drift_report.csv.
EXC_EDGES = [85.5, 86.8, 87.8, 88.6, 89.4, 90.2, 91.1, 92.1, 93.7]
EXC_NEW = [0.0101, 0.0211, 0.0258, 0.0461, 0.0515, 0.0687, 0.1023, 0.1179, 0.1944, 0.3622]
EXC_MEAN = (89.493, 92.723)

# Illustrative curve for P2.32, anchored on the test PR-AUC of about 0.38 (weeks 0 to 16, never a measurement).
STALE = [.380, .382, .379, .381, .380, .378, .365, .352, .340, .328, .316, .305, .294, .284, .274, .265, .256]
RETRAINED = STALE[:11] + [.375, .373, .371, .369, .367, .365]


# ------------------------------------------------------------------ helpers
def _psi(cls: str, sensor: str) -> float:
    for r in F.drift_major + F.drift_moderate:
        if r["equipment_class"] == cls and r["sensor"] == sensor:
            return r["psi"]
    raise KeyError((cls, sensor))


def chip(s, x, y, w, h, txt, tone="paper", size=14, bold=False, color="ink", align="c", font=BODY, line_color=None,
         fill_color=None, shape=MSO_SHAPE.ROUNDED_RECTANGLE, dash=False, name=None):
    shp = box(s, x, y, w, h, tone=tone, radius=min(0.12, h / 2), line_color=line_color, fill_color=fill_color,
              shape=shape, dash=dash, name=name or f"chip: {txt}")
    fill_text(shp.text_frame, [txt], size=size, color=color, font=font, bold=bold, align=align, anchor="m",
              margins=(0.08, 0.02, 0.08, 0.02))
    lint_fit(shp.name, [txt], w - 0.16, h - 0.04, size=size, font=font, bold=bold)
    return shp


def chip_flow(s, x, y, w, items, size=14, h=0.32, gap=0.08, tone="paper", pad=0.26):
    """Chips wrapped into rows inside width w; returns the bottom edge of the last row."""
    cx, cy = x, y
    for it in items:
        cw = text_w(it, BODY, size) + pad
        if cx > x and cx + cw > x + w + 1e-6:
            cx, cy = x, cy + h + gap
        chip(s, cx, cy, cw, h, it, tone=tone, size=size)
        cx += cw + gap
    return cy + h


def rule(s, x1, y1, x2, y2, color="line", w=0.75, dash=False, name="rule"):
    return arrow(s, x1, y1, x2, y2, color=color, w=w, dash=dash, tail=False, name=name)


# ------------------------------------------------------------------ P2.31 data drift
def _draw_data_drift(f):
    s = f.s
    top_h, gap, lw = 3.43, 0.12, 4.55
    ch = (top_h - 2 * gap) / 3
    for i, (t, b, ic, tone) in enumerate((
        ("Issue", "Production predictions can quietly go wrong.", "alert-triangle", "amber"),
        ("Cause", "The data pattern changed and the training pipeline was not adapted.", "search", "azure"),
        ("Solution", "Trigger an alert, then the training pipeline.", "refresh-cw", "success"),
    )):
        card(s, f.x, f.y + i * (ch + gap), lw, ch, t, [b], icon=ic, tone=tone, title_size=15, body_size=14, pad=0.14,
             after=2, name=f"card: {t}")

    px, pw = f.x + lw + 0.2, f.w - lw - 0.2
    box(s, px, f.y, pw, top_h, tone="paper", radius=0.12, name="chart panel")
    text(s, px + 0.18, f.y + 0.1, 3.6, 0.5, [
        dict(text="Excavator engine temperature", size=14, bold=True, font=HEAD),
        dict(text="Oct 1 to 14 vs the September reference", size=12, color="muted"),
    ], name="chart title")
    c1 = f"PSI {d2(_psi('Excavator', 'engine_temp_c'))}"
    c2 = f"mean {EXC_MEAN[0]:.1f} → {EXC_MEAN[1]:.1f} °C"
    w1, w2 = text_w(c1, BODY, 14, True) + 0.3, text_w(c2, BODY, 14) + 0.3
    xr = px + pw - 0.15
    chip(s, xr - w2, f.y + 0.14, w2, 0.34, c2, tone="amber", size=14, name="chip mean")
    chip(s, xr - w2 - 0.1 - w1, f.y + 0.14, w1, 0.34, c1, tone="amber_solid", size=14, bold=True, color="white",
         name="chip psi")

    gx0, gx1 = px + 0.62, px + pw - 0.2
    gy1 = f.y + 2.72
    sc = 2.0 / 40
    slot, bw = (gx1 - gx0) / 10, 0.46
    for v in (10, 20, 30):
        rule(s, gx0, gy1 - v * sc, gx1, gy1 - v * sc, name=f"grid {v}")
    for v in (0, 10, 20, 30):
        label(s, px + 0.05, gy1 - v * sc - 0.11, 0.5, f"{v} %", size=12, align="r", mono=False, name=f"y tick {v}")
    rule(s, gx0, gy1, gx1, gy1, color="sand", w=1.0, name="baseline")
    for i, v in enumerate(EXC_NEW):
        bx, bh = gx0 + i * slot + (slot - bw) / 2, v * 100 * sc
        box(s, bx, gy1 - bh, bw, bh, shape=MSO_SHAPE.RECTANGLE, fill_color="amber", line_color="amber",
            name=f"bar D{i + 1}")
    rule(s, gx0, gy1 - 10 * sc, gx1, gy1 - 10 * sc, color="azure", w=1.75, dash=True, name="reference 10 %")
    for i, v in enumerate(EXC_NEW):
        bx, bh = gx0 + i * slot + (slot - bw) / 2, v * 100 * sc
        label(s, bx - 0.1, gy1 - bh - 0.24, bw + 0.2, f"{round(v * 100)} %", size=12, color="amber" if i == 9 else "ink",
              bold=i == 9, mono=False, fill="paper", name=f"value D{i + 1}")
    for i, e in enumerate(EXC_EDGES):
        label(s, gx0 + (i + 1) * slot - 0.31, gy1 + 0.04, 0.62, f"{e:.1f}", size=12, mono=False, name=f"edge {e}")
    label(s, gx0, gy1 + 0.29, gx1 - gx0, "engine temperature in °C, at the edges of the September deciles", size=12,
          mono=False, name="x caption")
    lx, ly = gx0 + 0.15, f.y + 0.72
    box(s, lx, ly + 0.04, 0.16, 0.16, shape=MSO_SHAPE.RECTANGLE, fill_color="amber", line_color="amber",
        name="legend swatch new")
    text(s, lx + 0.28, ly, 4.3, 0.24, ["Oct 1 to 14: share of readings per September decile"], size=12, anchor="m",
         name="legend new")
    rule(s, lx - 0.02, ly + 0.4, lx + 0.2, ly + 0.4, color="azure", w=1.75, dash=True, name="legend swatch ref")
    text(s, lx + 0.28, ly + 0.28, 4.3, 0.24, ["September: 10 % in every decile, by construction"], size=12,
         anchor="m", name="legend ref")

    sy = f.y + top_h + gap
    sh = f.b - sy
    box(s, f.x, sy, f.w, sh, tone="node", radius=0.12, name="detection strip")
    text(s, f.x + 0.2, sy + 0.09, 4.9, sh - 0.12, [
        dict(text="How it is detected", size=14, bold=True, font=HEAD, after=1),
        dict(text="Each feature vs its training baseline, on a schedule", size=14, after=1),
        dict(text="PSI · KS test · Jensen-Shannon · Wasserstein", size=12, font=MONO, color="muted"),
    ], name="detection text")
    rule(s, f.x + 5.25, sy + 0.14, f.x + 5.25, sy + sh - 0.14, color="node_line", w=1.0, name="divider")
    gx = f.x + 5.5
    text(s, gx, sy + 0.08, 2.6, 0.22, ["PSI thresholds, rule of thumb"], size=12, color="muted", name="gauge title")
    sx = gx
    x3 = gx
    for lab, fill, line, col in (("stable < 0.10", "success_soft", "success_line", "success"),
                                 ("moderate 0.10 to 0.25", "amber_soft", "amber_line", "amber"),
                                 ("major > 0.25", "amber", "amber", "white")):
        w = text_w(lab, BODY, 12, True) * 1.03 + 0.2
        chip(s, sx, sy + 0.45, w, 0.32, lab, size=12, bold=True, color=col, fill_color=fill, line_color=line,
             shape=MSO_SHAPE.RECTANGLE, name=f"gauge {lab}")
        x3, sx = sx + w / 2, sx + w
    tri = box(s, x3 - 0.09, sy + 0.34, 0.18, 0.1, shape=MSO_SHAPE.ISOSCELES_TRIANGLE, fill_color="amber",
              line_color="amber", name="gauge marker")
    tri.rotation = 180
    label(s, x3 - 0.9, sy + 0.08, 1.8, f"this feature: {c1[4:]}", size=12, color="amber", bold=True, mono=False,
          name="gauge value")
    arrow(s, sx + 0.12, sy + sh / 2, sx + 0.47, sy + sh / 2, color="muted", w=1.5, name="alert arrow")
    chip(s, sx + 0.52, sy + 0.15, 1.55, sh - 0.3, "Alert, then retrain", tone="success", size=14, bold=True,
         color="success", name="chip alert")


def _notes_data_drift() -> str:
    top = round(EXC_NEW[-1] * 100)
    return f"""A model only sees columns. When the columns change, predictions can go quietly wrong long before anyone has a label to prove it. That is data drift. Read the left column as a story: silent degradation, a data pattern the training pipeline never saw, and an alert that starts the training pipeline.

The chart is real, computed with our own pipeline. By construction each September decile holds 10 percent of the excavator engine temperature readings. In the first two weeks of October, {top} percent land in the hottest decile. The mean moved from {EXC_MEAN[0]:.1f} to {EXC_MEAN[1]:.1f} degrees C and the PSI is {d2(_psi('Excavator', 'engine_temp_c'))}, far above the 0.25 rule of thumb. Of the {F.drift_combinations} class and sensor combinations, {len(F.drift_major)} are major, {len(F.drift_moderate)} are moderate (seasonal, expected) and {F.drift_stable} are stable. The injected cause is a calibration change on excavators and wheel loaders. Excavator vibration is even stronger, PSI {d2(_psi('Excavator', 'vibration_mm_s'))}.

ASK: Which of your inputs could change without anyone telling the data science team?
WATCH OUT: the 0.10 and 0.25 thresholds are a rule of thumb, not a standard. Tune them per feature.
IF SHORT ON TIME: show the chart and the PSI bar, skip the left column.
SOURCE: https://learn.microsoft.com/en-us/azure/machine-learning/concept-model-monitoring?view=azureml-api-2 (data drift metrics)
VERIFY: Fabric has no managed drift monitor for classical ML in the docs reviewed, so say "build it with scheduled notebooks".
TRANSITION: Drift in the inputs is the early warning. Next, what the business actually feels: model drift."""


# ------------------------------------------------------------------ P2.32 model drift
def _draw_model_drift(f):
    s = f.s
    lw = 7.7
    box(s, f.x, f.y, lw, f.h, tone="paper", radius=0.12, name="chart panel")
    text(s, f.x + 0.2, f.y + 0.12, 5.2, 0.3, [dict(text="Weekly PR-AUC of the production model", size=14, bold=True,
                                                    font=HEAD)], name="chart title")
    pill(s, f.x + lw - 0.18, f.y + 0.12, "illustrative", tone="amber", size=12, h=0.3, caps=False, mono=False,
         right=True, name="pill illustrative")

    gx0, gx1 = f.x + 0.3, f.x + lw - 0.25
    gy0, gy1 = f.y + 0.8, f.y + 3.7
    span, wk = gy1 - gy0, 16

    def X(w):
        return gx0 + w / wk * (gx1 - gx0)

    def Y(v):
        return gy1 - (v - 0.20) / 0.22 * span

    # legend row
    lx, ly = gx0 + 0.05, f.y + 0.46
    rule(s, lx, ly + 0.11, lx + 0.34, ly + 0.11, color="muted", w=2.25, dash=True, name="legend stale")
    t1, t2 = "never updated", "retrained when alerted"
    text(s, lx + 0.42, ly, 1.5, 0.22, [t1], size=12, anchor="m", name="legend stale text")
    lx2 = lx + 0.42 + text_w(t1, BODY, 12) + 0.35
    rule(s, lx2, ly + 0.11, lx2 + 0.34, ly + 0.11, color="azure", w=3.0, name="legend retrained")
    text(s, lx2 + 0.42, ly, 2.2, 0.22, [t2], size=12, anchor="m", name="legend retrained text")
    lx3 = lx2 + 0.42 + text_w(t2, BODY, 12) + 0.35
    box(s, lx3, ly + 0.02, 0.18, 0.18, shape=MSO_SHAPE.OVAL, fill_color="amber", line_color="amber", name="legend alert")
    text(s, lx3 + 0.26, ly, 0.8, 0.22, ["alert"], size=12, anchor="m", name="legend alert text")

    rule(s, gx0, gy1, gx1, gy1, color="sand", w=1.0, name="baseline")
    for w in (0, 4, 8, 12, 16):
        label(s, X(w) - 0.2, gy1 + 0.04, 0.4, str(w), size=12, mono=False, name=f"week {w}")
    label(s, gx0, gy1 + 0.29, gx1 - gx0, "weeks since deployment", size=12, mono=False, name="x caption")

    rule(s, gx0, Y(0.32), gx1, Y(0.32), color="amber", w=1.5, dash=True, name="threshold")
    label(s, gx0 + 0.05, Y(0.32) + 0.05, 2.7, "retrain threshold (example)", size=12, color="amber", align="l",
          mono=False, name="threshold text")
    rule(s, X(5), gy0, X(5), Y(0.32), color="muted", w=1.0, dash=True, name="drift starts line")
    label(s, X(5) + 0.08, gy0 + 0.02, 1.2, "drift starts", size=12, align="l", mono=False, name="drift starts")
    label(s, gx0 + 0.05, Y(0.38) - 0.32, 2.1, "about 0.38 at deployment", size=12, color="ink", align="l", mono=False,
          name="deployment level")

    polyline(s, [(X(i), Y(v)) for i, v in enumerate(STALE)], color="muted", w=2.25, dash=True, tail=False,
             name="curve never updated")
    polyline(s, [(X(i), Y(v)) for i, v in enumerate(RETRAINED)], color="azure", w=3.0, tail=False,
             name="curve retrained")
    box(s, X(10) - 0.1, Y(STALE[10]) - 0.1, 0.2, 0.2, shape=MSO_SHAPE.OVAL, fill_color="amber", line_color="white",
        line_w=1.5, name="alert marker")
    label(s, X(10) - 0.85, Y(STALE[10]) + 0.1, 0.7, "alert", size=12, color="amber", bold=True, align="r", mono=False,
          name="alert text")
    text(s, X(11) + 0.2, Y(0.32) - 0.5, 1.95, 0.44, ["retrain, compare with", "the champion, promote"], size=12,
         color="azure", bold=True, anchor="b", name="retrain text")
    chip(s, gx0 + 0.1, gy1 - 0.88, 4.6, 0.68, "Labels arrive 7 days after the prediction, so a performance alert is at "
         "least a week late", tone="amber", size=14, name="label delay callout")

    rx, rw, g = f.x + lw + 0.2, f.w - lw - 0.2, 0.12
    ch = 1.3
    card(s, rx, f.y, rw, ch, "Feature drift", ["Which features matter has changed, so the learned rules fit less well."],
         icon="bar-chart-3", title_size=16, body_size=14, pad=0.16, after=2, name="card: Feature drift")
    card(s, rx, f.y + ch + g, rw, ch, "Label drift",
         [f"The target itself moves: {pct(F.positive_rate)} of labelled rows are failures, and that rate can change."],
         icon="tag", title_size=16, body_size=14, pad=0.16, after=2, name="card: Label drift")
    ay = f.y + 2 * (ch + g)
    card(s, rx, ay, rw, f.b - ay, "What you do",
         ["- Alert on drift and performance", "- Retrain on fresh data",
          "- Compare with the champion, then promote"],
         icon="refresh-cw", tone="success", title_size=16, body_size=14, pad=0.16, after=2, name="card: What you do")


NOTES_MODEL_DRIFT = """The business never asks about PSI. It feels the model getting worse. Model drift is performance decay: the model was right when you trained it, and the world moved. Two causes sit behind it. Feature drift: which features matter has changed, so the learned rules fit less well. Label drift: the target itself moves, here the share of machines that fail within seven days.

The curve is illustrative, anchored on a test PR-AUC of about 0.38. Left alone, it decays. With an alert at a threshold you choose, you retrain, compare the candidate with the champion on the agreed metrics, and promote only if it wins. The metrics land in a table, and a Power BI report on that table is the usual dashboard.

Be honest about the delay. The label is a corrective work order within seven days, and work orders are opened three to six days late. So October labels do not exist yet: today we can only watch input and prediction drift. Performance is the confirmation, not the alarm.

ASK: How long after a prediction do you learn whether it was right?
WATCH OUT: the threshold on the slide is an example, not a recommendation.
IF SHORT ON TIME: say "drift is the early signal, performance is the confirmation" and move on.
SOURCE: https://learn.microsoft.com/en-us/azure/machine-learning/concept-model-monitoring?view=azureml-api-2 (the model performance signal, in preview, needs ground truth)
TRANSITION: So what exactly should you monitor? Three layers."""


# ------------------------------------------------------------------ P2.33 three monitoring layers
def platform_card(s, x, y, w, h, name, color, soft, bullets, size=14):
    box(s, x, y, w, h, tone="paper", radius=0.12, line_w=1.25, fill_color=soft, line_color=color,
        name=f"platform: {name}")
    paras = [dict(text=name, size=15, bold=True, font=HEAD, color=color, after=3)]
    paras += [dict(text=b, bullet=True, bullet_color=color, after=3) for b in bullets]
    return text(s, x + 0.18, y + 0.12, w - 0.36, h - 0.2, paras, size=size, name=f"platform text: {name}")


def _draw_layers(f):
    s = f.s
    gap, ch = 0.2, 2.3
    cw = (f.w - 2 * gap) / 3
    layers = (
        ("Technical", "Does it run?", "activity",
         ["Latency", "CPU and memory", "Calls and duration", "Errors", "Cost"], "Owner: platform team"),
        ("Data", "Is the data normal?", "database",
         ["Schema", "Null rate", "Value ranges", "Volume and freshness", "Drift (PSI)"], "Owner: data engineer"),
        ("Model and business", "Is the model right?", "line-chart",
         ["PR-AUC (when labels arrive)", "Calibration", "Precision at top 5 %", "Avoided unplanned downtime"],
         "Owner: data scientist and business owner"),
    )
    for i, (title, q, icon, chips, who) in enumerate(layers):
        x = f.x + i * (cw + gap)
        box(s, x, f.y, cw, ch, tone="node", radius=0.12, name=f"layer: {title}")
        add_icon(s, icon, x + 0.16, f.y + 0.14, 0.36, color="azure")
        text(s, x + 0.64, f.y + 0.12, cw - 0.8, 0.6, [dict(text=title, size=17, bold=True, font=HEAD),
                                                      dict(text=q, size=14, color="muted")],
             name=f"layer title: {title}")
        chip_flow(s, x + 0.16, f.y + 0.82, cw - 0.32, chips, size=14, h=0.3, gap=0.07)
        text(s, x + 0.16, f.y + ch - 0.4, cw - 0.32, 0.3, [who], size=14, color="muted", anchor="m",
             name=f"owner: {title}")

    wy = f.y + ch + 0.1
    text(s, f.x, wy, 4.0, 0.3, ["Where it lives"], size=15, bold=True, font=HEAD, anchor="m", name="where it lives")
    py = wy + 0.34
    pw = (f.w - gap) / 2
    platform_card(s, f.x, py, pw, f.b - py, "Azure ML", BLUE, BLUE_SOFT, [
        "Endpoints: Azure Monitor and Application Insights.",
        "Managed model monitoring: drift, data quality, performance (preview), alerts via Event Grid.",
    ])
    platform_card(s, f.x + pw + gap, py, pw, f.b - py, "Microsoft Fabric", TEAL, TEAL_SOFT, [
        "Monitor hub (runs) and Capacity Metrics app (consumption).",
        "No managed model monitoring for classical ML: build it with notebooks, a metrics table, Power BI and "
        "Activator.",
    ])


NOTES_LAYERS = """A healthy service can still serve a drifting model, so monitoring has three layers and three owners.

Technical: does it run? Latency, CPU and memory, calls and duration, errors, cost. The platform team owns it. Data: is the data normal? Schema, null rate, value ranges, volume and freshness, drift. The data engineer owns it. Model and business: is the model right? PR-AUC once labels arrive, calibration, precision at the top 5 percent, and the business result, avoided unplanned downtime. The data scientist and the business owner share it.

Where it lives. In Azure ML, online endpoints send metrics and logs to Azure Monitor and Application Insights, and managed model monitoring covers data drift, prediction drift, data quality and, when ground truth exists, model performance (still in preview), with alerts through Event Grid. In Fabric, the Monitor hub shows run status and the Capacity Metrics app shows consumption. The docs we reviewed show no first-party managed model monitoring for classical ML, so build it: scheduled notebooks write a metrics table, Power BI shows it and Activator alerts on it.

ASK: Who owns each layer in your team today?
WATCH OUT: do not promise managed drift monitoring on Fabric.
VERIFY: the Fabric statement comes from the fact sheet (docs reviewed); re-check Microsoft Learn before the session.
SOURCE: https://learn.microsoft.com/en-us/azure/machine-learning/how-to-monitor-online-endpoints?view=azureml-api-2 ; https://learn.microsoft.com/en-us/azure/machine-learning/concept-model-monitoring?view=azureml-api-2 ; https://learn.microsoft.com/en-us/fabric/admin/monitoring-hub ; https://learn.microsoft.com/en-us/fabric/enterprise/metrics-app
TRANSITION: Monitoring tells you when to retrain. Before that, what a new model must beat to replace the current one."""


# ------------------------------------------------------------------ P2.34 data validation
def _draw_validation(f):
    s = f.s

    def X(dx):
        return f.x + dx

    lh, lg = 1.11, 0.1
    ys = [f.y + i * (lh + lg) for i in range(3)]
    mid = [y + lh / 2 for y in ys]
    ymid = mid[1]
    lanes = (
        ("Schema", "table", "node", ["Columns and types match the contract", "Timestamps parse (ISO Z, offset, epoch ms)"]),
        ("Statistics", "bar-chart-3", "node", ["Rows per day and null rate vs recent weeks",
                                              "Ranges per sensor (vibration 0 to 30 mm/s)"]),
        ("Anomalies", "alert-triangle", "amber", [f"{n(F.duplicates)} duplicate event ids, {n(F.late_rows)} late events",
                                                  f"{n(F.out_of_range)} spikes (999), {n(F.unresolved)} readings with "
                                                  "no asset match"]),
    )
    for y, (t, ic, tone, bl) in zip(ys, lanes):
        card(s, X(2.2), y, 5.4, lh, t, [f"- {b}" for b in bl], icon=ic, tone=tone, title_size=15, body_size=14,
             pad=0.13, after=2, name=f"lane: {t}")

    card(s, X(0), ymid - 1.0, 1.75, 2.0, "Raw batch", ["Telematics events and CMMS work orders"], icon="database",
         icon_pos="top", title_size=15, body_size=14, pad=0.13, after=2, name="card: Raw batch")
    arrow(s, X(1.75), ymid, X(1.975), ymid, color="muted", w=1.5, tail=False, name="raw to trunk")
    rule(s, X(1.975), mid[0], X(1.975), mid[2], color="muted", w=1.5, name="fan-out trunk")
    for i, m in enumerate(mid):
        arrow(s, X(1.975), m, X(2.2), m, color="muted", w=1.5, name=f"fan-out {i + 1}")
        rule(s, X(7.6), m, X(7.82), m, color="muted", w=1.5, name=f"merge {i + 1}")
    rule(s, X(7.82), mid[0], X(7.82), mid[2], color="muted", w=1.5, name="merge trunk")
    arrow(s, X(7.82), ymid, X(8.05), ymid, color="muted", w=1.5, name="to decision")

    dm = box(s, X(8.05), ymid - 0.65, 1.5, 1.3, tone="amber", shape=MSO_SHAPE.DIAMOND, line_w=1.5,
             name="decision: Valid?")
    fill_text(dm.text_frame, ["Valid?"], size=15, bold=True, font=HEAD, color="amber", align="c", anchor="m",
              margins=(0, 0, 0, 0), wrap=False)
    cx = X(9.95)
    yes_y, no_y = f.y, ys[2] + lh - 1.3
    card(s, cx, yes_y, f.r - cx, 1.3, "Yes: continue", ["Transform, then train."], icon="check-circle", tone="success",
         title_size=15, body_size=14, pad=0.14, after=2, name="outcome: yes")
    card(s, cx, no_y, f.r - cx, 1.3, "No: stop", ["Alert the owner and quarantine the batch."], icon="x-circle",
         tone="amber", title_size=15, body_size=14, pad=0.14, after=2, name="outcome: no")
    polyline(s, [(X(8.8), ymid - 0.65), (X(8.8), yes_y + 0.65), (cx, yes_y + 0.65)], color="success", w=2.0,
             name="path yes")
    polyline(s, [(X(8.8), ymid + 0.65), (X(8.8), no_y + 0.65), (cx, no_y + 0.65)], color="amber", w=2.0,
             name="path no")
    label(s, X(9.1), yes_y + 0.65 - 0.27, 0.7, "yes", size=12, color="success", bold=True, mono=False, name="yes")
    label(s, X(9.1), no_y + 0.65 - 0.27, 0.7, "no", size=12, color="amber", bold=True, mono=False, name="no")

    hy = f.b - 0.5
    box(s, f.x, hy, f.w, 0.5, tone="node", radius=0.1, name="how strip")
    text(s, f.x + 0.2, hy, f.w - 0.4, 0.5, ["**How:** expectations as code (Great Expectations, pandera), Delta constraints, "
                                           "and a pipeline step that fails the run."], size=14, anchor="m",
         name="how text")


NOTES_VALIDATION = f"""A gate on the model is not enough: the same logic belongs at the front of the pipeline. The data contract we saw earlier is the specification; this slide is the enforcement. Every new batch of telematics events and work orders goes through three kinds of check before anything is transformed or trained.

Schema: columns and types match the contract, and timestamps parse in all three formats. Statistics: rows per day and null rate against recent weeks, and ranges per sensor. Anomalies: our reference run found {n(F.duplicates)} duplicate event ids, {n(F.late_rows)} late events, {n(F.out_of_range)} spikes of 999 and {n(F.unresolved)} readings with no asset match. Then one decision. Valid: continue. Not valid: stop the run, alert the owner and quarantine the batch. A pipeline that cannot say no will happily train on bad data.

Implementation options: expectations as code with Great Expectations or pandera, Delta constraints on the tables, and a pipeline step that fails the run. In Fabric pipelines the If Condition and Fail activities do the last part.

ASK: What happens in your pipeline today when a batch looks wrong?
WATCH OUT: quarantine the batch, do not silently drop rows, or you hide the problem.
IF SHORT ON TIME: name the three checks and the yes or no decision.
VERIFY: Delta CHECK constraints on Fabric Lakehouse tables: test in a notebook before promising it.
SOURCE: https://learn.microsoft.com/en-us/fabric/data-factory/if-condition-activity ; https://learn.microsoft.com/en-us/fabric/data-factory/fail-activity
TRANSITION: Next, responsible AI, which also needs a pipeline."""


# ------------------------------------------------------------------ P2.35 responsible AI
def _draw_responsible(f):
    s = f.s
    g = 0.15
    pw = (f.w - 3 * g) / 4
    for i, (t, ic, b) in enumerate((
        ("Compliance", "shield-check", "Traceable lineage: data, code, run and approver for each model."),
        ("Evaluation", "clipboard-check", "Transparent metrics and thresholds behind each deployment decision."),
        ("Explainability", "eye", "Feature importance, global and local (InterpretML, SHAP)."),
        ("Fairness", "scale", "No unjustified gap between groups: same metric per group (Fairlearn)."),
    )):
        card(s, f.x + i * (pw + g), f.y, pw, 1.5, t, [b], icon=ic, title_size=16, body_size=14, pad=0.16, after=2,
             name=f"pillar: {t}")

    ey = f.y + 1.5 + 0.12
    hw = (f.w - g) / 2
    card(s, f.x, ey, hw, 1.3, "Fleet example: explainable",
         ["Why is this excavator flagged? Show the signals behind the score, and prefer a white-box model when a "
          "person must act."], icon="eye", tone="azure", title_size=16, body_size=14, pad=0.16, after=2,
         name="example: explainable")
    card(s, f.x + hw + g, ey, hw, 1.3, "Fleet example: fair",
         ["No systematic under-coverage of one site, machine family or country (12 sites in 8 countries). Compare "
          "recall per group."], icon="scale", tone="azure", title_size=16, body_size=14, pad=0.16, after=2,
         name="example: fair")

    ry = ey + 1.3 + 0.12
    text(s, f.x, ry, 1.9, 0.56, ["Make it routine"], size=16, bold=True, font=HEAD, anchor="m", name="routine title")
    steps = ("Log explanation and fairness results with MLflow", "Check them in the promotion gate",
             "Keep them versioned with the model")
    ag = 0.35
    cx0 = f.x + 2.0
    cw = (f.r - cx0 - 2 * ag) / 3
    for i, t in enumerate(steps):
        x = cx0 + i * (cw + ag)
        chip(s, x, ry, cw, 0.56, t, tone="azure", size=14, name=f"routine step {i + 1}")
        if i < 2:
            arrow(s, x + cw + 0.05, ry + 0.28, x + cw + ag - 0.05, ry + 0.28, color="azure", w=1.75,
                  name=f"routine arrow {i + 1}")
    text(s, cx0, ry + 0.66, f.r - cx0, 0.28,
         ["Azure ML Responsible AI dashboard (preview) bundles Fairlearn and InterpretML."], size=14, color="muted",
         name="routine note")


NOTES_RESPONSIBLE = """Responsible AI is not a separate project. It is four properties you can only guarantee if the pipeline produces the evidence every time. Compliance: traceable lineage, with data, code, run and approver for each model. Evaluation: transparent metrics and thresholds behind each deployment decision. Explainability: feature importance, global and local. Fairness: no unjustified gap between groups.

Fleet example, explainable: a site manager asks why this excavator is flagged. We show the signals that drove the score, and when a person must act on a score we prefer a white-box model. Careful: the top drivers column in our risk table is rule based, not a model attribution, so say so. Fleet example, fair: we have 12 sites in 8 countries, so check that recall does not collapse for one site, one machine family or one country.

Make it routine: log explanation and fairness results as MLflow artifacts next to the model, check them in the promotion gate, and keep them versioned with the model. Azure ML offers a Responsible AI dashboard, in preview, that bundles Fairlearn and InterpretML.

ASK: Which of these four could you prove today for your last model?
WATCH OUT: the Responsible AI dashboard is a preview feature; do not make it a live dependency.
VERIFY: preview status of the Azure ML Responsible AI dashboard (fact sheet: public preview, docs updated 2026-01).
SOURCE: https://learn.microsoft.com/en-us/azure/machine-learning/concept-responsible-ai-dashboard?view=azureml-api-2
TRANSITION: Let us put all of it into one flow."""


# ------------------------------------------------------------------ P2.36 complete CI / CT / CD flow
def _draw_flow(f):
    s = f.s
    side, bh, gy = 0.2, 1.08, 0.32
    y1 = f.y
    y2 = y1 + bh + gy
    y3 = y2 + bh + 0.82
    inner = f.w - 2 * side
    for by, tag, head in ((y1, "CI", "Continuous integration: build and test the code"),
                          (y2, "CT", "Continuous training: build the model"),
                          (y3, "CD", "Continuous deployment: ship and watch")):
        box(s, f.x, by, f.w, bh, tone="node", radius=0.12, name=f"band {tag}")
        hw = text_w(head, HEAD, 15, True) * 1.03
        x0 = f.x + (f.w - (0.72 + hw)) / 2
        pill(s, x0, by + 0.08, tag, tone="solid", size=12, h=0.3, w=0.6, name=f"pill {tag}")
        text(s, x0 + 0.72, by + 0.07, hw + 0.05, 0.32, [head], size=15, bold=True, font=HEAD, anchor="m",
             name=f"band title {tag}")

    def step(x, y, w, num, txt, hot=False):
        shp = box(s, x, y, w, 0.6, tone="amber" if hot else "paper", radius=0.1, name=f"step {num}: {txt}")
        fill_text(shp.text_frame, [txt], size=14, bold=hot, color="ink", anchor="m", margins=(0.44, 0.02, 0.06, 0.02))
        lint_fit(shp.name, [txt], w - 0.5, 0.56, size=14, bold=hot)
        num_badge(s, x + 0.08, y + 0.15, num, tone="amber" if hot else "solid", size=0.3, fsize=12)

    def row(by, names, first, gap, reverse=False):
        k = len(names)
        w = (inner - (k - 1) * gap) / k
        xs = [f.x + side + i * (w + gap) for i in range(k)]
        order = list(range(k))[::-1] if reverse else list(range(k))
        for slot, i in enumerate(order):
            step(xs[slot], by + 0.4, w, first + i, names[i], hot=names[i] == "Model registry")
        ay = by + 0.7
        for slot in range(k - 1):
            if reverse:
                arrow(s, xs[slot + 1] - 0.03, ay, xs[slot] + w + 0.03, ay, color="muted", w=1.5, name="flow arrow")
            else:
                arrow(s, xs[slot] + w + 0.03, ay, xs[slot + 1] - 0.03, ay, color="muted", w=1.5, name="flow arrow")
        return xs, w

    row(y1, ["New code", "Source repo", "Build components", "Run tests", "Deploy pipeline"], 1, 0.32)
    xs2, w2 = row(y2, ["Ingest data", "Validate data", "Transform data", "Train model", "Analyze model",
                       "Model registry"], 6, 0.28, reverse=True)
    row(y3, ["Validate model", "Run tests", "Deploy model", "Prediction service", "Monitor model"], 12, 0.32)

    ax = f.x + 11.5
    arrow(s, ax, y1 + 1.0, ax, y2 + 0.4, color="muted", w=2.0, name="CI to CT")
    label(s, ax - 3.4, y1 + bh + 0.04, 3.3, "deploys the training pipeline", size=12, align="r", mono=False,
          name="CI to CT label")
    fx = f.x + 10.9
    arrow(s, fx, y3 + 0.4, fx, y2 + 1.0, color="amber", w=2.25, dash=True, name="feedback loop")
    label(s, fx - 4.7, y2 + bh + 0.2, 4.6, "feedback loop: drift or performance trigger", size=12, color="amber",
          bold=True, align="r", mono=False, name="feedback label")

    gate = "Go / no go gate"
    gw = text_w(gate, BODY, 12, True) * 1.03 + 0.3
    gx = xs2[0] + w2 / 2
    gy = y2 + bh + 0.14
    arrow(s, gx, y2 + 1.0, gx, gy, color="amber", w=2.0, name="registry to gate")
    pill(s, gx - gw / 2, gy, gate, tone="amber_solid", size=12, h=0.34, w=gw, caps=False, mono=False, name="gate")
    arrow(s, gx, gy + 0.34, gx, y3 + 0.4, color="amber", w=2.0, name="gate to validate")
    text(s, gx + gw / 2 + 0.15, gy, 3.9, 0.34, ["go if the candidate beats the champion"], size=12, color="muted",
         anchor="m", name="gate caption")


NOTES_FLOW = """This is the whole picture in one flow: three loops around one registry and one gate. Walk it in order.

CI, steps 1 to 5: new code lands in the source repo, components are built, tests run, and the training pipeline is deployed. CT, steps 6 to 11: ingest the data, validate it, transform it, train, analyze the candidate, and register it. Then the gate: go only if the candidate beats the champion on the agreed metrics. CD, steps 12 to 16: validate the model, run tests, deploy, serve predictions, and monitor. The amber arrow is the feedback loop: a drift or performance trigger starts the training pipeline again. In the original sketch, a performance trigger starts the evaluation of several candidate models, and the best one is selected and promoted automatically.

An earlier slide shows the three cards, CI, CT and CD, and another shows the promotion gate in detail. This one only connects them.

ASK: Which of the 16 steps do you already automate?
IF SHORT ON TIME: name the three loops, point at the registry and the gate, and stop.
TRANSITION: How far along is your team? The next slide gives five maturity levels."""


def build(d: Deck) -> None:
    d.custom(
        "P2.31", "Data drift: the inputs change before the model notices", _draw_data_drift,
        takeaway="Drift in the inputs is an early warning because it shows up before the labels arrive.",
        source="Azure ML model monitoring offers these drift signals out of the box (Microsoft Learn). PSI thresholds "
               "are a rule of thumb, not a standard.",
        minutes=4, core=False, notes=_notes_data_drift(),
    )
    d.custom(
        "P2.32", "Model drift is what the business feels: performance decays", _draw_model_drift,
        takeaway="Use data drift as the early signal and measured performance as the confirmation.",
        source="The curve is illustrative, anchored on the test PR-AUC of about 0.38. A Power BI report on the metrics "
               "table is the usual dashboard.",
        minutes=3, core=False, notes=NOTES_MODEL_DRIFT,
    )
    d.custom(
        "P2.33", "Monitoring has three layers: does it run, is the data normal, is the model right", _draw_layers,
        takeaway="Monitor all three layers: a healthy service can still serve a drifting model.",
        source="Microsoft Learn: monitor online endpoints, Azure ML model monitoring, Monitor hub, Capacity Metrics app.",
        minutes=4, core=False, notes=NOTES_LAYERS,
    )
    d.custom(
        "P2.34", "Validate the data first, then decide whether the pipeline continues", _draw_validation,
        takeaway="A pipeline that cannot say no will happily train on bad data.",
        source="Counts from the reference run. Great Expectations and pandera are open-source libraries.",
        minutes=3, core=False, notes=NOTES_VALIDATION,
    )
    d.custom(
        "P2.35", "Responsible AI needs MLOps: every model decision must be explainable and traceable",
        _draw_responsible,
        takeaway="Explainability and fairness checks belong in the pipeline, not in a slide after the incident.",
        source="Azure ML Responsible AI dashboard (preview): Fairlearn, InterpretML, error analysis (Microsoft Learn).",
        minutes=3, core=False, notes=NOTES_RESPONSIBLE,
    )
    d.custom(
        "P2.36", "One flow: CI builds, CT trains, CD ships and watches", _draw_flow,
        takeaway="Three loops, one registry, one gate: that is MLOps.",
        minutes=4, core=False, notes=NOTES_FLOW,
    )
