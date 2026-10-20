#!/usr/bin/env python3
"""
LK Design and Build — DXF logo masters for CAD.

A vector PDF is the right answer for a printer or an embroiderer, but it is the
weak answer for a drawing set. AutoCAD can attach a PDF as an underlay or run
PDFIMPORT on it, and both are fiddly and lossy. What a drafter actually wants is
native geometry, so this writes real DXF.

Each logo becomes closed LWPOLYLINEs plus solid HATCHes, organised onto layers
by brand colour:

    LK-CHAMPAGNE / LK-GOLD / LK-CHARCOAL        outlines, true colour set
    LK-CHAMPAGNE-FILL / LK-GOLD-FILL / ...      solid fills

so a drafter can freeze the fills for a line-only logo, or recolour by layer.
Drawn at 100 mm wide with the file's units set to millimetres, so it inserts at a
sensible size and scales cleanly.

    python3 generate_logo_dxf.py
"""

import os
import re
import xml.etree.ElementTree as ET

import ezdxf
from ezdxf import colors as dxf_colors
from fontTools.pens.basePen import BasePen

from generate_logo_pack import SRC, OUT, face_for, spacing
from generate_site_sign import Face

TARGET_WIDTH = 100.0      # mm across the artwork's viewBox
CURVE_STEPS = 24          # segments per curve; well below plotter resolution

COLOUR_NAMES = {
    "F2E6D0": "CHAMPAGNE", "C9A96E": "GOLD", "2C2C2C": "CHARCOAL",
    "000000": "BLACK", "FFFFFF": "WHITE", "FAFAFA": "WHITE",
    "9C7A42": "DEEPGOLD", "0A0A0A": "BLACK", "1A1A1A": "CHARCOAL",
}

# Which lockups are worth having as CAD geometry.
WANTED = [
    "lk-logo-horizontal-k-gold",     # the one in use on the drawings
    "lk-logo-horizontal-charcoal",
    "lk-logo-charcoal",
    "lk-icon-charcoal",
]


class ContourPen(BasePen):
    """Collects flattened closed contours in font units."""

    def __init__(self, glyph_set):
        super().__init__(glyph_set)
        self.contours = []
        self._cur = []

    def _moveTo(self, pt):
        self._flush()
        self._cur = [pt]

    def _lineTo(self, pt):
        self._cur.append(pt)

    def _curveToOne(self, p1, p2, p3):
        p0 = self._cur[-1]
        for i in range(1, CURVE_STEPS + 1):
            t = i / CURVE_STEPS
            u = 1 - t
            self._cur.append((
                u**3 * p0[0] + 3 * u*u*t * p1[0] + 3 * u*t*t * p2[0] + t**3 * p3[0],
                u**3 * p0[1] + 3 * u*u*t * p1[1] + 3 * u*t*t * p2[1] + t**3 * p3[1]))

    def _qCurveToOne(self, p1, p2):
        p0 = self._cur[-1]
        for i in range(1, CURVE_STEPS + 1):
            t = i / CURVE_STEPS
            u = 1 - t
            self._cur.append((
                u*u * p0[0] + 2 * u*t * p1[0] + t*t * p2[0],
                u*u * p0[1] + 2 * u*t * p1[1] + t*t * p2[1]))

    def _closePath(self):
        self._flush()

    def _endPath(self):
        self._flush()

    def _flush(self):
        if len(self._cur) > 2:
            self.contours.append(self._cur)
        self._cur = []


def glyph_contours(face_key, ch):
    f = Face.get(face_key)
    gname = f.name_for(ch)
    if not gname:
        return [], f
    gs = f.font.getGlyphSet()
    pen = ContourPen(gs)
    gs[gname].draw(pen)
    pen._flush()
    return pen.contours, f


def collect(path):
    """Walk an approved SVG and return {colour_hex: [contours in SVG units]}."""
    tree = ET.parse(path)
    root = tree.getroot()
    vb = [float(v) for v in root.get("viewBox").split()]
    by_colour = {}

    for el in root:
        tag = el.tag.split("}")[-1]
        if tag != "text":
            continue
        size = float(el.get("font-size", "16"))
        ls = spacing(el.get("letter-spacing"), size)
        face_key = face_for(el.get("font-family", ""), el.get("font-weight"),
                            el.get("font-style"))
        f = Face.get(face_key)
        scale = size / f.upm

        runs = []
        if el.text and el.text.strip():
            runs.append((el.text.strip(), el.get("fill"), None))
        for child in el:
            if child.tag.endswith("tspan") and child.text:
                runs.append((child.text.strip(), child.get("fill"), child.get("x")))

        x0 = float(el.get("x", "0"))
        y = float(el.get("y", "0"))
        if el.get("text-anchor") in ("middle", "end"):
            glyphs = sum(len(t) for t, _, _ in runs)
            total = sum(f.advance(c) * scale for t, _, _ in runs for c in t)
            total += ls * max(glyphs - 1, 0)
            x0 -= total / 2 if el.get("text-anchor") == "middle" else total

        pen_x = x0
        for txt, fill, explicit_x in runs:
            if explicit_x is not None:
                pen_x = float(explicit_x)
            hexc = (fill or "#000000").lstrip("#").upper()
            for ch in txt:
                contours, _ = glyph_contours(face_key, ch)
                for c in contours:
                    pts = [(pen_x + px * scale, y - py * scale) for px, py in c]
                    by_colour.setdefault(hexc, []).append(pts)
                pen_x += f.advance(ch) * scale + ls
    return by_colour, vb


def write_dxf(name, by_colour, vb):
    vb_x, vb_y, vb_w, vb_h = vb
    k = TARGET_WIDTH / vb_w

    doc = ezdxf.new("R2010", setup=True)
    doc.header["$INSUNITS"] = 4          # millimetres
    doc.header["$MEASUREMENT"] = 1       # metric
    msp = doc.modelspace()

    for hexc, contours in by_colour.items():
        cname = COLOUR_NAMES.get(hexc, hexc)
        rgb = tuple(int(hexc[i:i + 2], 16) for i in (0, 2, 4))
        line_layer, fill_layer = f"LK-{cname}", f"LK-{cname}-FILL"
        for ln in (line_layer, fill_layer):
            if ln not in doc.layers:
                lay = doc.layers.add(ln)
                lay.rgb = rgb

        # DXF is Y-up and the SVG is Y-down, so flip about the viewBox.
        paths = [[((x - vb_x) * k, (vb_y + vb_h - y) * k) for x, y in c]
                 for c in contours]

        for pts in paths:
            msp.add_lwpolyline(pts, close=True, dxfattribs={"layer": line_layer})

        hatch = msp.add_hatch(dxfattribs={"layer": fill_layer})
        hatch.rgb = rgb
        hatch.set_solid_fill()
        for pts in paths:
            hatch.paths.add_polyline_path(pts, is_closed=True)
        hatch.dxf.hatch_style = 0        # normal: counters knock out correctly

    out = os.path.join(OUT, "dxf", f"{name}.dxf")
    doc.saveas(out)
    return out, sum(len(v) for v in by_colour.values())


def main():
    os.makedirs(os.path.join(OUT, "dxf"), exist_ok=True)
    for name in WANTED:
        by_colour, vb = collect(os.path.join(SRC, f"{name}.svg"))
        out, n = write_dxf(name, by_colour, vb)
        colours = ", ".join(COLOUR_NAMES.get(c, c) for c in by_colour)
        print(f"  ✓ {name:34} {n:3} contours  [{colours}]")
    print(f"\nOutput: {os.path.join(OUT, 'dxf')}")


if __name__ == "__main__":
    main()
