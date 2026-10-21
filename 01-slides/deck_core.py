"""Primitives for the workshop deck: palette, rich text, measuring, shapes, connectors.

Only native, editable python-pptx objects are produced (text boxes, rounded rectangles,
connectors, tables, charts, small PNG icons). Never a whole-slide image.
"""
from __future__ import annotations

import re
from pathlib import Path

from lxml import etree
from PIL import ImageFont
from pptx.dml.color import RGBColor
from pptx.enum.dml import MSO_LINE
from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, MSO_AUTO_SIZE, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Inches, Pt

HEAD, BODY, MONO = "Trebuchet MS", "Segoe UI", "Consolas"
SLIDE_W, SLIDE_H = 13.333, 7.5
MX = 0.533
CW = SLIDE_W - 2 * MX
BODY_TOP = 1.85

PAL = dict(
    paper="FFFFFF", white="FFFFFF", ink="16202F", muted="53617A", line="E2E8F2", azure="0F6CBD",
    azure_soft="EAF3FC", azure_line="BBD7F0", amber="A64B00", amber_soft="FFF4E4", amber_line="F0C078",
    success="1F7A55", success_soft="EFFAF5", success_line="A8D7C3", node="F7F9FC", node_line="D5DEEB",
    sand="9FB4D0",
)
TONES = {
    "node": dict(fill="node", line="node_line", accent="azure"),
    "paper": dict(fill="paper", line="node_line", accent="azure"),
    "azure": dict(fill="azure_soft", line="azure_line", accent="azure"),
    "amber": dict(fill="amber_soft", line="amber_line", accent="amber"),
    "success": dict(fill="success_soft", line="success_line", accent="success"),
    "solid": dict(fill="azure", line="azure", accent="white"),
    "dark": dict(fill="ink", line="ink", accent="white"),
    "amber_solid": dict(fill="amber", line="amber", accent="white"),
    "muted": dict(fill="paper", line="muted", accent="muted"),
}

LINT: list[str] = []
CTX = {"slide": "?"}


def rgb(key: str) -> RGBColor:
    return RGBColor.from_string(PAL.get(key, key).upper())


# ---------------------------------------------------------------- text metrics
_FONT_FILES = {
    (HEAD, False): "trebuc.ttf", (HEAD, True): "trebucbd.ttf",
    (BODY, False): "segoeui.ttf", (BODY, True): "segoeuib.ttf",
    (MONO, False): "consola.ttf", (MONO, True): "consolab.ttf",
}
_font_cache: dict = {}


def _ft(font: str, bold: bool, size: float):
    key = (font, bold, round(size * 10))
    if key not in _font_cache:
        file = _FONT_FILES.get((font, bold)) or _FONT_FILES[(BODY, bold)]
        _font_cache[key] = ImageFont.truetype(str(Path(r"C:\Windows\Fonts") / file), size=max(1, round(size * 10)))
    return _font_cache[key]


def text_w(text: str, font: str = BODY, size: float = 14, bold: bool = False) -> float:
    """Width in inches of a single line of text."""
    return _ft(font, bold, size).getlength(text) / 10 / 72


MARK = re.compile(r"(\*\*.+?\*\*|`[^`]+`)")


def plain(text: str) -> str:
    return re.sub(r"\*\*(.+?)\*\*", r"\1", re.sub(r"`([^`]+)`", r"\1", text))


def lines_needed(text: str, width_in: float, font: str = BODY, size: float = 14, bold: bool = False) -> int:
    total = 0
    for para in plain(text).split("\n"):
        count, cur = 1, ""
        for word in para.split(" "):
            trial = f"{cur} {word}" if cur else word
            if cur and text_w(trial, font, size, bold) * 1.03 > width_in:
                count, cur = count + 1, word
            else:
                cur = trial
        total += count
    return total


