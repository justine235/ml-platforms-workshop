"""Presentation factory: 16:9 canvas, deck theme (colors + fonts) and a tidy master.

New slides added by hand in PowerPoint then inherit the same identity as the generated ones.
"""
from __future__ import annotations

import re

from pptx import Presentation
from pptx.enum.text import MSO_ANCHOR
from pptx.opc.constants import RELATIONSHIP_TYPE as RT
from pptx.oxml.ns import qn
from pptx.util import Emu, Inches

from deck_core import BODY, BODY_TOP, CW, HEAD, MX, PAL

TITLE_BOX = (MX, 0.66, CW, 1.05)
KEEP_LAYOUTS = {"Title Slide", "Title and Content", "Section Header", "Title Only", "Blank"}


def _patch_theme(prs) -> None:
    part = prs.slide_master.part.part_related_by(RT.THEME)
    xml = part.blob.decode("utf-8")
    colors = dict(dk1=PAL["ink"], lt1="FFFFFF", dk2=PAL["muted"], lt2=PAL["azure_soft"], accent1=PAL["azure"],
                  accent2=PAL["amber"], accent3=PAL["success"], accent4=PAL["sand"], accent5=PAL["amber_line"],
                  accent6=PAL["azure_line"], hlink=PAL["azure"], folHlink=PAL["muted"])
    for tag, val in colors.items():
        xml = re.sub(rf"<a:{tag}>.*?</a:{tag}>", f'<a:{tag}><a:srgbClr val="{val}"/></a:{tag}>', xml, count=1, flags=re.S)
    xml = xml.replace('<a:majorFont><a:latin typeface="Calibri"/>', f'<a:majorFont><a:latin typeface="{HEAD}"/>')
    xml = xml.replace('<a:minorFont><a:latin typeface="Calibri"/>', f'<a:minorFont><a:latin typeface="{BODY}"/>')
    xml = re.sub(r'<a:theme ([^>]*)name="[^"]*"', r'<a:theme \1name="Workshop"', xml, count=1)
    part._blob = xml.encode("utf-8")


def _place(shape, box_in) -> None:
    x, y, w, h = box_in
    shape.left, shape.top, shape.width, shape.height = Inches(x), Inches(y), Inches(w), Inches(h)


def _patch_master(prs) -> None:
    master = prs.slide_master
    tx = master.element.find(qn("p:txStyles"))
    lvl = tx.find(qn("p:titleStyle")).find(qn("a:lvl1pPr"))
    lvl.set("algn", "l")
    lvl.find(qn("a:defRPr")).set("sz", "3000")
    lvl.find(qn("a:defRPr")).set("b", "1")
    body = tx.find(qn("p:bodyStyle"))
    for i, size in enumerate((2000, 1800, 1600, 1400, 1400), start=1):
        node = body.find(qn(f"a:lvl{i}pPr"))
        if node is not None:
            node.find(qn("a:defRPr")).set("sz", str(size))
    for ph in master.placeholders:
        kind = ph.placeholder_format.type
        if "TITLE" in str(kind):
            _place(ph, TITLE_BOX)
            tf = ph.text_frame
            tf.vertical_anchor = MSO_ANCHOR.TOP
            tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
        elif "BODY" in str(kind) or "OBJECT" in str(kind):
            _place(ph, (MX, BODY_TOP, CW, 4.9))


def new_presentation() -> Presentation:
    prs = Presentation()
    k = 12192000 / prs.slide_width
    prs.slide_width, prs.slide_height = Emu(12192000), Emu(6858000)
    for layout in list(prs.slide_layouts):
        if layout.name not in KEEP_LAYOUTS:
            prs.slide_layouts.remove(layout)
    shapes = list(prs.slide_master.shapes) + [s for lay in prs.slide_layouts for s in lay.shapes]
    for shp in shapes:
        left, top, width, height = shp.left, shp.top, shp.width, shp.height
        shp.left, shp.top, shp.width, shp.height = int(left * k), top, int(width * k), height
    _patch_theme(prs)
    _patch_master(prs)
    for layout in prs.slide_layouts:
        if layout.name == "Title Only":
            for ph in layout.placeholders:
                if "TITLE" in str(ph.placeholder_format.type):
                    _place(ph, TITLE_BOX)
    return prs


def layout_by_name(prs, name: str):
    return next(lay for lay in prs.slide_layouts if lay.name == name)
