#!/usr/bin/env python3
"""
LK Design and Build — outlined logo master pack.

Every file in assets/branding/final/*.svg stores the mark as live <text> in
Courier New and Inter. That is fine in a browser with both fonts installed, and
wrong everywhere else: a machine without Inter silently substitutes Helvetica or
Arial, so the tagline changes shape and width without anyone noticing. It also
means the SVGs cannot be handed to a printer or an embroiderer.

This script reads each approved SVG, converts the type to outlines at exactly
the published positions, and writes:

    assets/branding/logo-pack/svg/      outlined SVG   (web, Figma, anything)
    assets/branding/logo-pack/pdf/      vector PDF     (print, A3, drawings, apparel)
    assets/branding/logo-pack/png-4000/ 4000 px PNG    (transparent, digital fallback)
    assets/branding/logo-pack/png-1200/ 1200 px PNG    (transparent, screen use)
    assets/branding/logo-pack/apparel/  one-colour, no transparency

The geometry is reproduced from the source file rather than re-derived, so the
output is visually identical to what has already been approved.

    python3 generate_logo_pack.py
"""

import os
import re
import subprocess
import xml.etree.ElementTree as ET

from generate_site_sign import Face

SVG_NS = "http://www.w3.org/2000/svg"
ET.register_namespace("", SVG_NS)

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "assets", "branding", "final")
OUT = os.path.join(HERE, "assets", "branding", "logo-pack")

GOLD = "#C9A96E"
CHARCOAL = "#2C2C2C"

# Apparel versions. Solid colour, no opacity, no background panel: embroidery
# and screen print both need that. `None` keeps the source colours (two-tone).
APPAREL = [
    ("lk-logo-horizontal-k-gold", "2colour", None),
    ("lk-logo-charcoal", "black", "#000000"),
    ("lk-logo-charcoal", "white", "#FFFFFF"),
    ("lk-logo-charcoal", "gold", GOLD),
    ("lk-logo-horizontal-charcoal", "black", "#000000"),
    ("lk-logo-horizontal-charcoal", "white", "#FFFFFF"),
    ("lk-icon-charcoal", "black", "#000000"),
    ("lk-icon-charcoal", "white", "#FFFFFF"),
]


def face_for(family, weight, style=None):
    """Map an SVG font-family/weight/style trio onto one of the installed faces."""
    if "Courier" in family:
        return "mono"
    w = str(weight or "400")
    base = {"300": "light", "400": "regular", "500": "medium",
            "600": "semibold", "normal": "regular"}.get(w, "regular")
    if style == "italic" and base != "semibold":
        return f"{base}-italic"
    return base


def spacing(value, size):
    """SVG letter-spacing: a bare number is user units, `em` is relative."""
    if not value:
        return 0.0
    value = value.strip()
    if value.endswith("em"):
        return float(value[:-2]) * size
    return float(value.rstrip("px"))


def outline_text(el, force_fill=None, strip_opacity=False):
    """Convert one <text> element (with optional <tspan>s) to outlined paths."""
    size = float(el.get("font-size", "16"))
    ls = spacing(el.get("letter-spacing"), size)
    face_key = face_for(el.get("font-family", ""), el.get("font-weight"),
                        el.get("font-style"))
    f = Face.get(face_key)
    scale = size / f.upm

    # (text, fill, explicit x or None) for the element and each tspan
    runs = []
    if el.text and el.text.strip():
        runs.append((el.text.strip(), el.get("fill"), None))
    for child in el:
        if child.tag.endswith("tspan") and child.text:
            runs.append((child.text.strip(), child.get("fill"), child.get("x")))
        if child.tail and child.tail.strip():
            runs.append((child.tail.strip(), el.get("fill"), None))

    x0 = float(el.get("x", "0"))
    y = float(el.get("y", "0"))

    anchor = el.get("text-anchor")
    if anchor in ("middle", "end"):
        # Verified against librsvg by pixel-diffing both candidates: the anchored
        # width EXCLUDES the trailing letter-space. Including it shifts the icon
        # by ls/2 (2.6 units at size 260), which is plainly visible.
        glyphs = sum(len(t) for t, _, _ in runs)
        total = sum(f.advance(c) * scale for t, _, _ in runs for c in t)
        total += ls * max(glyphs - 1, 0)
        x0 -= total / 2 if anchor == "middle" else total

    opacity = el.get("fill-opacity")
    parts = []
    pen = x0
    for txt, fill, explicit_x in runs:
        if explicit_x is not None:
            pen = float(explicit_x)
        fill = force_fill or fill or "#000000"
        op = ""
        if opacity and not force_fill and not strip_opacity:
            op = f' fill-opacity="{opacity}"'
        parts.append(f'<g fill="{fill}"{op}>')
        for ch in txt:
            d = f.path_d(ch)
            if d.strip():
                parts.append(
                    f'<path d="{d}" transform="translate({pen:.4f} {y:.4f}) '
                    f'scale({scale:.6f} {-scale:.6f})"/>')
            pen += f.advance(ch) * scale + ls
        parts.append("</g>")
    return "".join(parts)


