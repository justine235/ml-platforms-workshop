"""Native tables, charts and code blocks (everything stays editable in PowerPoint)."""
from __future__ import annotations

import re

from lxml import etree
from pptx.chart.data import CategoryChartData
from pptx.enum.chart import XL_CHART_TYPE, XL_LABEL_POSITION, XL_LEGEND_POSITION, XL_TICK_MARK
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Inches, Pt

from deck_core import (BODY, CTX, HEAD, LINT, MONO, PAL, TONES, _add_runs, box, lines_needed, rgb, text, text_w)

NO_STYLE_ID = "{2D5ABB26-0587-4C30-8999-92F81FD0307C}"
_ALIGN = {"l": PP_ALIGN.LEFT, "c": PP_ALIGN.CENTER, "r": PP_ALIGN.RIGHT}


# ---------------------------------------------------------------- tables
def _border(tag, spec):
    color, w_pt = spec if spec else (None, 0)
    ln = etree.Element(qn(tag), w=str(int(w_pt * 12700)), cap="flat", cmpd="sng", algn="ctr")
    if color is None:
        etree.SubElement(ln, qn("a:noFill"))
    else:
        etree.SubElement(etree.SubElement(ln, qn("a:solidFill")), qn("a:srgbClr"), val=PAL.get(color, color))
        etree.SubElement(ln, qn("a:prstDash"), val="solid")
    return ln


def _set_borders(cell, top=None, bottom=None):
    """Borders must precede the fill element inside a:tcPr (schema order lnL, lnR, lnT, lnB, fill)."""
    tcPr = cell._tc.get_or_add_tcPr()
    for tag in ("a:lnL", "a:lnR", "a:lnT", "a:lnB"):
        for old in tcPr.findall(qn(tag)):
            tcPr.remove(old)
    for i, (tag, spec) in enumerate((("a:lnL", None), ("a:lnR", None), ("a:lnT", top), ("a:lnB", bottom))):
        tcPr.insert(i, _border(tag, spec))


def _cell_text(cell, txt, size, color, font, bold, align, pad_x, pad_y):
    tf = cell.text_frame
    cell.margin_left = cell.margin_right = Inches(pad_x)
    cell.margin_top = cell.margin_bottom = Inches(pad_y)
    cell.vertical_anchor = MSO_ANCHOR.MIDDLE
    for i, line in enumerate(str(txt).split("\n")):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = _ALIGN[align]
        _add_runs(p, line, size, color, font, bold, False, 0)