def _norm(para):
    """Return (spec dict, is_bullet) for a paragraph given as str or dict."""
    if isinstance(para, str):
        if para.startswith("- "):
            return {"text": para[2:], "bullet": True}
        return {"text": para}
    return dict(para)


def est_height(paras, width_in, size=14, font=BODY, bold=False, line=1.0, after=0, exact=None) -> float:
    if isinstance(paras, str):
        paras = paras.split("\n")
    total = 0.0
    for para in paras:
        sp = _norm(para)
        s = sp.get("size", size)
        avail = width_in - sp.get("indent", 0) - (sp.get("bullet_indent", 0.2) if sp.get("bullet") else 0)
        n = lines_needed(sp["text"], avail, sp.get("font", font), s, sp.get("bold", bold))
        lh = (exact if exact else s * 1.2 * sp.get("line", line)) / 72
        total += n * lh + sp.get("after", after) / 72 + sp.get("before", 0) / 72
    return total


def lint_fit(name: str, paras, w: float, h: float, **kw) -> None:
    need = est_height(paras, w, **{k: v for k, v in kw.items() if k in ("size", "font", "bold", "line", "after", "exact")})
    if need > h + 0.04:
        LINT.append(f"[{CTX['slide']}] '{name}' needs {need:.2f} in but has {h:.2f} in")


# ---------------------------------------------------------------- rich text
def _add_runs(p, text, size, color, font, bold, italic, track):
    for tok in MARK.split(text):
        if not tok:
            continue
        style = ""
        if tok.startswith("**") and tok.endswith("**") and len(tok) > 4:
            tok, style = tok[2:-2], "b"
        elif tok.startswith("`") and tok.endswith("`") and len(tok) > 2:
            tok, style = tok[1:-1], "c"
        r = p.add_run()
        r.text = tok
        f = r.font
        f.size = Pt(size * (0.94 if style == "c" else 1))
        f.bold = bool(bold or style == "b")
        f.italic = bool(italic)
        f.name = MONO if style == "c" else font
        f.color.rgb = rgb("azure" if style == "c" else color)
        rpr = r._r.get_or_add_rPr()
        rpr.set("lang", "en-US")
        if track:
            rpr.set("spc", str(int(track * 100)))


def _bullet(pPr, color, left_in, hang_in, char="\u2022"):
    pPr.set("marL", str(int((left_in + hang_in) * 914400)))
    pPr.set("indent", str(-int(hang_in * 914400)))
    clr = etree.SubElement(pPr, qn("a:buClr"))
    etree.SubElement(clr, qn("a:srgbClr"), val=PAL.get(color, color))
    etree.SubElement(pPr, qn("a:buFont"), typeface="Arial")
    etree.SubElement(pPr, qn("a:buChar"), char=char)


def fill_text(tf, paras, size=14, color="ink", font=BODY, bold=False, italic=False, align="l", anchor="t",
              line=1.0, after=0, margins=(0.1, 0.05, 0.1, 0.05), wrap=True, track=0, exact=None,
              bullet_color="azure"):
    tf.word_wrap = wrap
    tf.auto_size = MSO_AUTO_SIZE.NONE
    tf.margin_left, tf.margin_top, tf.margin_right, tf.margin_bottom = (Inches(m) for m in margins)
    tf.vertical_anchor = {"t": MSO_ANCHOR.TOP, "m": MSO_ANCHOR.MIDDLE, "b": MSO_ANCHOR.BOTTOM}[anchor]
    if isinstance(paras, str):
        paras = paras.split("\n")
    first = True
    for para in paras:
        sp = _norm(para)
        p = tf.paragraphs[0] if first else tf.add_paragraph()
        first = False
        p.alignment = {"l": PP_ALIGN.LEFT, "c": PP_ALIGN.CENTER, "r": PP_ALIGN.RIGHT}[sp.get("align", align)]
        p.line_spacing = Pt(exact) if exact else sp.get("line", line)
        p.space_after = Pt(sp.get("after", after))
        if sp.get("before"):
            p.space_before = Pt(sp["before"])
        pPr = p._p.get_or_add_pPr()
        if sp.get("indent") and not sp.get("bullet"):
            pPr.set("marL", str(int(sp["indent"] * 914400)))
        if sp.get("bullet"):
            _bullet(pPr, sp.get("bullet_color", bullet_color), sp.get("indent", 0), sp.get("bullet_indent", 0.2))
        _add_runs(p, sp["text"], sp.get("size", size), sp.get("color", color), sp.get("font", font),
                  sp.get("bold", bold), sp.get("italic", italic), sp.get("track", track))
