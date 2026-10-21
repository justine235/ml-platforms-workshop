"""Deck: one method per slide layout. Every slide gets a real title, an eyebrow, a footer and speaker notes."""
from __future__ import annotations

import re
import uuid
from dataclasses import dataclass
from pathlib import Path

from lxml import etree
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Inches

from deck_core import (BODY, CTX, CW, HEAD, LINT, MONO, MX, PAL, SLIDE_H, SLIDE_W, TONES, add_icon, arrow, box, card,
                       card_need, est_height, fill_text, label, lines_needed, link, num_badge, pill, polyline, rgb,
                       text, text_w)
from deck_theme import layout_by_name, new_presentation
from deck_widgets import bar_chart, code_block, table

FOOTER = "Machine learning on Microsoft  \u00b7  Fabric, Azure Machine Learning and Foundry"
PARTS = {
    "O": ("WORKSHOP", 20),
    "P1": ("PART 1  \u00b7  FABRIC VS AZURE ML", 90),
    "P2": ("PART 2  \u00b7  MLOPS CONCEPTS", 75),
    "P3": ("PART 3  \u00b7  END-TO-END DEMO", 115),
    "P4": ("PART 4  \u00b7  FOUNDRY AND DATA AGENT", 75),
    "C": ("WRAP-UP", 15),
    "A": ("APPENDIX", None),
}
TRACK = [("P1", "PLATFORMS"), ("P2", "MLOPS"), ("P3", "DEMO"), ("P4", "AGENTS")]


@dataclass
class Frame:
    s: object
    x: float
    y: float
    w: float
    h: float

    @property
    def r(self):
        return self.x + self.w

    @property
    def b(self):
        return self.y + self.h


def _field_number(slide):
    tb = slide.shapes.add_textbox(Inches(SLIDE_W - MX - 1.0), Inches(7.06), Inches(1.0), Inches(0.24))
    tb.name = "footer-number"
    tf = tb.text_frame
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.RIGHT
    fld = etree.SubElement(p._p, qn("a:fld"), id="{" + str(uuid.uuid4()).upper() + "}", type="slidenum")
    rpr = etree.SubElement(fld, qn("a:rPr"), lang="en-US", sz="1000")
    etree.SubElement(etree.SubElement(rpr, qn("a:solidFill")), qn("a:srgbClr"), val=PAL["muted"])
    etree.SubElement(rpr, qn("a:latin"), typeface=BODY)
    etree.SubElement(fld, qn("a:t")).text = "\u2039#\u203a"