def table(slide, x, y, w, header, rows, col_w=None, size=13, head_size=None, align=None, bold_first=False,
          zebra=False, pad_x=0.12, pad_y=0.07, max_bottom=6.6, name="table", row_tones=None, mono_cols=(),
          min_row_h=0.0, head_tone="azure", fit=None):
    """Native table with a quiet style. Cells are str or dict(text, bold, color, tone, align, mono, size).

    `fit` is a sequence of candidate body sizes (largest first): the first one that fits above `max_bottom` is used,
    then the rows are padded a little when there is room. Returns (graphic_frame, total_height_in).
    """
    ncols = len(header or rows[0])
    weights = col_w or [1] * ncols
    widths = [w * k / sum(weights) for k in weights]
    align = align or ["l"] * ncols
    row_tones = row_tones or {}

    def spec(cell):
        return dict(text=cell) if isinstance(cell, str) else dict(cell)

    grid = ([("head", [spec(c) for c in header])] if header else []) + [("body", [spec(c) for c in r]) for r in rows]

    def measure(sz, hs, py):
        out = []
        for kind, cells in grid:
            n = 1
            for ci, c in enumerate(cells):
                font = MONO if (c.get("mono") or (kind == "body" and ci in mono_cols)) else (HEAD if kind == "head" else BODY)
                s = hs if kind == "head" else c.get("size", sz)
                bold = kind == "head" or c.get("bold") or (bold_first and ci == 0)
                n = max(n, lines_needed(c["text"], widths[ci] - 2 * pad_x, font, s, bool(bold)))
            s0 = hs if kind == "head" else sz
            out.append(max(min_row_h, n * s0 * 1.2 / 72 + 2 * py))
        return out

    if fit:
        size = next((c for c in fit if y + sum(measure(c, head_size or c - 0.5, pad_y)) <= max_bottom), fit[-1])
    head_size = head_size or size - 0.5
    heights = measure(size, head_size, pad_y)
    if fit:
        room = max_bottom - y - sum(heights) - 0.1
        if room > 0:
            pad_y = min(0.2, pad_y + room / (2 * len(grid)))
            heights = measure(size, head_size, pad_y)
    total = sum(heights)
    if y + total > max_bottom + 0.02:
        LINT.append(f"[{CTX['slide']}] table '{name}' ends at {y + total:.2f} in (limit {max_bottom:.2f})")

    gf = slide.shapes.add_table(len(grid), ncols, Inches(x), Inches(y), Inches(w), Inches(total))
    gf.name = name
    tbl = gf.table
    tbl.first_row = False
    tbl.horz_banding = False
    gf._element.xpath(".//a:tableStyleId")[0].text = NO_STYLE_ID
    for ci, cw in enumerate(widths):
        tbl.columns[ci].width = Inches(cw)
    for ri, ((kind, cells), rh) in enumerate(zip(grid, heights)):
        tbl.rows[ri].height = Inches(rh)
        body_i = ri - (1 if header else 0)
        for ci, c in enumerate(cells):
            cell = tbl.cell(ri, ci)
            head = kind == "head"
            font = MONO if (c.get("mono") or (not head and ci in mono_cols)) else (HEAD if head else BODY)
            color = c.get("color", "ink")
            bold = head or c.get("bold") or (bold_first and ci == 0)
            _cell_text(cell, c["text"], head_size if head else c.get("size", size), color, font, bool(bold),
                       c.get("align", align[ci]), pad_x, pad_y)
            _set_borders(cell, bottom=("azure", 1.5) if head else ("line", 0.75))
            tone = c.get("tone") or row_tones.get(body_i if not head else -1)
            fill = TONES[head_tone]["fill"] if head else (TONES[tone]["fill"] if tone else ("node" if zebra and body_i % 2 else None))
            if fill:
                cell.fill.solid()
                cell.fill.fore_color.rgb = rgb(fill)
    return gf, total


# ---------------------------------------------------------------- charts
def fmt_value(v, fmt):
    """Render a number the way an Excel-style format ('0.00', '0.0%', '#,##0') would, but locale-proof."""
    pct = "%" in fmt
    tail = fmt.split(".")[1] if "." in fmt else ""
    dec = sum(ch in "0#" for ch in tail)
    val = v * 100 if pct else v
    out = f"{val:,.{dec}f}" if "," in fmt else f"{val:.{dec}f}"
    return out + ("%" if pct else "")