# ---------------------------------------------------------------- shapes
def _no_style(shp) -> None:
    style = shp._element.find(qn("p:style"))
    if style is not None:
        shp._element.remove(style)


def text(slide, x, y, w, h, paras, name="text", lint=True, margins=(0, 0, 0, 0), **kw):
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tb.name = name
    fill_text(tb.text_frame, paras, margins=margins, **kw)
    if lint:
        lint_fit(name, paras, w - margins[0] - margins[2], h - margins[1] - margins[3], **kw)
    return tb


def box(slide, x, y, w, h, tone="node", radius=0.1, line_w=1.0, dash=False, filled=True,
        shape=MSO_SHAPE.ROUNDED_RECTANGLE, name="box", line_color=None, fill_color=None):
    shp = slide.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h))
    shp.name = name
    _no_style(shp)
    t = TONES[tone]
    if shape in (MSO_SHAPE.ROUNDED_RECTANGLE, MSO_SHAPE.ROUND_2_SAME_RECTANGLE):
        shp.adjustments[0] = min(0.5, radius / min(w, h))
    if filled:
        shp.fill.solid()
        shp.fill.fore_color.rgb = rgb(fill_color or t["fill"])
    else:
        shp.fill.background()
    shp.line.color.rgb = rgb(line_color or t["line"])
    shp.line.width = Pt(line_w)
    if dash:
        shp.line.dash_style = MSO_LINE.DASH
    return shp


def pill(slide, x, y, label, tone="azure", size=10, h=0.26, w=None, caps=True, mono=True, right=False, name=None):
    t = label.upper() if caps else label
    font = MONO if mono else BODY
    track = 0.6 if caps else 0
    wid = w or text_w(t, font, size, True) + len(t) * track / 72 + 0.26
    left = x - wid if right else x
    shp = box(slide, left, y, wid, h, tone=tone, radius=h / 2, line_w=0.75, name=name or f"pill: {label}")
    fill_text(shp.text_frame, [t], size=size, color=TONES[tone]["accent"], font=font, bold=True, align="c",
              anchor="m", margins=(0.04, 0, 0.04, 0), wrap=False, track=track)
    return shp, wid


def num_badge(slide, x, y, label_txt, tone="solid", size=0.36, fsize=14, name=None):
    """Numbered circle."""
    accent = TONES[tone]["accent"] if tone != "solid" else "azure"
    o = box(slide, x, y, size, size, tone="solid", shape=MSO_SHAPE.OVAL, name=name or f"badge {label_txt}",
            fill_color=accent, line_color=accent)
    fill_text(o.text_frame, [str(label_txt)], size=fsize, color="white", font=HEAD, bold=True, align="c", anchor="m",
              margins=(0, 0, 0, 0), wrap=False)
    return o

def card_need(w, title=None, body=None, title_size=17, body_size=14, pad=0.18, icon=False, icon_pos="inline",
              icon_size=0.36, after=4, line=1.0, badge=False) -> float:
    """Height in inches that card() needs for this content."""
    top_pad = pad + (icon_size + 0.1 if icon and icon_pos == "top" else 0)
    ind = (icon_size + 0.12) if ((icon and icon_pos != "top") or badge) else 0.0
    need = top_pad + pad * 0.7
    if title:
        need += lines_needed(title, w - 2 * pad - ind, HEAD, title_size, True) * title_size * 1.2 / 72
        need += (after + (2 if body else 0)) / 72
    paras = [{"after": after} | _norm(b) for b in ([] if body is None else [body] if isinstance(body, str) else body)]
    return need + est_height(paras, w - 2 * pad, size=body_size, line=line)


