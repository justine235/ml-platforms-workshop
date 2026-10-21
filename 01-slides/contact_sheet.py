"""Contact sheets from rendered slides (one image holds several slides, so a whole part can be reviewed quickly).

    python contact_sheet.py out\\dev\\content_p2\\render out\\dev\\content_p2\\sheet [--cols 2] [--rows 2] [--width 1800]

Reads s001.png, s002.png ... from the render folder and writes <prefix>_01.png, <prefix>_02.png ...
Tiles are labelled with the slide number and, when slide-index.md sits next to the render folder, the slide id.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def read_ids(index_md: Path) -> dict[int, str]:
    ids = {}
    if index_md.exists():
        for line in index_md.read_text(encoding="utf-8").splitlines():
            m = re.match(r"\|\s*(\d+)\s*\|\s*([A-Z0-9.]+)\s*\|", line)
            if m:
                ids[int(m.group(1))] = m.group(2)
    return ids


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("render_dir")
    ap.add_argument("out_prefix")
    ap.add_argument("--cols", type=int, default=2)
    ap.add_argument("--rows", type=int, default=2)
    ap.add_argument("--width", type=int, default=1800)
    a = ap.parse_args()

    rd = Path(a.render_dir)
    files = sorted(rd.glob("s[0-9]*.png"))
    if not files:
        raise SystemExit(f"no s###.png in {rd}")
    ids = read_ids(rd.parent / "slide-index.md")
    gap, label_h = 16, 30
    tile_w = (a.width - gap * (a.cols + 1)) // a.cols
    first = Image.open(files[0])
    tile_h = round(tile_w * first.height / first.width)
    font = ImageFont.truetype(r"C:\Windows\Fonts\consolab.ttf", 20)
    per = a.cols * a.rows
    for sheet_no, start in enumerate(range(0, len(files), per), 1):
        chunk = files[start:start + per]
        rows = -(-len(chunk) // a.cols)
        H = gap + rows * (tile_h + label_h + gap)
        sheet = Image.new("RGB", (a.width, H), (214, 222, 235))
        draw = ImageDraw.Draw(sheet)
        for k, f in enumerate(chunk):
            n = int(re.search(r"(\d+)", f.stem).group(1))
            r, c = divmod(k, a.cols)
            x = gap + c * (tile_w + gap)
            y = gap + r * (tile_h + label_h + gap)
            draw.text((x, y + 3), f"#{n}  {ids.get(n, '')}", fill=(22, 32, 47), font=font)
            im = Image.open(f).convert("RGB").resize((tile_w, tile_h), Image.LANCZOS)
            sheet.paste(im, (x, y + label_h))
            draw.rectangle([x - 1, y + label_h - 1, x + tile_w, y + label_h + tile_h], outline=(150, 165, 190))
        out = Path(f"{a.out_prefix}_{sheet_no:02d}.png")
        sheet.save(out)
        print(out)


if __name__ == "__main__":
    main()