def bar_chart(slide, x, y, w, h, cats, series, horizontal=True, fmt="0.0", highlight=None, colors=None,
              label_size=13, axis_size=13, gap=55, max_val=None, legend=False, name="chart", alt=None, kind="bar",
              labels=None):
    """Native bar/column/line chart. `series` is {name: [values]}; `highlight` indexes get the accent colour.

    Data labels are written as explicit text (so '0.385' stays '0.385' on a machine with a comma decimal separator);
    `labels` optionally gives {series: [text, ...]} to override them."""
    cd = CategoryChartData(number_format=fmt)
    cd.categories = list(cats)
    for sname, vals in series.items():
        cd.add_series(sname, list(vals))
    ctype = {"bar": XL_CHART_TYPE.BAR_CLUSTERED if horizontal else XL_CHART_TYPE.COLUMN_CLUSTERED,
             "line": XL_CHART_TYPE.LINE_MARKERS}[kind]
    gf = slide.shapes.add_chart(ctype, Inches(x), Inches(y), Inches(w), Inches(h), cd)
    gf.name = name
    gf._element.xpath(".//p:cNvPr")[0].set("descr", alt or name)
    ch = gf.chart
    ch.has_title = False
    ch.font.size, ch.font.name = Pt(axis_size), BODY
    ch.font.color.rgb = rgb("ink")
    ch.has_legend = legend or len(series) > 1
    if ch.has_legend:
        ch.legend.position = XL_LEGEND_POSITION.BOTTOM
        ch.legend.include_in_layout = False
        ch.legend.font.size = Pt(axis_size)
    va, ca = ch.value_axis, ch.category_axis
    va.has_major_gridlines = False
    va.visible = kind == "line"
    va.format.line.fill.background()
    if kind == "line":
        va.tick_labels.font.size = Pt(axis_size - 1)
        va.tick_labels.font.color.rgb = rgb("muted")
        va.major_gridlines.format.line.color.rgb = rgb("line") if va.has_major_gridlines else None
    if max_val is not None:
        va.maximum_scale = max_val
    va.minimum_scale = 0
    ca.format.line.color.rgb = rgb("node_line")
    ca.major_tick_mark = XL_TICK_MARK.NONE
    ca.tick_labels.font.size = Pt(axis_size)
    if horizontal and kind == "bar":
        ca.reverse_order = True
    plot = ch.plots[0]
    if kind == "bar":
        plot.gap_width = gap
        plot.vary_by_categories = False
    plot.has_data_labels = True
    dl = plot.data_labels
    dl.number_format, dl.number_format_is_linked = fmt, False
    dl.font.size, dl.font.bold = Pt(label_size), True
    dl.position = XL_LABEL_POSITION.OUTSIDE_END if kind == "bar" else XL_LABEL_POSITION.ABOVE
    palette = colors or ["azure", "amber", "success", "sand"]
    hl = set([highlight] if isinstance(highlight, int) else (highlight or []))
    for si, (sname, vals) in enumerate(series.items()):
        ser = plot.series[si]
        for i, v in enumerate(vals):
            dlab = ser.points[i].data_label
            dlab.text_frame.text = (labels or {}).get(sname, [None] * len(vals))[i] or fmt_value(v, fmt)
            run = dlab.text_frame.paragraphs[0].runs[0]
            run.font.size, run.font.bold, run.font.name = Pt(label_size), True, BODY
            run.font.color.rgb = rgb("ink")
            dlab.position = XL_LABEL_POSITION.OUTSIDE_END if kind == "bar" else XL_LABEL_POSITION.ABOVE
    for si, ser in enumerate(plot.series):
        base = palette[si % len(palette)] if len(series) > 1 else ("sand" if hl else "azure")
        if kind == "line":
            ser.format.line.color.rgb = rgb(base)
            ser.format.line.width = Pt(2.5)
            ser.smooth = False
            ser.marker.format.fill.solid()
            ser.marker.format.fill.fore_color.rgb = rgb(base)
            ser.marker.format.line.color.rgb = rgb(base)
            continue
        ser.format.fill.solid()
        ser.format.fill.fore_color.rgb = rgb(base)
        for i in hl:
            pt = ser.points[i]
            pt.format.fill.solid()
            pt.format.fill.fore_color.rgb = rgb("azure")
    return gf


# ---------------------------------------------------------------- code
_KW = {
    "python": "def class return import from as if elif else for while in not and or is with try except finally raise "
              "lambda yield pass break continue None True False async await",
    "sql": "select from where group by order having join left right inner outer on as and or not in is null case when "
           "then else end union all create table insert into values update set delete limit with over partition "
           "distinct desc asc merge using matched cast",
    "bash": "if then fi for do done in export set echo cd",
    "yaml": "true false null",
    "json": "true false null",
}
_COMMENT = {"python": "#", "yaml": "#", "bash": "#", "sql": "--", "json": None, "bicep": "//", "js": "//"}
_LIGHT = dict(kw="azure", string="amber", comment="muted", number="success", word="ink", other="ink")
_DARK = dict(kw="8CC4F5", string="F0C078", comment="9FB4D0", number="8FD6B5", word="F2F5FA", other="F2F5FA")
_RX: dict = {}