def card(slide, x, y, w, h, title=None, body=None, icon=None, tone="node", title_size=17, body_size=14,
         pad=0.18, icon_size=0.36, anchor="t", line_w=1.0, radius=0.12, name=None, title_color="ink",
         body_color="ink", after=4, line=1.0, icon_color=None, icon_pos="inline", badge=None):
    """One rounded rectangle holding title + body; the icon (or number badge) is laid over the top-left corner."""
    shp = box(slide, x, y, w, h, tone=tone, radius=radius, line_w=line_w, name=name or f"card: {title or body}")
    top_pad, ind = pad, 0.0
    if icon and icon_pos == "top":
        top_pad = pad + icon_size + 0.1
    elif icon or badge:
        ind = icon_size + 0.12
    paras = []
    if title:
        paras.append(dict(text=title, size=title_size, bold=True, font=HEAD, color=title_color, indent=ind,
                          after=after + (2 if body else 0)))
    for b in ([] if body is None else [body] if isinstance(body, str) else body):
        paras.append({"after": after} | _norm(b))
    fill_text(shp.text_frame, paras, size=body_size, color=body_color, anchor=anchor, line=line,
              margins=(pad, top_pad, pad, pad * 0.7))
    need = card_need(w, title, body, title_size, body_size, pad, bool(icon), icon_pos, icon_size, after, line, bool(badge))
    if anchor == "t" and need > h + 0.04:
        LINT.append(f"[{CTX['slide']}] '{shp.name}' needs {need:.2f} in but has {h:.2f} in")
    if icon:
        add_icon(slide, icon, x + pad, y + pad - 0.04, icon_size, color=icon_color or TONES[tone]["accent"])
    elif badge:
        num_badge(slide, x + pad, y + pad - 0.04, badge, tone=tone, size=icon_size)
    return shp

# ---------------------------------------------------------------- connectors
def _ends(line_shape, head=False, tail=True, size="med"):
    ln = line_shape.line._get_or_add_ln()
    for tag, on in (("a:headEnd", head), ("a:tailEnd", tail)):
        if on:
            etree.SubElement(ln, qn(tag), type="triangle", w=size, len=size)


def arrow(slide, x1, y1, x2, y2, color="muted", w=1.5, dash=False, head=False, tail=True, elbow=False, name="arrow"):
    kind = MSO_CONNECTOR.ELBOW if elbow else MSO_CONNECTOR.STRAIGHT
    c = slide.shapes.add_connector(kind, Inches(x1), Inches(y1), Inches(x2), Inches(y2))
    c.name = name
    _no_style(c)
    c.line.color.rgb = rgb(color)
    c.line.width = Pt(w)
    if dash:
        c.line.dash_style = MSO_LINE.DASH
    _ends(c, head=head, tail=tail)
    return c


def link(slide, a, b, a_side="r", b_side="l", color="muted", w=1.5, dash=False, head=False, tail=True,
         elbow=False, name="link"):
    """Connector glued to two shapes (sides t/l/b/r), so it follows them when moved in PowerPoint."""
    sites = {"t": 0, "l": 1, "b": 2, "r": 3}
    kind = MSO_CONNECTOR.ELBOW if elbow else MSO_CONNECTOR.STRAIGHT
    c = slide.shapes.add_connector(kind, 0, 0, 0, 0)
    c.name = name
    c.begin_connect(a, sites[a_side])
    c.end_connect(b, sites[b_side])
    _no_style(c)
    c.line.color.rgb = rgb(color)
    c.line.width = Pt(w)
    if dash:
        c.line.dash_style = MSO_LINE.DASH
    _ends(c, head=head, tail=tail)
    return c