def serialise(el):
    """Serialise a non-text element (rect, existing path) back to markup."""
    tag = el.tag.split("}")[-1]
    attrs = " ".join(f'{k}="{v}"' for k, v in el.attrib.items())
    return f"<{tag} {attrs}/>"


def convert(path, force_fill=None, drop_bg=False, strip_opacity=False):
    tree = ET.parse(path)
    root = tree.getroot()
    body = []
    for el in root:
        tag = el.tag.split("}")[-1]
        if tag == "text":
            body.append(outline_text(el, force_fill, strip_opacity))
        elif tag == "path":
            if force_fill:
                el.set("fill", force_fill)
            if force_fill or strip_opacity:
                el.attrib.pop("fill-opacity", None)
            body.append(serialise(el))
        elif tag == "rect":
            if not drop_bg:
                body.append(serialise(el))
        elif tag == "g":
            inner = "".join(serialise(c) for c in el)
            attrs = " ".join(f'{k}="{v}"' for k, v in el.attrib.items())
            if force_fill:
                attrs = re.sub(r'fill="[^"]*"', f'fill="{force_fill}"', attrs)
                attrs = re.sub(r'fill-opacity="[^"]*"', "", attrs)
            body.append(f"<g {attrs}>{inner}</g>")
    head = (f'<svg xmlns="{SVG_NS}" viewBox="{root.get("viewBox")}" '
            f'width="{root.get("width")}" height="{root.get("height")}">')
    return head + "".join(body) + "</svg>"



# --------------------------------------------------------------- thumbnails ----

LIGHT_TILE, DARK_TILE, MID_TILE = "#F5F0EB", "#2C2C2C", "#8C857B"


def tile_for(svg_text):
    """Pick a background the artwork is actually visible against.

    Three cases, not two. A two-tone mark pairs a champagne half with a charcoal
    half, and whichever tile you choose one of them disappears, so those get a
    mid-tone instead.
    """
    if "<rect" in svg_text:          # mono/light variants carry their own panel
        return LIGHT_TILE
    fills = re.findall(r'fill="#([0-9A-Fa-f]{6})"', svg_text)
    if not fills:
        return LIGHT_TILE
    lums = []
    for f in fills:
        r, g, b = (int(f[i:i + 2], 16) / 255 for i in (0, 2, 4))
        lums.append(0.2126 * r + 0.7152 * g + 0.0722 * b)
    if max(lums) > 0.75 and min(lums) < 0.35:
        return MID_TILE
    return DARK_TILE if max(lums) > 0.75 else LIGHT_TILE


def write_thumb(name, svg_path, svg_text, folder="thumbs"):
    bg = tile_for(svg_text)
    out = os.path.join(OUT, folder, f"{name}.png")
    run(["rsvg-convert", "-f", "png", "-w", "520", "-b", bg, "-o", out, svg_path])
    return bg


# ---------------------------------------------------------------- index page ----

GROUPS = [
    ("CAD and drawing sets", "dxf",
     "Native DXF for AutoCAD and anything that opens DWG. Real geometry on "
     "layers by brand colour, drawn 100 mm wide in millimetres. Freeze the "
     "-FILL layers for a line-only logo."),
    ("Print and signage", "pdf",
     "Vector. Sharp at any size, from a business card to a billboard. This is "
     "what printers, signwriters and embroiderers want."),
    ("Shirts and workwear", "apparel",
     "Solid colour, no opacity, no background. Both processes need this: the "
     "standard gold sits at 90% opacity and a printer cannot print 90% of an ink."),
    ("High resolution images", "png-4000",
     "Transparent PNG, 4000 px wide, 342 dpi across a full A3 sheet. Use when "
     "software will not take a PDF."),
    ("Screen and web images", "png-1200",
     "Transparent PNG, 1200 px wide. Slides, social, email. Not for print."),
    ("Vector for web and design tools", "svg",
     "Outlined SVG. Figma, Illustrator, websites."),
]


def pretty(name):
    n = name
    for a, b in (("lk-logo-horizontal", "Horizontal"), ("lk-logo-letterhead", "Letterhead"),
                 ("lk-logo", "Stacked"), ("lk-icon", "Icon"), ("og-image", "Social card")):
        if n.startswith(a):
            n = b + n[len(a):]
            break
    n = n.replace("-1colour-", ", one colour ").replace("-2colour", ", two colour")
    n = n.replace("-k-gold", " K-gold").replace("-kgold", " K-gold")
    n = n.replace("-two-tone", " two-tone").replace("-", " ")
    return n.strip()