class Deck:
    def __init__(self):
        self.prs = new_presentation()
        self.layout = layout_by_name(self.prs, "Title Only")
        self.index: list[dict] = []

    # ------------------------------------------------------------ scaffold
    def _new(self, sid, title, kind, eyebrow=None, notes="", minutes=1.0, core=True, takeaway=None, source=None,
             footer="full", title_box=None, title_size=None, title_color="ink", eyebrow_color="azure"):
        CTX["slide"] = sid
        if any(r["id"] == sid for r in self.index):
            raise ValueError(f"duplicate slide id {sid}")
        slide = self.prs.slides.add_slide(self.layout)
        part = re.match(r"(P\d|O|C|A)", sid).group(1)
        ph = slide.shapes.title
        ph.name = "title"
        lines = 1
        if title_box:
            size = title_size or 40
            ph.left, ph.top, ph.width, ph.height = (Inches(v) for v in title_box)
            lines = lines_needed(title, title_box[2], HEAD, size, True)
        else:
            for size in (30, 28, 26, 24):
                lines = lines_needed(title, CW, HEAD, size, True)
                if lines <= 2:
                    break
            else:
                LINT.append(f"[{sid}] title is longer than 2 lines: {title[:60]}")
            ph.left, ph.top, ph.width = Inches(MX), Inches(0.66), Inches(CW)
            ph.height = Inches(0.55 if lines == 1 else 1.05)
        fill_text(ph.text_frame, [title], size=size, color=title_color, font=HEAD, bold=True, margins=(0, 0, 0, 0),
                  anchor="t")
        if kind not in ("title", "section"):
            text(slide, MX, 0.36, CW, 0.24, [eyebrow or PARTS[part][0]], size=11, color=eyebrow_color, font=MONO,
                 bold=True, track=1.2, anchor="m", wrap=False, lint=False, name="eyebrow")
        if footer == "full":
            arrow(slide, MX, 7.0, MX + CW, 7.0, color="line", w=0.75, tail=False, name="footer-rule")
            text(slide, MX, 7.06, 9.0, 0.24, [FOOTER], size=10, color="muted", anchor="m", wrap=False, lint=False,
                 name="footer-left")
        if footer in ("full", "num"):
            _field_number(slide)
        header = f"[{sid}  \u00b7  ~{minutes:g} min  \u00b7  {'CORE' if core else 'OPTIONAL'}]"
        slide.notes_slide.notes_text_frame.text = f"{header}\n\n{notes.strip()}" if notes.strip() else header
        self.index.append(dict(id=sid, title=title, kind=kind, minutes=minutes, core=core, part=part))
        top = (1.55 if lines == 1 else 1.85) if not title_box else 1.85
        bottom = 6.78
        if takeaway:
            bottom = 6.0
            bar = box(slide, MX, 6.14, CW, 0.5, tone="azure", radius=0.1, name="takeaway bar")
            pill(slide, MX + 0.16, 6.27, "Takeaway", tone="solid", size=10, h=0.24, name="takeaway tag")
            tsize = 16 if lines_needed(takeaway, CW - 1.6, BODY, 16) <= 1 else 14.5
            text(slide, MX + 1.45, 6.14, CW - 1.65, 0.5, [takeaway], size=tsize, anchor="m", name="takeaway text")
        if source:
            text(slide, MX, 6.72, CW, 0.2, [source], size=10, color="muted", anchor="m", wrap=False, lint=False,
                 name="source")
            bottom = min(bottom, 6.6)
        return Frame(slide, MX, top, CW, bottom - top)

    # ------------------------------------------------------------ opening
    def title_slide(self, sid, title, subtitle, meta, platforms, notes="", minutes=1):
        f = self._new(sid, title, "title", notes=notes, minutes=minutes, footer=None, title_box=(MX, 1.7, 7.6, 2.4),
                      title_size=44)
        s = f.s
        text(s, MX, 1.15, 7.3, 0.3, ["WORKSHOP  \u00b7  DATA SCIENCE AND DATA ENGINEERING"], size=12, color="azure",
             font=MONO, bold=True, track=1.2, anchor="m", wrap=False, lint=False, name="eyebrow")
        text(s, MX, 4.3, 7.3, 1.2, [subtitle], size=20, color="muted", name="subtitle")
        text(s, MX, 6.55, 7.3, 0.3, [meta], size=12, color="muted", font=MONO, anchor="m", wrap=False, lint=False,
             name="meta")
        x0, cw, ch, gap, y0 = 8.45, 4.35, 1.35, 0.3, 1.2
        for i, (icon, name, sub) in enumerate(platforms):
            y = y0 + i * (ch + gap)
            box(s, x0, y, cw, ch, tone="node", radius=0.14, name=f"platform tile: {name}")
            add_icon(s, icon, x0 + 0.25, y + (ch - 0.62) / 2, 0.62, color="azure")
            text(s, x0 + 1.1, y + 0.2, cw - 1.2, 0.4, [name], size=18, bold=True, font=HEAD, anchor="m",
                 name=f"platform name: {name}")
            text(s, x0 + 1.1, y + 0.66, cw - 1.2, 0.52, [sub], size=13.5, color="muted", name=f"platform sub: {name}")
            if i < len(platforms) - 1:
                arrow(s, x0 + cw / 2, y + ch, x0 + cw / 2, y + ch + gap, color="sand", w=1.5, tail=False,
                      name="platform thread")
        return f

    def section(self, sid, part_no, title, subtitle, goals, when, notes="", minutes=1, label=None, track_part=None,
                goals_label="WHAT YOU WILL LEAVE WITH"):
        """Divider. part_no: a digit -> huge part number; any other string -> an icon name drawn large instead.
        label: small caption above the number (default PART for numbers, CHAPTER for icons).
        track_part: part highlighted in the progress track (default: part_no when numeric, else none)."""
        numeric = str(part_no).isdigit()
        label = label or ("PART" if numeric else "CHAPTER")
        if track_part is None and numeric:
            track_part = int(part_no)
        f = self._new(sid, title, "section", notes=notes, minutes=minutes, footer="num", title_box=(5.4, 1.45, 7.4, 1.4),
                      title_size=38)
        s = f.s
        box(s, 0, 0, 4.6, SLIDE_H, tone="solid", shape=MSO_SHAPE.RECTANGLE, name="bleed panel")
        text(s, 0.6, 1.5, 3.4, 0.3, [label], size=16, color="azure_line", font=MONO, bold=True, track=3, wrap=False,
             lint=False, name="section label")
        if numeric:
            text(s, 0.5, 1.9, 3.6, 2.9, [str(part_no)], size=170, color="white", font=HEAD, bold=True, wrap=False,
                 lint=False, name="section number")
        else:
            add_icon(s, part_no, 0.62, 2.35, 2.3, color="white")
        text(s, 0.6, 6.0, 3.6, 0.3, [when[0]], size=16, color="white", font=MONO, bold=True, wrap=False, lint=False,
             name="section time")
        text(s, 0.6, 6.35, 3.6, 0.3, [when[1]], size=14, color="azure_line", wrap=False, lint=False,
             name="section length")
        text(s, 5.4, 3.0, 7.4, 0.9, [subtitle], size=20, color="muted", name="section subtitle")
        text(s, 5.4, 4.15, 7.4, 0.3, [goals_label], size=11, color="azure", font=MONO, bold=True,
             track=1.2, wrap=False, lint=False, name="goals heading")
        y = 4.55
        for g in goals:
            add_icon(s, "check-circle", 5.4, y + 0.02, 0.3, color="azure")
            text(s, 5.85, y, 6.9, 0.36, [g], size=17, anchor="m", name=f"goal: {g[:30]}")
            y += 0.46
        if track_part is None:
            return f
        x, seg = 5.4, 1.72
        for key, lab in TRACK:
            cur = int(key[1]) == track_part
            done = int(key[1]) < track_part
            box(s, x, 6.45, seg, 0.09, tone="solid" if cur else "node", radius=0.045, line_w=0.5,
                fill_color="azure" if cur else ("sand" if done else "line"), line_color="azure" if cur else ("sand" if done else "line"),
                name=f"progress {key}")
            text(s, x, 6.6, seg, 0.24, [f"{key}  {lab}"], size=10.5, color="azure" if cur else "muted", font=MONO,
                 bold=cur, wrap=False, lint=False, name=f"progress label {key}")
            x += seg + 0.12
        return f

    def agenda(self, sid, title, rows, notes="", minutes=1, takeaway=None, **kw):
        """rows: (time, title, desc, minutes_label, kind) with kind in part/talk/break."""
        f = self._new(sid, title, "agenda", notes=notes, minutes=minutes, takeaway=takeaway, **kw)
        s = f.s
        heights = [0.64 if r[4] != "break" else 0.36 for r in rows]
        gap = 0.07
        scale = min(1.0, (f.h - gap * (len(rows) - 1)) / sum(heights))
        y = f.y
        for (when, name, desc, mins, kind), h in zip(rows, heights):
            h *= scale
            if kind == "break":
                text(s, f.x + 0.2, y, 2.0, h, [when], size=12.5, color="muted", font=MONO, anchor="m", wrap=False,
                     lint=False, name=f"time: {name}")
                text(s, f.x + 2.3, y, 6.0, h, [f"{name}  \u00b7  {desc}" if desc else name], size=13.5, color="muted",
                     italic=True, anchor="m", wrap=False, lint=False, name=f"break: {name}")
            else:
                tone = "azure" if kind == "part" else "node"
                box(s, f.x, y, f.w, h, tone=tone, radius=0.1, name=f"row: {name}")
                text(s, f.x + 0.2, y, 2.0, h, [when], size=13.5, color="azure", font=MONO, bold=True, anchor="m",
                     wrap=False, lint=False, name=f"time: {name}")
                text(s, f.x + 2.3, y + 0.02, 8.0, h - 0.04, [dict(text=name, size=16, bold=True, font=HEAD),
                                                             dict(text=desc, size=13, color="muted")], anchor="m",
                     name=f"agenda: {name}")
                pill(s, f.r - 0.2, y + (h - 0.28) / 2, mins, tone="solid" if kind == "part" else "azure", size=10.5,
                     h=0.28, right=True, name=f"minutes: {name}")
            y += h + gap
        return f

    # ------------------------------------------------------------ content layouts
    @staticmethod
    def _item(i):
        keys = ("lead", "text", "icon")
        if isinstance(i, str):
            return {k: None for k in keys} | {"lead": i}
        if isinstance(i, (tuple, list)):
            return {k: None for k in keys} | dict(zip(keys, i))
        return {k: None for k in keys} | dict(i)

    def _stack(self, s, x, y, w, h, items, gap=0.2, title_size=16, body_size=14, max_extra=None):
        """Vertical stack of cards that fills the given height (extra space is shared between the cards,
        at most `max_extra` inches per card when given)."""
        needs = [card_need(w, i.get("title"), i.get("body"), title_size, body_size, icon=bool(i.get("icon")))
                 for i in items]
        if sum(needs) + gap * (len(items) - 1) > h + 0.04:
            LINT.append(f"[{CTX['slide']}] side stack needs {sum(needs) + gap * (len(items) - 1):.2f} in, has {h:.2f} in")
        extra = max(0.0, (h - sum(needs) - gap * (len(items) - 1)) / len(items))
        if max_extra is not None:
            extra = min(extra, max_extra)
        for it, need in zip(items, needs):
            card(s, x, y, w, need + extra, it.get("title"), it.get("body"), icon=it.get("icon"),
                 tone=it.get("tone", "node"), title_size=title_size, body_size=body_size)
            y += need + extra + gap

    def bullets(self, sid, title, items, visual=None, visual_w=4.9, lead_size=None, text_size=None, notes="",
                minutes=1, **kw):
        """Rows of 'lead + supporting line' with an optional icon. items: str | (lead, text, icon) | dict.
        Sizes are picked automatically (largest that fits) unless given."""
        f = self._new(sid, title, "bullets", notes=notes, minutes=minutes, **kw)
        s = f.s
        tw = f.w - ((visual_w + 0.5) if visual else 0)
        rows = [self._item(i) for i in items]

        def build(lead, txt):
            specs = []
            for r in rows:
                ps = [dict(text=r["lead"], size=lead, bold=True, font=HEAD, after=2)]
                if r["text"]:
                    ps.append(dict(text=r["text"], size=txt, color="muted"))
                specs.append(ps)
            return specs, [est_height(ps, tw - 0.7) for ps in specs]

        cands = [(lead_size, text_size)] if lead_size else [(23, 18), (22, 17), (21, 16.5), (20, 16), (19, 16), (18, 15)]
        for lead, txt in cands:
            specs, heights = build(lead, txt)
            if sum(heights) + 0.22 * (len(rows) - 1) <= f.h * 0.94:
                break
        gap = min(0.42, max(0.12, (f.h * 0.9 - sum(heights)) / max(1, len(rows) - 1)))
        total = sum(heights) + gap * (len(rows) - 1)
        if total > f.h + 0.04:
            LINT.append(f"[{sid}] bullets need {total:.2f} in, have {f.h:.2f} in")
        y = f.y + max(0.0, min(0.35, (f.h - total) * 0.4))
        for r, ps, h in zip(rows, specs, heights):
            if r["icon"]:
                add_icon(s, r["icon"], f.x, y + 0.02, 0.42, color="azure")
            else:
                box(s, f.x + 0.1, y + 0.1, 0.15, 0.15, tone="solid", shape=MSO_SHAPE.OVAL, name="bullet dot")
            text(s, f.x + 0.7, y, tw - 0.7, h + 0.02, ps, name=f"bullet: {r['lead'][:30]}")
            y += h + gap
        if visual:
            visual(s, f.r - visual_w, f.y, visual_w, f.h)
        return f

    def cards(self, sid, title, items, cols=None, icon_pos="top", max_h=None, min_h=2.4, numbered=False,
              title_size=None, body_size=None, notes="", minutes=1, gap=0.25, tone=None, **kw):
        """Grid of cards. items: dict(title, body, icon, tone). Text sizes are picked automatically (largest that
        fits) and the grid is centred in the body area instead of stretching to it."""
        f = self._new(sid, title, "cards", notes=notes, minutes=minutes, **kw)
        s = f.s
        n = len(items)
        cols = cols or (n if n <= 4 else 3)
        rows = -(-n // cols)
        cw = (f.w - gap * (cols - 1)) / cols
        avail = (f.h - gap * (rows - 1)) / rows

        def needs_for(ts, bs):
            return [card_need(cw, i.get("title"), i.get("body"), ts, bs, icon=bool(i.get("icon")),
                              icon_pos=icon_pos, badge=numbered) for i in items]

        cands = [(title_size, body_size)] if title_size else [(21, 16.5), (20, 16), (19, 15.5), (18, 15), (17, 14.5),
                                                              (16, 14)]
        for ts, bs in cands:
            needs = needs_for(ts, bs)
            if max(needs) <= avail:
                break
        ch = min(avail, max_h or 99, max(min_h, max(needs) + 0.25))
        grid_h = ch * rows + gap * (rows - 1)
        y0 = f.y + (f.h - grid_h) * 0.4
        for k, it in enumerate(items):
            r, c = divmod(k, cols)
            card(s, f.x + c * (cw + gap), y0 + r * (ch + gap), cw, ch, it.get("title"), it.get("body"),
                 icon=it.get("icon"), tone=it.get("tone", tone or "node"), title_size=ts, body_size=bs,
                 icon_pos=icon_pos, badge=(k + 1) if numbered else None)
        return f

    def compare(self, sid, title, left, right, notes="", minutes=1, vs=True, item_size=None, **kw):
        """Two panels. left/right: dict(title, sub, icon, tone, items=[str])."""
        f = self._new(sid, title, "compare", notes=notes, minutes=minutes, **kw)
        s = f.s
        gap, head_h = 0.5, 0.95
        pw = (f.w - gap) / 2

        def need_for(sz):
            return max(est_height([dict(text=t, bullet=True, after=10) for t in side["items"]], pw - 0.6, size=sz)
                       for side in (left, right))

        sizes = [item_size] if item_size else [20, 19, 18, 17, 16, 15]
        for item_size in sizes:
            need = need_for(item_size)
            if head_h + 0.25 + need + 0.35 <= f.h:
                break
        ph = min(f.h, max(3.6, head_h + 0.25 + need + 0.45))
        y0 = f.y + (f.h - ph) * 0.35
        for k, side in enumerate((left, right)):
            x = f.x + k * (pw + gap)
            tone = side.get("tone", "azure" if k == 0 else "amber")
            box(s, x, y0, pw, ph, tone="paper", radius=0.14, name=f"panel: {side['title']}")
            box(s, x, y0, pw, head_h, tone=tone, radius=0.14, shape=MSO_SHAPE.ROUND_2_SAME_RECTANGLE,
                name=f"panel header: {side['title']}")
            tx = x + 0.3
            if side.get("icon"):
                add_icon(s, side["icon"], x + 0.25, y0 + 0.2, 0.55, color=TONES[tone]["accent"])
                tx = x + 1.0
            text(s, tx, y0 + 0.14, pw - (tx - x) - 0.2, 0.4, [side["title"]], size=21, bold=True, font=HEAD,
                 anchor="m", name=f"panel title: {side['title']}")
            if side.get("sub"):
                text(s, tx, y0 + 0.54, pw - (tx - x) - 0.2, 0.3, [side["sub"]], size=14, color="muted", anchor="m",
                     name=f"panel sub: {side['title']}")
            paras = [dict(text=t, bullet=True, after=10, bullet_color=TONES[tone]["accent"]) for t in side["items"]]
            text(s, x + 0.3, y0 + head_h + 0.25, pw - 0.6, ph - head_h - 0.35, paras, size=item_size,
                 name=f"panel items: {side['title']}")
        if vs:
            num_badge(s, f.x + pw + gap / 2 - 0.25, y0 + head_h / 2 - 0.25, "vs", tone="muted", size=0.5, fsize=12,
                      name="vs")
        return f

    def stats(self, sid, title, items, cols=None, notes="", minutes=1, gap=0.25, max_h=3.3, **kw):
        """Big-number cards. items: dict(value, label, sub, tone)."""
        f = self._new(sid, title, "stat", notes=notes, minutes=minutes, **kw)
        s = f.s
        n = len(items)
        cols = cols or min(n, 4)
        rows = -(-n // cols)
        cw = (f.w - gap * (cols - 1)) / cols
        ch = min(max_h, (f.h - gap * (rows - 1)) / rows)
        y0 = f.y + (f.h - (ch * rows + gap * (rows - 1))) * 0.4
        vsize = 48
        while vsize > 28 and max(text_w(it["value"], HEAD, vsize, True) for it in items) * 1.1 > cw - 0.6:
            vsize -= 2
        for k, it in enumerate(items):
            r, c = divmod(k, cols)
            tone = it.get("tone", "azure")
            body = [dict(text=it["label"], size=17, bold=True, after=3)]
            if it.get("sub"):
                body.append(dict(text=it["sub"], size=14, color="muted"))
            card(s, f.x + c * (cw + gap), y0 + r * (ch + gap), cw, ch, it["value"], body, tone=tone, title_size=vsize,
                 title_color=TONES[tone]["accent"], pad=0.25, name=f"stat: {it['value']}")
        return f

    def callout(self, sid, title, statement, support=None, tone="azure", size=30, notes="", minutes=1, **kw):
        """One big statement, optionally followed by up to three small supporting cards."""
        f = self._new(sid, title, "callout", notes=notes, minutes=minutes, **kw)
        s = f.s
        sh = 2.2 if support else min(f.h, 3.4)
        y0 = f.y + (0 if support else (f.h - sh) / 2)
        box(s, f.x, y0, f.w, sh, tone=tone, radius=0.16, name="callout panel")
        text(s, f.x + 0.5, y0 + 0.2, f.w - 1.2, sh - 0.4, [statement], size=size, bold=True, font=HEAD, anchor="m",
             name="callout statement", color="ink")
        if support:
            n = len(support)
            gap = 0.25
            cw = (f.w - gap * (n - 1)) / n
            ch = min(f.h - sh - 0.3, 2.3)
            for k, it in enumerate(support):
                card(s, f.x + k * (cw + gap), y0 + sh + 0.3, cw, ch, it.get("title"), it.get("body"),
                     icon=it.get("icon"), tone=it.get("tone", "node"), icon_pos="inline", title_size=18, body_size=15)
        return f

    def recap(self, sid, title, points, question=None, notes="", minutes=1, **kw):
        """Numbered takeaways plus an optional question for the room."""
        f = self._new(sid, title, "recap", notes=notes, minutes=minutes, **kw)
        s = f.s
        n, gap = len(points), 0.3
        cw = (f.w - gap * (n - 1)) / n
        qh = 0.85 if question else 0.0
        avail = f.h - (qh + 0.3 if question else 0.0)
        need = max(card_need(cw, p["title"], p.get("body"), 21, 16, pad=0.22, badge=True) for p in points)
        ch = min(avail, max(2.6, need + 0.3))
        y0 = f.y + (avail - ch) * 0.4
        for k, p in enumerate(points):
            card(s, f.x + k * (cw + gap), y0, cw, ch, p["title"], p.get("body"), tone=p.get("tone", "azure"),
                 badge=k + 1, title_size=21, body_size=16, pad=0.22)
        if question:
            y = f.b - qh
            box(s, f.x, y, f.w, qh, tone="amber", radius=0.12, name="question bar")
            pill(s, f.x + 0.2, y + (qh - 0.28) / 2, "Question for the room", tone="amber_solid", size=10, h=0.28,
                 name="question tag")
            text(s, f.x + 2.75, y, f.w - 2.95, qh, [question], size=17, bold=True, anchor="m", name="question text")
        return f

    def discuss(self, sid, title, questions, when="5 min", notes="", minutes=5, **kw):
        """Discussion prompts as large amber cards. questions: str | dict(title, body)."""
        items = [dict(title=q, tone="amber") if isinstance(q, str) else dict(q, tone="amber") for q in questions]
        f = self.cards(sid, title, items, cols=len(items), numbered=True, min_h=2.6, title_size=23, body_size=16,
                       notes=notes, minutes=minutes, eyebrow=f"DISCUSS  \u00b7  {when.upper()}",
                       eyebrow_color="amber", **kw)
        return f

    def table_slide(self, sid, title, header, rows, col_w=None, size=None, side=None, side_w=3.8, tbl=None, notes="",
                    minutes=1, **kw):
        """Native table. size=None picks the largest text size that fits the body area."""
        f = self._new(sid, title, "table", notes=notes, minutes=minutes, **kw)
        tw = f.w - ((side_w + 0.35) if side else 0)
        opts = dict(tbl or {})
        if size:
            opts["size"] = size
        else:
            opts["fit"] = (19, 18, 17, 16, 15, 14, 13, 12.5)
        _, th = table(f.s, f.x, f.y, tw, header, rows, col_w=col_w, max_bottom=f.b, **opts)
        if side:
            self._stack(f.s, f.r - side_w, f.y, side_w, max(th, min(f.h, 3.4)), side)
        return f

    def chart_slide(self, sid, title, cats, series, side=None, side_w=4.2, fmt="0.00", chart=None, notes="", minutes=1,
                    **kw):
        f = self._new(sid, title, "chart", notes=notes, minutes=minutes, **kw)
        cw = f.w - ((side_w + 0.4) if side else 0)
        bar_chart(f.s, f.x, f.y, cw, f.h, cats, series, fmt=fmt, **(chart or {}))
        if side:
            self._stack(f.s, f.r - side_w, f.y, side_w, f.h, side)
        return f

    def code_slide(self, sid, title, code, lang="python", file=None, side=None, hl=(), code_w=None, size=None,
                   dark=False, notes="", minutes=1, **kw):
        """Code block (+ optional side cards). size=None picks the largest Consolas size that fits."""
        f = self._new(sid, title, "code", notes=notes, minutes=minutes, **kw)
        lines = code.strip("\n").split("\n")
        cw = code_w or (7.6 if side else f.w)

        def need_h(sz):
            return (0.42 if file else 0.0) + 0.28 + len(lines) * sz * 1.34 / 72

        def fits(sz):
            return need_h(sz) <= f.h and max(text_w(ln, MONO, sz) for ln in lines) + 0.5 <= cw

        size = size or next((sz for sz in (18, 17, 16, 15, 14, 13, 12.5) if fits(sz)), 12.5)
        ph = min(f.h, max(need_h(size), 2.2))
        code_block(f.s, f.x, f.y, cw, ph, code, lang=lang, size=size, title=file, hl=hl, dark=dark)
        if side:
            self._stack(f.s, f.x + cw + 0.3, f.y, f.w - cw - 0.3, ph, side)
        return f

    def demo(self, sid, title, steps, prebaked, notice, when, where=None, notes="", minutes=10, **kw):
        """Live-demo cue card. steps: (text, minutes_label). prebaked / notice: lists of short strings."""
        f = self._new(sid, title, "demo", eyebrow=f"LIVE DEMO  \u00b7  {PARTS[re.match(r'(P\d|O|C|A)', sid).group(1)][0]}",
                      eyebrow_color="amber", notes=notes, minutes=minutes, **kw)
        s = f.s
        lw, rw = 7.0, f.w - 7.0 - 0.4
        pill(s, f.x, f.y, f"Live demo  \u00b7  {when}", tone="amber", size=11, h=0.32)
        y = f.y + 0.5
        if where:
            text(s, f.x, y, lw, 0.3, [where], size=12.5, color="muted", font=MONO, anchor="m", wrap=False, lint=False,
                 name="demo where")
            y += 0.45
        gap = 0.12
        rh = min(0.78, (f.b - y - gap * (len(steps) - 1)) / len(steps))
        for k, (txt, mins) in enumerate(steps):
            box(s, f.x, y, lw, rh, tone="node", radius=0.1, name=f"step {k + 1}")
            num_badge(s, f.x + 0.16, y + (rh - 0.36) / 2, k + 1, tone="amber")
            text(s, f.x + 0.7, y, lw - 1.95, rh, [txt], size=15.5, anchor="m", name=f"step text {k + 1}")
            text(s, f.x + lw - 1.2, y, 1.05, rh, [mins], size=12, color="amber", font=MONO, bold=True, align="r",
                 anchor="m", wrap=False, lint=False, name=f"step time {k + 1}")
            y += rh + gap
        self._stack(s, f.r - rw, f.y, rw, f.h, [
            dict(title="Pre-baked fallback", body=[dict(text=t, bullet=True) for t in prebaked], icon="shield-check", tone="node"),
            dict(title="What to notice", body=[dict(text=t, bullet=True) for t in notice], icon="eye", tone="success"),
        ], title_size=17, body_size=15, max_extra=0.5)
        return f

    def custom(self, sid, title, draw, kind="custom", notes="", minutes=1, **kw):
        f = self._new(sid, title, kind, notes=notes, minutes=minutes, **kw)
        draw(f)
        return f

    # ------------------------------------------------------------ diagrams
    def flow(self, sid, title, steps, back=None, numbered=False, title_size=None, body_size=None, gap=0.5, max_h=None,
             notes="", minutes=1, **kw):
        """Left-to-right steps joined by arrows. back: dict(label) draws a dashed return path under the cards."""
        f = self._new(sid, title, "flow", notes=notes, minutes=minutes, **kw)
        s = f.s
        n = len(steps)
        cw = (f.w - gap * (n - 1)) / n
        back_h = 0.8 if back else 0.0

        def needs_for(ts, bs):
            return [card_need(cw, st.get("title"), st.get("body"), ts, bs, icon=bool(st.get("icon")), icon_pos="top",
                              badge=numbered) for st in steps]

        cands = [(title_size, body_size)] if title_size else [(20, 16), (19, 15.5), (18, 15), (17, 14.5), (16, 14)]
        for ts, bs in cands:
            needs = needs_for(ts, bs)
            if max(needs) <= f.h - back_h:
                break
        ch = min(f.h - back_h, max_h or 99, max(2.4, max(needs) + 0.3))
        y0 = f.y + (f.h - back_h - ch) * 0.45
        shapes = []
        for k, st in enumerate(steps):
            shapes.append(card(s, f.x + k * (cw + gap), y0, cw, ch, st.get("title"), st.get("body"),
                               icon=st.get("icon"), tone=st.get("tone", "node"), title_size=ts, body_size=bs,
                               icon_pos="top", badge=(k + 1) if numbered else None))
        for a, b in zip(shapes, shapes[1:]):
            link(s, a, b, "r", "l", color="muted", w=1.75, name="flow arrow")
        if back:
            xa = f.x + (n - 1) * (cw + gap) + cw / 2
            xb = f.x + cw / 2
            yb = y0 + ch
            yl = yb + 0.5
            polyline(s, [(xa, yb + 0.03), (xa, yl), (xb, yl), (xb, yb + 0.04)], color="amber", w=1.75, dash=True,
                     name="return path")
            lab = back.get("label", "")
            lw = text_w(lab, MONO, 11, True) + 0.3
            label(s, (xa + xb) / 2 - lw / 2, yl - 0.14, lw, lab, size=11, color="amber", bold=True, fill="paper",
                  h=0.28, name="return label")
        return f

    @staticmethod
    def _hits(pts, rect, shrink=0.05):
        """True when an axis-aligned polyline crosses the inside of a node rectangle."""
        rx, ry, rw, rh = rect
        return any(min(xa, xb) < rx + rw - shrink and max(xa, xb) > rx + shrink
                   and min(ya, yb) < ry + rh - shrink and max(ya, yb) > ry + shrink
                   for (xa, ya), (xb, yb) in zip(pts, pts[1:]))

    @staticmethod
    def _route(ga, gb, sa, sb, pad=0.03):
        def anchor(g, side):
            x, y, w, h = g
            return {"l": (x, y + h / 2), "r": (x + w, y + h / 2), "t": (x + w / 2, y), "b": (x + w / 2, y + h)}[side]
        nudge = {"l": (-pad, 0), "r": (pad, 0), "t": (0, -pad), "b": (0, pad)}
        (x1, y1), (x2, y2) = anchor(ga, sa), anchor(gb, sb)
        x1, y1 = x1 + nudge[sa][0], y1 + nudge[sa][1]
        x2, y2 = x2 + nudge[sb][0], y2 + nudge[sb][1]
        if sa in "lr" and sb in "lr":
            if abs(y1 - y2) < 0.02:
                return [(x1, y1), (x2, y2)]
            mx = (x1 + x2) / 2
            return [(x1, y1), (mx, y1), (mx, y2), (x2, y2)]
        if sa in "tb" and sb in "tb":
            if abs(x1 - x2) < 0.02:
                return [(x1, y1), (x2, y2)]
            my = (y1 + y2) / 2
            return [(x1, y1), (x1, my), (x2, my), (x2, y2)]
        return [(x1, y1), (x2, y1), (x2, y2)] if sa in "lr" else [(x1, y1), (x1, y2), (x2, y2)]

    def arch(self, sid, title, nodes, edges=(), groups=(), gap=(0.55, 0.5), max_node_h=1.5, node_title=15,
             node_sub=12.5, notes="", minutes=1, **kw):
        """Grid diagram. nodes: dict(id,label,sub,icon,col,row,cspan,rspan,tone,h). edges: (a,b[,label]) or dict.
        groups: dict(label,c0,r0,c1,r1,tone) drawn as dashed labelled zones behind the nodes."""
        f = self._new(sid, title, "arch", notes=notes, minutes=minutes, **kw)
        s = f.s
        ncols = max(n["col"] + n.get("cspan", 1) for n in nodes)
        nrows = max(n["row"] + n.get("rspan", 1) for n in nodes)
        gx, gy = gap
        pad_top = 0.3 if groups else 0.0
        pad_bot = 0.2 if groups else 0.0
        inset = 0.2 if groups else 0.0
        cw = (f.w - 2 * inset - gx * (ncols - 1)) / ncols
        ch = min(max_node_h, (f.h - pad_top - pad_bot - gy * (nrows - 1)) / nrows)
        grid_h = ch * nrows + gy * (nrows - 1) + pad_top + pad_bot
        y0 = f.y + pad_top + max(0.0, (f.h - grid_h) / 2)

        def cell(c, r, cs=1, rs=1):
            return (f.x + inset + c * (cw + gx), y0 + r * (ch + gy), cs * cw + (cs - 1) * gx, rs * ch + (rs - 1) * gy)

        for g in groups:
            x, y, w, h = cell(g["c0"], g["r0"], g["c1"] - g["c0"] + 1, g["r1"] - g["r0"] + 1)
            tone = g.get("tone", "azure")
            box(s, x - 0.14, y - 0.16, w + 0.28, h + 0.32, tone=tone, radius=0.14, dash=True, filled=False, line_w=1.25,
                name=f"group: {g['label']}")
            pill(s, x - 0.02, y - 0.3, g["label"], tone=tone, size=10, h=0.26, name=f"group label: {g['label']}")
        geo = {}
        for nd in nodes:
            x, y, w, h = cell(nd["col"], nd["row"], nd.get("cspan", 1), nd.get("rspan", 1))
            if nd.get("h"):
                y, h = y + (h - nd["h"]) / 2, nd["h"]
            tone = nd.get("tone", "node")
            solid = tone == "solid"
            body = [dict(text=nd["sub"], size=node_sub, color="white" if solid else "muted")] if nd.get("sub") else None
            card(s, x, y, w, h, nd["label"], body, icon=nd.get("icon"), tone=tone, title_size=node_title,
                 body_size=node_sub, pad=0.14, icon_size=0.3, after=2, radius=0.1,
                 title_color="white" if solid else "ink", icon_color="white" if solid else None,
                 name=f"node: {nd['id']}")
            geo[nd["id"]] = (x, y, w, h)
        for e in edges:
            e = dict(a=e[0], b=e[1], label=e[2] if len(e) > 2 else None) if isinstance(e, (tuple, list)) else dict(e)
            ga, gb = geo[e["a"]], geo[e["b"]]
            overlap_x = ga[0] < gb[0] + gb[2] and gb[0] < ga[0] + ga[2]
            if "sa" not in e:
                if overlap_x:
                    e["sa"], e["sb"] = ("b", "t") if gb[1] > ga[1] else ("t", "b")
                else:
                    e["sa"], e["sb"] = ("r", "l") if gb[0] > ga[0] else ("l", "r")
            pts = self._route(ga, gb, e["sa"], e["sb"])
            for k, rect in geo.items():
                if k not in (e["a"], e["b"]) and self._hits(pts, rect):
                    LINT.append(f"[{sid}] arch edge {e['a']} -> {e['b']} runs through node '{k}'")
            color = e.get("color", "muted")
            if len(pts) == 2:
                arrow(s, *pts[0], *pts[1], color=color, w=1.75, dash=e.get("dash", False), name=f"edge {e['a']}-{e['b']}")
            else:
                polyline(s, pts, color=color, w=1.75, dash=e.get("dash", False), name=f"edge {e['a']}-{e['b']}")
            if e.get("label"):
                segs = list(zip(pts, pts[1:]))
                (xa, ya), (xb, yb) = max(segs, key=lambda sg: abs(sg[0][0] - sg[1][0]) + abs(sg[0][1] - sg[1][1]))
                lw = text_w(e["label"], MONO, 10.5, True) + 0.2
                if abs(xa - xb) < abs(ya - yb):
                    lx, ly = xa + 0.1, (ya + yb) / 2 - 0.12
                else:
                    lx, ly = (xa + xb) / 2 - lw / 2, ya - 0.32
                label(s, lx, ly, lw, e["label"], size=10.5, color=color, bold=True, fill="paper", h=0.24,
                      name=f"edge label: {e['label']}")
        return f

    def stairs(self, sid, title, steps, notes="", minutes=1, gap=0.2, title_size=19, body_size=15, **kw):
        """Ascending columns (maturity levels). steps: dict(tag, title, body, tone)."""
        f = self._new(sid, title, "ladder", notes=notes, minutes=minutes, **kw)
        s = f.s
        n = len(steps)
        cw = (f.w - gap * (n - 1)) / n
        needs = [card_need(cw, st["title"], st.get("body"), title_size, body_size) for st in steps]
        h_min = max(needs[0], 1.7)
        tones = ["node", "azure", "azure", "solid", "solid"][:n] if n <= 5 else ["azure"] * n
        for k, st in enumerate(steps):
            h = h_min + (f.h - 0.3 - h_min) * k / max(1, n - 1)
            tone = st.get("tone", tones[k])
            solid = tone == "solid"
            y = f.b - h
            card(s, f.x + k * (cw + gap), y, cw, h, st["title"], st.get("body"), tone=tone, title_size=title_size,
                 body_size=body_size, title_color="white" if solid else "ink", body_color="white" if solid else "ink",
                 pad=0.2)
            pill(s, f.x + k * (cw + gap) + 0.18, y - 0.13, st["tag"], tone="amber_solid" if solid else "azure",
                 size=10, h=0.26)
        return f

    def timeline(self, sid, title, events, notes="", minutes=1, block_w=3.8, **kw):
        """Dated markers on an axis, labels alternating above and below. events: dict(when,title,body,tone)."""
        f = self._new(sid, title, "timeline", notes=notes, minutes=minutes, **kw)
        s = f.s
        ay = f.y + f.h / 2
        arrow(s, f.x, ay, f.r, ay, color="sand", w=2.5, name="timeline axis")
        n = len(events)
        seg = f.w / n
        bh = f.h / 2 - 0.5
        for k, ev in enumerate(events):
            cx = f.x + seg * (k + 0.5)
            tone = ev.get("tone", "azure")
            accent = TONES[tone]["accent"]
            up = k % 2 == 0
            bw = min(block_w, seg * 1.9)
            paras = [dict(text=ev["when"], size=14, color=accent, font=MONO, bold=True, after=3),
                     dict(text=ev["title"], size=19, bold=True, font=HEAD, after=3)]
            if ev.get("body"):
                paras.append(dict(text=ev["body"], size=15, color="muted"))
            by = f.y + 0.05 if up else ay + 0.42
            text(s, cx - bw / 2, by, bw, bh, paras, align="c", anchor="b" if up else "t", name=f"event: {ev['title'][:24]}")
            arrow(s, cx, ay - 0.37 if up else ay + 0.11, cx, ay - 0.11 if up else ay + 0.37, color="sand", w=1.25,
                  tail=False, name="timeline stem")
            box(s, cx - 0.11, ay - 0.11, 0.22, 0.22, tone="solid", shape=MSO_SHAPE.OVAL, name="timeline dot",
                fill_color=accent, line_color="white", line_w=2)
        return f

    # ------------------------------------------------------------ output
    def minutes_report(self):
        rep = {}
        for r in self.index:
            d = rep.setdefault(r["part"], dict(core=0.0, optional=0.0, slides=0))
            d["core" if r["core"] else "optional"] += r["minutes"]
            d["slides"] += 1
        return rep

    def index_markdown(self):
        lines = ["# Slide index", "", "| # | id | layout | min | core | headline |", "|---|---|---|---|---|---|"]
        for i, r in enumerate(self.index, 1):
            lines.append(f"| {i} | {r['id']} | {r['kind']} | {r['minutes']:g} | {'yes' if r['core'] else 'optional'} | "
                         f"{r['title']} |")
        lines += ["", "## Minutes per part (core / optional vs agenda)", "", "| part | slides | core min | optional min | agenda |",
                  "|---|---|---|---|---|"]
        for part, d in self.minutes_report().items():
            lines.append(f"| {part} | {d['slides']} | {d['core']:g} | {d['optional']:g} | {PARTS[part][1] or '-'} |")
        return "\n".join(lines) + "\n"

    def save(self, path):
        path = Path(path)
        self.prs.save(str(path))
        (path.parent / "slide-index.md").write_text(self.index_markdown(), encoding="utf-8", newline="\n")
        return path