def _rx(lang):
    if lang not in _RX:
        cm = _COMMENT.get(lang, "#")
        pats = ([rf"(?P<comment>{re.escape(cm)}.*$)"] if cm else []) + [
            r"(?P<string>\"(?:[^\"\\]|\\.)*\"|'(?:[^'\\]|\\.)*')", r"(?P<number>\b\d[\d_]*(?:\.\d+)?\b)",
            r"(?P<word>[A-Za-z_][A-Za-z0-9_]*)", r"(?P<other>\s+|.)"]
        _RX[lang] = re.compile("|".join(pats))
    return _RX[lang]


def tokens(line: str, lang: str):
    if lang == "yaml":
        m = re.match(r"^(\s*-?\s*)([\w./-]+)(:)(.*)$", line)
        if m:
            return [(m[1], "other"), (m[2], "kw"), (m[3], "other")] + tokens(m[4], "yaml-val")
    kws = set(_KW.get(lang if lang != "yaml-val" else "yaml", "").split())
    out = []
    for m in _rx("yaml" if lang == "yaml-val" else lang).finditer(line):
        kind, tok = m.lastgroup, m.group()
        if kind == "word" and (tok.lower() if lang == "sql" else tok) in kws:
            kind = "kw"
        out.append((tok, kind))
    return out


def code_block(slide, x, y, w, h, code, lang="python", size=12.5, title=None, dark=False, hl=(), pad=0.2,
               name="code", spacing=1.34):
    """Syntax-lit code panel. One paragraph per line with exact spacing so highlight bands line up."""
    code = code.strip("\n")
    lines = code.split("\n")
    tone = "dark" if dark else "node"
    box(slide, x, y, w, h, tone=tone, radius=0.12, name=f"{name} panel", line_w=1.0)
    head_h = 0.42 if title else 0.0
    if title:
        text(slide, x + pad, y + 0.12, w - 2 * pad, 0.24, [title], size=11, color="sand" if dark else "muted",
             font=MONO, bold=True, anchor="m", wrap=False, lint=False, name=f"{name} title")
    line_h = size * spacing
    top = y + pad * 0.7 + head_h
    inner_w, inner_h = w - 2 * pad, h - head_h - pad * 1.4
    for i in hl:
        band = box(slide, x + 0.08, top + (i - 1) * line_h / 72 - 0.01, w - 0.16, line_h / 72 + 0.02,
                   tone="amber", radius=0.04, line_w=0.25, name=f"{name} highlight {i}",
                   fill_color="2B3A55" if dark else "amber_soft", line_color="2B3A55" if dark else "amber_soft")
    tb = slide.shapes.add_textbox(Inches(x + pad), Inches(top), Inches(inner_w), Inches(inner_h))
    tb.name = name
    tf = tb.text_frame
    tf.word_wrap = False
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    colors = _DARK if dark else _LIGHT
    for i, line in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.line_spacing = Pt(line_h)
        p.space_after = Pt(0)
        for tok, kind in tokens(line.replace("\t", "    ") or " ", lang):
            r = p.add_run()
            r.text = tok
            f = r.font
            f.name, f.size = MONO, Pt(size)
            f.bold, f.italic = kind == "kw", kind == "comment"
            f.color.rgb = rgb(colors[kind])
            r._r.get_or_add_rPr().set("lang", "en-US")
        widest = text_w(line, MONO, size)
        if widest > inner_w + 0.02:
            LINT.append(f"[{CTX['slide']}] {name} line {i + 1} is {widest:.2f} in wide (limit {inner_w:.2f}): {line[:40]}")
    if len(lines) * line_h / 72 > inner_h + 0.04:
        LINT.append(f"[{CTX['slide']}] {name} needs {len(lines) * line_h / 72:.2f} in but has {inner_h:.2f} in")
    return tb