def build_index(thumb_bg):
    sections = []
    for title, folder, blurb in GROUPS:
        items = []
        seen = set()
        for f in sorted(os.listdir(os.path.join(OUT, folder))):
            stem, ext = os.path.splitext(f)
            if ext not in (".pdf", ".png", ".svg", ".dxf") or stem in seen:
                continue
            if folder == "apparel" and ext != ".pdf":
                continue
            if folder == "dxf" and ext != ".dxf":
                continue
            seen.add(stem)
            key = f"apparel-{stem}" if folder == "apparel" else stem
            thumb = f"thumbs/{key}.png"
            bg = thumb_bg.get(key, "#F5F0EB")
            items.append(
                f'<li><a href="{folder}/{f}" download>'
                f'<span class="tile" style="background:{bg}">'
                f'<img src="{thumb}" alt="" loading="lazy"></span>'
                f'<span class="meta"><strong>{pretty(stem)}</strong>'
                f'<em>{ext.lstrip(".").upper()}</em></span></a></li>')
        sections.append(
            f'<section><h2>{title}</h2><p>{blurb}</p>'
            f'<ul class="grid">{"".join(items)}</ul></section>')
    return "".join(sections)


def run(cmd):
    subprocess.run(cmd, check=True)


def write_set(name, svg_text):
    svg_path = os.path.join(OUT, "svg", f"{name}.svg")
    with open(svg_path, "w") as fh:
        fh.write(svg_text)
    run(["rsvg-convert", "-f", "pdf", "-o",
         os.path.join(OUT, "pdf", f"{name}.pdf"), svg_path])
    for px, folder in ((4000, "png-4000"), (1200, "png-1200")):
        run(["rsvg-convert", "-f", "png", "-w", str(px), "-o",
             os.path.join(OUT, folder, f"{name}.png"), svg_path])
    return write_thumb(name, svg_path, svg_text)


def main():
    for sub in ("svg", "pdf", "png-4000", "png-1200", "apparel", "thumbs"):
        os.makedirs(os.path.join(OUT, sub), exist_ok=True)

    thumb_bg = {}
    sources = sorted(f for f in os.listdir(SRC) if f.endswith(".svg"))
    for fname in sources:
        name = fname[:-4]
        thumb_bg[name] = write_set(name, convert(os.path.join(SRC, fname)))
        print(f"  ✓ {name}")

    # One-colour apparel masters: solid fill, no opacity, no background panel.
    print("\napparel (one colour, no transparency):")
    for src_name, label, fill in APPAREL:
        svg = convert(os.path.join(SRC, f"{src_name}.svg"),
                      force_fill=fill, drop_bg=True, strip_opacity=True)
        base = src_name.replace("-charcoal", "").replace("-k-gold", "-kgold")
        out_name = (f"{base}-{label}" if label == "2colour"
                    else f"{base}-1colour-{label}")
        svg_path = os.path.join(OUT, "apparel", f"{out_name}.svg")
        with open(svg_path, "w") as fh:
            fh.write(svg)
        run(["rsvg-convert", "-f", "pdf", "-o",
             os.path.join(OUT, "apparel", f"{out_name}.pdf"), svg_path])
        thumb_bg[f"apparel-{out_name}"] = write_thumb(
            f"apparel-{out_name}", svg_path, svg)
        print(f"  ✓ {out_name}")

    # USAGE.md is a build input, not something hand-edited inside the output
    # folder: it lived in there once and a rebuild deleted it.
    import shutil
    shutil.copy(os.path.join(HERE, "logo_pack_usage.md"),
                os.path.join(OUT, "USAGE.md"))

    import generate_logo_dxf          # late: it imports from this module
    print("\ndxf for CAD:")
    generate_logo_dxf.main()

    with open(os.path.join(HERE, "logo_pack_index_template.html")) as fh:
        template = fh.read()
    with open(os.path.join(OUT, "index.html"), "w") as fh:
        fh.write(template.replace("<!--SECTIONS-->", build_index(thumb_bg)))
    print(f"\n  ✓ index.html")

    # Prove the output is font-independent.
    leftover = [f for f in os.listdir(os.path.join(OUT, "svg"))
                if "<text" in open(os.path.join(OUT, "svg", f)).read()]
    print(f"\nfiles still containing live text: {len(leftover)}")
    print(f"Output: {OUT}")


if __name__ == "__main__":
    main()