def polyline(slide, pts, color="muted", w=1.5, dash=False, tail=True, name="path"):
    """Open polyline (inches) with an optional arrow head, for feedback paths and loops."""
    e = [(int(Inches(px)), int(Inches(py))) for px, py in pts]
    fb = slide.shapes.build_freeform(e[0][0], e[0][1], scale=1.0)
    fb.add_line_segments(e[1:], close=False)
    shp = fb.convert_to_shape()
    shp.name = name
    _no_style(shp)
    shp.fill.background()
    shp.line.color.rgb = rgb(color)
    shp.line.width = Pt(w)
    if dash:
        shp.line.dash_style = MSO_LINE.DASH
    _ends(shp, tail=tail)
    return shp


def label(slide, x, y, w, txt, size=10.5, color="muted", align="c", mono=True, bold=False, h=0.22, fill=None, name=None):
    """Small caption (edge label, axis label). Optional opaque fill masks a line passing behind it."""
    tb = text(slide, x, y, w, h, [txt], size=size, color=color, font=MONO if mono else BODY, bold=bold, align=align,
              anchor="m", wrap=False, lint=False, name=name or f"label: {txt}")
    if fill:
        tb.fill.solid()
        tb.fill.fore_color.rgb = rgb(fill)
    return tb


# ---------------------------------------------------------------- icons
ICON_DIR = Path(__file__).resolve().parent / "assets" / "icons"
ICON_COLORS = {"amber", "azure", "ink", "muted", "success", "white"}
_icon_index: dict = {}


def _scan_icons() -> int:
    _icon_index.clear()
    n = 0
    for p in ICON_DIR.rglob("*.png"):
        parts = p.relative_to(ICON_DIR).parts
        col = parts[-2] if len(parts) >= 2 and parts[-2] in ICON_COLORS else ""
        _icon_index[(p.stem.lower(), col)] = p
        n += 1
    return n


def _lookup_icon(n: str, color: str):
    for key in ((n, color), (n, ""), (n, "azure")):
        if key in _icon_index:
            return _icon_index[key]
    return next((p for (nm, _), p in _icon_index.items() if nm == n), None)


def icon_file(name: str, color: str = "azure"):
    """PNG for a Lucide-style icon (png/<color>/<name>.png) or a colourless product icon (microsoft/<name>.png).
    The index is rebuilt once on a miss, so a library that is still being generated is picked up."""
    n = name.lower()
    if not _icon_index:
        _scan_icons()
    hit = _lookup_icon(n, color)
    if hit is None and ICON_DIR.exists() and sum(1 for _ in ICON_DIR.rglob("*.png")) != len(_icon_index):
        _scan_icons()
        hit = _lookup_icon(n, color)
    return hit

def mark_decorative(shape) -> None:
    c_nv = shape._element.xpath(".//p:cNvPr")[0]
    ext_lst = etree.SubElement(c_nv, qn("a:extLst"))
    ext = etree.SubElement(ext_lst, qn("a:ext"), uri="{C183D7F6-B498-43B3-948B-1728B52AA6E4}")
    etree.SubElement(ext, "{http://schemas.microsoft.com/office/drawing/2017/decorative}decorative",
                     nsmap={"adec": "http://schemas.microsoft.com/office/drawing/2017/decorative"}, val="1")


def add_icon(slide, name, x, y, size=0.36, color="azure", alt=None):
    f = icon_file(name, color)
    if f is None:
        LINT.append(f"[{CTX['slide']}] missing icon '{name}' ({color})")
        shp = box(slide, x, y, size, size, tone="amber", radius=size / 2, name=f"missing icon: {name}")
        return shp
    pic = slide.shapes.add_picture(str(f), Inches(x), Inches(y), width=Inches(size))
    pic.name = f"icon: {name}"
    if alt:
        pic._element.xpath(".//p:cNvPr")[0].set("descr", alt)
    else:
        mark_decorative(pic)
    return pic