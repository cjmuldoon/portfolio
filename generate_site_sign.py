#!/usr/bin/env python3
"""
LK Design and Build — external site sign artwork.

400 x 600 mm portrait, 3 mm ACM panel. Five design options, each written as
print-ready SVG (3 mm bleed, all type converted to outlines), PDF and 300 dpi PNG.

Everything is drawn in millimetres: the SVG user unit == 1 mm, artboard origin is
the top-left TRIM corner, so bleed lives at negative coordinates.

    python3 generate_site_sign.py
"""

import os
import subprocess

import qrcode
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.ttLib import TTFont

# ---------------------------------------------------------------- brand ----

# Palette per the brand guide (lk-hub.html → Colour Palette, 6 colours).
GOLD = "#C9A96E"         # accent · rules · tagline
CHARCOAL = "#2C2C2C"     # primary mark on light backgrounds
CHAMPAGNE = "#F2E6D0"    # primary mark on dark backgrounds
NEAR_BLACK = "#0A0A0A"   # dark background
CREAM = "#F5F0EB"        # warm-neutral / two-tone background
WHITE = "#FAFAFA"        # light background
INK = "#1A1A1A"          # flood-fill charcoal — holds richer on a UV flatbed

# Verified against the live site, https://lkdesignandbuild.com.au/ (Aug 2026).
CONTACT = {
    "name": "Lyda",
    "phone": "0401 061 246",
    "website": "lkdesignandbuild.com.au",
    "url": "https://lkdesignandbuild.com.au/",
    "instagram": "@lkdesignandbuild",
    "instagram_url": "https://www.instagram.com/lkdesignandbuild/",
    # SA building work contractor licence. Lyda asked for this on the signs in
    # place of the ABN.
    "licence": "BLD 359176",
    "abn": "17 697 207 391",
}
TAGLINE = "DESIGN AND BUILD"

_HERE = os.path.dirname(os.path.abspath(__file__))

FONTS = {
    # Logo mark — Courier New, exactly as the approved lockup files use it.
    "mono": "/System/Library/Fonts/Supplemental/Courier New.ttf",
    # Body & UI — Inter (brand guide).
    "light": os.path.expanduser("~/Library/Fonts/Inter-Light.ttf"),
    "regular": os.path.expanduser("~/Library/Fonts/Inter-Regular.ttf"),
    "medium": os.path.expanduser("~/Library/Fonts/Inter-Medium.ttf"),
    "semibold": os.path.expanduser("~/Library/Fonts/Inter-SemiBold.ttf"),
    "light-italic": os.path.expanduser("~/Library/Fonts/Inter-LightItalic.ttf"),
    "regular-italic": os.path.expanduser("~/Library/Fonts/Inter-Italic.ttf"),
    "medium-italic": os.path.expanduser("~/Library/Fonts/Inter-MediumItalic.ttf"),
    # Headings & display — Cormorant Garamond (brand guide).
    "serif-light": os.path.join(_HERE, "assets/fonts/CormorantGaramond-Light.ttf"),
    "serif": os.path.join(_HERE, "assets/fonts/CormorantGaramond-Regular.ttf"),
    "serif-medium": os.path.join(_HERE, "assets/fonts/CormorantGaramond-Medium.ttf"),
    "serif-italic-light": os.path.join(_HERE,
                                       "assets/fonts/CormorantGaramond-LightItalic.ttf"),
    "serif-italic": os.path.join(_HERE, "assets/fonts/CormorantGaramond-Italic.ttf"),
}

# ------------------------------------------------------------ geometry ----

W, H = 400.0, 600.0      # trim, mm
BLEED = 3.0
SAFE = 20.0              # keep all content inside this margin

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "assets", "branding", "final", "signage")


# ------------------------------------------------------------ type-set ----

class Face:
    """Glyph-outline source for one font file."""

    _cache = {}

    def __init__(self, path):
        self.font = TTFont(path, fontNumber=0)
        self.upm = self.font["head"].unitsPerEm
        self.glyphs = self.font.getGlyphSet()
        self.cmap = self.font.getBestCmap()
        self.hmtx = self.font["hmtx"]

    @classmethod
    def get(cls, key):
        if key not in cls._cache:
            cls._cache[key] = cls(FONTS[key])
        return cls._cache[key]

    def name_for(self, ch):
        return self.cmap.get(ord(ch))

    def advance(self, ch):
        gn = self.name_for(ch)
        return self.hmtx[gn][0] if gn else self.upm // 2

    def path_d(self, ch):
        gn = self.name_for(ch)
        if not gn:
            return ""
        pen = SVGPathPen(self.glyphs)
        self.glyphs[gn].draw(pen)
        return pen.getCommands()


def measure(face_key, text, size, tracking=0.0):
    """Advance width in mm. `tracking` is in em."""
    f = Face.get(face_key)
    s = size / f.upm
    w = sum(f.advance(c) * s for c in text)
    if len(text) > 1:
        w += tracking * size * (len(text) - 1)
    return w


def text(face_key, txt, size, x, y, fill, tracking=0.0, anchor="start", opacity=None):
    """Outlined text. (x, y) is the baseline start/middle/end per `anchor`."""
    f = Face.get(face_key)
    s = size / f.upm
    width = measure(face_key, txt, size, tracking)
    if anchor == "middle":
        x -= width / 2
    elif anchor == "end":
        x -= width
    op = f' fill-opacity="{opacity}"' if opacity is not None else ""
    out = [f'<g fill="{fill}"{op}>']
    pen_x = x
    for ch in txt:
        d = f.path_d(ch)
        if d.strip():
            out.append(
                f'<path d="{d}" transform="translate({pen_x:.4f} {y:.4f}) '
                f'scale({s:.6f} {-s:.6f})"/>'
            )
        pen_x += f.advance(ch) * s + tracking * size
    out.append("</g>")
    return "".join(out), width


# ------------------------------------------------------------- lockup ----

# Ratios lifted straight from the approved website lockup
# (assets/branding/final/lk-logo-hero-champagne.svg, tagline already outlined).
#
# Reverse-engineering that file: LK is Courier New at 140 with -0.02em tracking,
# starting at x=40, so its ADVANCE box runs 40 -> 202.4 and its advance centre is
# 121.2. The approved tagline is centred at 125.18 — not on the advance centre but
# on the INK centre of the letterforms (125.20), which is what "centred under LK"
# actually means once Courier's side bearings are accounted for. The tagline is
# Inter *Medium* at 13 with 2.1 letter-spacing (solved from the outlined glyph
# positions: Medium gives exactly 2.100, Light 2.156). Both facts are reproduced
# below rather than approximated.
LK_TRACK = -0.02          # letter-spacing on "LK"
TAG_FACE = "medium"       # Inter Medium — the bolder website tagline
TAG_RATIO = 13.0 / 140.0  # tagline size relative to LK size
TAG_TRACK = 2.1 / 13.0    # tagline letter-spacing, em
TAG_GAP = 18.0 / 140.0    # baseline-to-baseline gap relative to LK size


def lk_ink(lk_size):
    """Ink extents of 'LK' relative to the advance origin: (start, width)."""
    from fontTools.pens.boundsPen import BoundsPen
    f = Face.get("mono")
    s = lk_size / f.upm
    gs = f.font.getGlyphSet()

    def bounds(ch):
        pen = BoundsPen(gs)
        gs[f.name_for(ch)].draw(pen)
        return pen.bounds

    k_origin = f.advance("L") * s + LK_TRACK * lk_size
    start = bounds("L")[0] * s
    end = k_origin + bounds("K")[2] * s
    return start, end - start


def lockup(cx, baseline, lk_size, lk_fill, tag_fill, k_fill=None, tag_opacity=0.9):
    """LK + DESIGN AND BUILD. cx is the optical (ink) centre of the mark, which is
    what both the mark and the tagline align to in the approved lockup."""
    f = Face.get("mono")
    s = lk_size / f.upm
    ink_start, ink_w = lk_ink(lk_size)
    x = cx - ink_start - ink_w / 2          # advance origin of the "L"
    parts = []
    for ch, fill in (("L", lk_fill), ("K", k_fill or lk_fill)):
        parts.append(
            f'<g fill="{fill}"><path d="{f.path_d(ch)}" '
            f'transform="translate({x:.4f} {baseline:.4f}) '
            f'scale({s:.6f} {-s:.6f})"/></g>'
        )
        x += f.advance(ch) * s + LK_TRACK * lk_size
    tag_size = lk_size * TAG_RATIO
    tag_svg, _ = text(TAG_FACE, TAGLINE, tag_size, cx,
                      baseline + lk_size * TAG_GAP, tag_fill,
                      tracking=TAG_TRACK, anchor="middle", opacity=tag_opacity)
    parts.append(tag_svg)
    return "".join(parts), ink_w


def lk_cap_height(lk_size):
    """Courier New cap height in mm — used to optically centre the mark."""
    f = Face.get("mono")
    return f.font["OS/2"].sCapHeight / f.upm * lk_size


# ----------------------------------------------------------------- qr ----

def instagram_glyph(cx, cy, size, colour, light):
    """The Instagram camera mark, knocked out of the centre of a QR code."""
    pad = size * 0.30
    box = size + pad
    sw = size * 0.105
    r = size * 0.30
    return (
        f'<rect x="{cx-box/2:.3f}" y="{cy-box/2:.3f}" width="{box:.3f}" '
        f'height="{box:.3f}" rx="{box*0.22:.3f}" fill="{light}"/>'
        f'<g fill="none" stroke="{colour}" stroke-width="{sw:.3f}">'
        f'<rect x="{cx-size/2:.3f}" y="{cy-size/2:.3f}" width="{size:.3f}" '
        f'height="{size:.3f}" rx="{r:.3f}"/>'
        f'<circle cx="{cx:.3f}" cy="{cy:.3f}" r="{size*0.235:.3f}"/></g>'
        f'<circle cx="{cx+size*0.255:.3f}" cy="{cy-size*0.255:.3f}" '
        f'r="{size*0.062:.3f}" fill="{colour}"/>'
    )


def qr_block(x, y, size, light, dark, radius=0.0, url=None, style=None):
    """QR drawn as vector modules with a 4-module quiet zone.

    style="instagram" knocks the Instagram mark out of the centre; error
    correction steps up to H (30% recovery) so the code still reads.
    """
    style = style if style is not None else ACTIVE["style"]
    ec = (qrcode.constants.ERROR_CORRECT_H if style == "instagram"
          else qrcode.constants.ERROR_CORRECT_Q)
    qr = qrcode.QRCode(version=None, box_size=1, border=4, error_correction=ec)
    qr.add_data(url if url is not None else ACTIVE["url"])
    qr.make(fit=True)
    m = qr.get_matrix()
    n = len(m)
    mod = size / n
    rx = f' rx="{radius}"' if radius else ""
    out = [f'<rect x="{x:.3f}" y="{y:.3f}" width="{size:.3f}" height="{size:.3f}" '
           f'fill="{light}"{rx}/>', f'<g fill="{dark}">']
    for r, row in enumerate(m):
        c = 0
        while c < n:
            if row[c]:
                run = 0
                while c + run < n and row[c + run]:
                    run += 1
                out.append(
                    f'<rect x="{x + c * mod:.4f}" y="{y + r * mod:.4f}" '
                    f'width="{run * mod + 0.02:.4f}" height="{mod + 0.02:.4f}"/>'
                )
                c += run
            else:
                c += 1
    out.append("</g>")
    if style == "instagram":
        out.append(instagram_glyph(x + size / 2, y + size / 2, size * 0.20,
                                   dark, light))
    return "".join(out)


# ------------------------------------------------------------- qr variant ----
#
# Two sets of artwork are generated from the same layouts: one whose QR points at
# the website, one at Instagram. The website URL is already set in type on every
# panel, so the Instagram set is arguably the more useful scan — it takes a
# passer-by straight to photos of the work.

QR_VARIANTS = {
    "web": dict(url=CONTACT["url"], style="plain", caption=None),
    "insta": dict(url=CONTACT["instagram_url"], style="instagram",
                  caption=CONTACT["instagram"]),
}
ACTIVE = QR_VARIANTS["web"]


def cap(default, maxw=None, size=8.4):
    """Caption under a QR: the handle on the Instagram set, else the design's own
    wording. Returns (text, size) with the size shrunk to fit `maxw` if given."""
    txt = ACTIVE["caption"] or default
    if maxw:
        while size > 3.2 and measure("light", txt, size, 0.2) > maxw:
            size -= 0.1
    return txt, size


# -------------------------------------------------------------- pieces ----

def rule(x1, y1, x2, y2, colour, w=0.8, opacity=None):
    op = f' stroke-opacity="{opacity}"' if opacity is not None else ""
    return (f'<line x1="{x1:.3f}" y1="{y1:.3f}" x2="{x2:.3f}" y2="{y2:.3f}" '
            f'stroke="{colour}" stroke-width="{w}"{op} stroke-linecap="butt"/>')


def flood(colour, x=-BLEED, y=-BLEED, w=W + 2 * BLEED, h=H + 2 * BLEED):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{colour}"/>'


# ------------------------------------------------------------- designs ----

def design_a():
    """A — Monolith. Charcoal ground, champagne mark, gold detail. Premium/minimal."""
    p = [flood(INK)]
    # inner gold keyline
    p.append(f'<rect x="14" y="14" width="{W-28}" height="{H-28}" fill="none" '
             f'stroke="{GOLD}" stroke-width="0.9" stroke-opacity="0.55"/>')

    lk_size = 165
    mark, _ = lockup(W / 2, 168, lk_size, CHAMPAGNE, GOLD, k_fill=GOLD)
    p.append(mark)

    p.append(rule(W / 2 - 32, 232, W / 2 + 32, 232, GOLD, 1.2))

    t, _ = text("light", "RENOVATION IN PROGRESS", 13.5, W / 2, 268,
                CHAMPAGNE, tracking=0.24, anchor="middle")
    p.append(t)
    t, _ = text("light", "INTERIOR DESIGN  ·  RENOVATION  ·  PROJECT MANAGEMENT",
                7.6, W / 2, 292, CHAMPAGNE, tracking=0.14, anchor="middle",
                opacity=0.62)
    p.append(t)

    t, _ = text("light", "ENQUIRIES", 8.5, W / 2, 350, GOLD,
                tracking=0.32, anchor="middle")
    p.append(t)
    t, _ = text("semibold", CONTACT["phone"], 40, W / 2, 394, CHAMPAGNE,
                tracking=0.005, anchor="middle")
    p.append(t)
    t, _ = text("regular", CONTACT["website"], 16.2, W / 2, 424, GOLD,
                tracking=0.03, anchor="middle")
    p.append(t)

    p.append(rule(W / 2 - 32, 452, W / 2 + 32, 452, GOLD, 0.7, opacity=0.5))

    qs = 62
    p.append(qr_block(W / 2 - qs / 2, 470, qs, CHAMPAGNE, INK))
    ct, cs = cap("SCAN TO VIEW OUR WORK", maxw=W - 2 * SAFE, size=8.4)
    t, _ = text("light", ct, cs, W / 2, 546, CHAMPAGNE,
                tracking=0.2, anchor="middle", opacity=0.6)
    p.append(t)
    t, _ = text("light", CONTACT["licence"], 7.0, W / 2, 566, CHAMPAGNE,
                tracking=0.16, anchor="middle", opacity=0.38)
    p.append(t)
    return "".join(p)


def design_b():
    """B — Champagne. Light ground, charcoal type. Softest, most 'interiors'."""
    p = [flood(CHAMPAGNE)]
    p.append(f'<rect x="-{BLEED}" y="-{BLEED}" width="{W+2*BLEED}" '
             f'height="{10+BLEED}" fill="{GOLD}"/>')
    p.append(f'<rect x="-{BLEED}" y="{H-10}" width="{W+2*BLEED}" '
             f'height="{10+BLEED}" fill="{GOLD}"/>')

    lk_size = 158
    mark, _ = lockup(W / 2, 176, lk_size, CHARCOAL, GOLD)
    p.append(mark)

    p.append(rule(W / 2 - 28, 236, W / 2 + 28, 236, GOLD, 1.2))

    t, _ = text("light", "RENOVATION IN PROGRESS", 13, W / 2, 272,
                CHARCOAL, tracking=0.24, anchor="middle")
    p.append(t)

    for i, line in enumerate(("Interior Design", "Renovation",
                              "Project Management")):
        t, _ = text("light", line, 11, W / 2, 312 + i * 19, CHARCOAL,
                    tracking=0.03, anchor="middle", opacity=0.7)
        p.append(t)

    p.append(rule(SAFE + 26, 392, W - SAFE - 26, 392, CHARCOAL, 0.5, opacity=0.28))

    t, _ = text("semibold", CONTACT["phone"], 38, W / 2, 442, CHARCOAL,
                tracking=0.005, anchor="middle")
    p.append(t)
    t, _ = text("regular", CONTACT["website"], 15.7, W / 2, 470, CHARCOAL,
                tracking=0.03, anchor="middle", opacity=0.72)
    p.append(t)

    qs = 58
    p.append(qr_block(W / 2 - qs / 2, 484, qs, CHAMPAGNE, CHARCOAL))
    ct, cs = cap("SCAN FOR OUR PORTFOLIO", maxw=W - 2 * SAFE, size=8.4)
    t, _ = text("light", ct, cs, W / 2, 558, CHARCOAL,
                tracking=0.2, anchor="middle", opacity=0.55)
    p.append(t)
    t, _ = text("light", CONTACT["licence"], 7.0, W / 2, 574, CHARCOAL,
                tracking=0.16, anchor="middle", opacity=0.35)
    p.append(t)
    return "".join(p)


def design_c():
    """C — Split. Charcoal identity block over a champagne information panel."""
    split = 330.0
    p = [flood(CHAMPAGNE)]
    p.append(flood(INK, y=-BLEED, h=split + BLEED))
    p.append(f'<rect x="-{BLEED}" y="{split}" width="{W+2*BLEED}" height="5" '
             f'fill="{GOLD}"/>')

    lk_size = 168
    mark, _ = lockup(W / 2, 172, lk_size, CHAMPAGNE, GOLD, k_fill=GOLD)
    p.append(mark)

    p.append(rule(W / 2 - 30, 234, W / 2 + 30, 234, GOLD, 1.0, opacity=0.85))
    t, _ = text("light", "RENOVATION IN PROGRESS", 13.5, W / 2, 272,
                CHAMPAGNE, tracking=0.24, anchor="middle")
    p.append(t)
    t, _ = text("light", "Considered design. Precision build.", 11, W / 2, 298,
                CHAMPAGNE, tracking=0.02, anchor="middle", opacity=0.55)
    p.append(t)

    # information panel
    lx = SAFE + 8
    t, _ = text("light", "ENQUIRIES WELCOME", 7.4, lx, 372, GOLD,
                tracking=0.28)
    p.append(t)
    t, _ = text("semibold", CONTACT["phone"], 33, lx, 412, CHARCOAL,
                tracking=0.005)
    p.append(t)
    t, _ = text("regular", CONTACT["website"], 13.9, lx, 438, CHARCOAL,
                tracking=0.03, opacity=0.75)
    p.append(t)

    p.append(rule(lx, 460, W - SAFE - 8, 460, CHARCOAL, 0.5, opacity=0.25))
    for i, line in enumerate(("Interior Design", "Renovation",
                              "Project Management")):
        t, _ = text("light", line, 10, lx, 482 + i * 17, CHARCOAL,
                    tracking=0.04, opacity=0.7)
        p.append(t)

    qs = 56
    qx = W - SAFE - 8 - qs
    p.append(qr_block(qx, 476, qs, CHAMPAGNE, CHARCOAL))
    ct, cs = cap("SCAN", maxw=qs + 26, size=8.4)
    t, _ = text("light", ct, cs, qx + qs / 2, 544, CHARCOAL,
                tracking=0.24, anchor="middle", opacity=0.55)
    p.append(t)

    t, _ = text("light", CONTACT["licence"], 7.0, lx, 566, CHARCOAL,
                tracking=0.16, opacity=0.4)
    p.append(t)
    return "".join(p)


def design_d():
    """D — Blueprint. Drafting grid + registration marks. Architectural."""
    p = [flood(INK)]
    grid = ['<g stroke="%s" stroke-width="0.25" stroke-opacity="0.16">' % GOLD]
    step = 20.0
    x = 0.0
    while x <= W:
        grid.append(f'<line x1="{x}" y1="0" x2="{x}" y2="{H}"/>')
        x += step
    y = 0.0
    while y <= H:
        grid.append(f'<line x1="0" y1="{y}" x2="{W}" y2="{y}"/>')
        y += step
    grid.append("</g>")
    p.append("".join(grid))

    # drafting frame + corner ticks
    p.append(f'<rect x="20" y="20" width="{W-40}" height="{H-40}" fill="none" '
             f'stroke="{GOLD}" stroke-width="0.8" stroke-opacity="0.75"/>')
    for cx, cy in ((20, 20), (W - 20, 20), (20, H - 20), (W - 20, H - 20)):
        p.append(f'<g stroke="{GOLD}" stroke-width="0.8" stroke-opacity="0.9">')
        p.append(f'<line x1="{cx-7}" y1="{cy}" x2="{cx+7}" y2="{cy}"/>')
        p.append(f'<line x1="{cx}" y1="{cy-7}" x2="{cx}" y2="{cy+7}"/></g>')

    t, _ = text("light", "PROJECT", 6.2, 31, 44, GOLD, tracking=0.3, opacity=0.75)
    p.append(t)
    t, _ = text("light", "RESIDENTIAL RENOVATION", 6.2, W - 31, 44, GOLD,
                tracking=0.3, anchor="end", opacity=0.75)
    p.append(t)
    p.append(rule(31, 52, W - 31, 52, GOLD, 0.4, opacity=0.4))

    lk_size = 160
    mark, _ = lockup(W / 2, 232, lk_size, CHAMPAGNE, GOLD, k_fill=GOLD)
    p.append(mark)

    # dimension line under the mark
    lk_w = measure("mono", "LK", lk_size, LK_TRACK)
    dy = 274
    p.append(f'<g stroke="{GOLD}" stroke-width="0.5" stroke-opacity="0.6">')
    p.append(f'<line x1="{W/2-lk_w/2}" y1="{dy}" x2="{W/2+lk_w/2}" y2="{dy}"/>')
    for ex in (W / 2 - lk_w / 2, W / 2 + lk_w / 2):
        p.append(f'<line x1="{ex}" y1="{dy-4}" x2="{ex}" y2="{dy+4}"/>')
    p.append("</g>")

    t, _ = text("light", "WORKS IN PROGRESS", 12.5, W / 2, 326, CHAMPAGNE,
                tracking=0.26, anchor="middle")
    p.append(t)
    t, _ = text("light", "Considered design. Precision build.", 10, W / 2, 350,
                CHAMPAGNE, tracking=0.02, anchor="middle", opacity=0.55)
    p.append(t)

    # spec-sheet style contact table
    top = 426
    rows = (("PHONE", CONTACT["phone"]),
            ("WEB", CONTACT["website"]),
            ("SCOPE", "Design · Renovation · PM"),
            ("LICENCE", CONTACT["licence"]))
    p.append(rule(31, top - 12, W - 31, top - 12, GOLD, 0.4, opacity=0.4))
    for i, (k, v) in enumerate(rows):
        yy = top + i * 22
        t, _ = text("light", k, 6.4, 31, yy, GOLD, tracking=0.28, opacity=0.85)
        p.append(t)
        weight = "semibold" if k == "PHONE" else "light"
        sz = 17 if k == "PHONE" else 10.5
        t, _ = text(weight, v, sz, 96, yy + (2 if k == "PHONE" else 0),
                    CHAMPAGNE, tracking=0.02)
        p.append(t)
        p.append(rule(31, yy + 9, W - 31 - 78, yy + 9, GOLD, 0.3, opacity=0.28))

    qs = 60
    p.append(qr_block(W - 31 - qs, top - 6, qs, CHAMPAGNE, INK))
    ct, cs = cap("SCAN", maxw=qs + 26, size=8.4)
    t, _ = text("light", ct, cs, W - 31 - qs / 2, top + qs + 6, CHAMPAGNE,
                tracking=0.24, anchor="middle", opacity=0.6)
    p.append(t)

    # drafting-sheet footer
    p.append(rule(31, 540, W - 31, 540, GOLD, 0.4, opacity=0.4))
    t, _ = text("light", "SHEET 01", 6.2, 31, 556, GOLD, tracking=0.3,
                opacity=0.7)
    p.append(t)
    t, _ = text("light", "ADELAIDE  SA", 6.2, W - 31, 556, GOLD, tracking=0.3,
                anchor="end", opacity=0.7)
    p.append(t)
    return "".join(p)


def design_e():
    """E — Contact-first. Maximum street legibility / lead generation."""
    p = [flood(CHAMPAGNE)]
    band = 186.0
    p.append(flood(INK, y=-BLEED, h=band + BLEED))
    p.append(f'<rect x="-{BLEED}" y="{band}" width="{W+2*BLEED}" height="4" '
             f'fill="{GOLD}"/>')

    lk_size = 122
    mark, _ = lockup(W / 2, 118, lk_size, CHAMPAGNE, GOLD, k_fill=GOLD)
    p.append(mark)
    t, _ = text("light", "RENOVATION IN PROGRESS", 10.5, W / 2, 160, CHAMPAGNE,
                tracking=0.26, anchor="middle", opacity=0.75)
    p.append(t)

    t, _ = text("light", "PLANNING A RENOVATION?", 13, W / 2, 236, CHARCOAL,
                tracking=0.2, anchor="middle")
    p.append(t)
    t, _ = text("light", "Talk to the team transforming this home.", 11, W / 2,
                260, CHARCOAL, tracking=0.02, anchor="middle", opacity=0.65)
    p.append(t)

    p.append(f'<rect x="{SAFE}" y="286" width="{W-2*SAFE}" height="86" '
             f'fill="{GOLD}"/>')
    t, _ = text("light", "CALL", 8.5, W / 2, 312, INK, tracking=0.34,
                anchor="middle", opacity=0.8)
    p.append(t)
    t, _ = text("semibold", CONTACT["phone"], 46, W / 2, 356, INK,
                tracking=0.005, anchor="middle")
    p.append(t)

    t, _ = text("regular", CONTACT["website"], 17.4, W / 2, 402, CHARCOAL,
                tracking=0.03, anchor="middle")
    p.append(t)

    qs = 84
    p.append(qr_block(W / 2 - qs / 2, 420, qs, CHAMPAGNE, CHARCOAL))
    ct, cs = cap("SCAN TO SEE OUR PORTFOLIO", maxw=W - 2 * SAFE, size=8.4)
    t, _ = text("light", ct, cs, W / 2, 522, CHARCOAL,
                tracking=0.2, anchor="middle", opacity=0.6)
    p.append(t)
    p.append(rule(W / 2 - 40, 540, W / 2 + 40, 540, GOLD, 0.8))
    t, _ = text("light", "INTERIOR DESIGN  ·  RENOVATION  ·  PROJECT MANAGEMENT",
                7, W / 2, 560, CHARCOAL, tracking=0.12, anchor="middle",
                opacity=0.6)
    p.append(t)
    t, _ = text("light", CONTACT["licence"], 7.0, W / 2, 578, CHARCOAL,
                tracking=0.16, anchor="middle", opacity=0.4)
    p.append(t)
    return "".join(p)


# ------------------------------------------------- round two: style guide ----
#
# Round two applies the brand guide properly — Cormorant Garamond as the display
# face (round one used Inter throughout), the full six-colour palette, and the
# logo clear-space rule (1x monogram height on all sides) — together with the
# signage legibility research: one dominant message, ~1 in of cap height per
# 10 ft of viewing distance, light-on-dark or dark-on-light only, and enough
# empty field that the mark reads before the detail does.


def design_f():
    """F — Plaque. Charcoal plaque on cream, serif headline. Architect's plate."""
    p = [flood(CREAM)]

    px, py, pw, ph = 40.0, 48.0, W - 80.0, 232.0
    p.append(f'<rect x="{px}" y="{py}" width="{pw}" height="{ph}" '
             f'fill="{NEAR_BLACK}"/>')
    p.append(f'<rect x="{px+7}" y="{py+7}" width="{pw-14}" height="{ph-14}" '
             f'fill="none" stroke="{GOLD}" stroke-width="0.7" '
             f'stroke-opacity="0.5"/>')

    lk_size = 118
    mark, _ = lockup(W / 2, 178, lk_size, CHAMPAGNE, GOLD, k_fill=GOLD)
    p.append(mark)

    t, _ = text("serif-light", "Renovation in progress", 36, W / 2, 344,
                CHARCOAL, tracking=0.01, anchor="middle")
    p.append(t)
    p.append(rule(W / 2 - 30, 366, W / 2 + 30, 366, GOLD, 1.0))
    t, _ = text("light", "INTERIOR DESIGN  ·  RENOVATION  ·  PROJECT MANAGEMENT",
                7.2, W / 2, 392, CHARCOAL, tracking=0.14, anchor="middle",
                opacity=0.62)
    p.append(t)

    t, _ = text("semibold", CONTACT["phone"], 38, W / 2, 452, CHARCOAL,
                tracking=0.005, anchor="middle")
    p.append(t)
    t, _ = text("regular", CONTACT["website"], 15.7, W / 2, 480, CHARCOAL,
                tracking=0.03, anchor="middle", opacity=0.72)
    p.append(t)

    qs = 52
    p.append(qr_block(W / 2 - qs / 2, 498, qs, CREAM, CHARCOAL))
    ct, cs = cap("SCAN TO VIEW OUR WORK", maxw=W - 2 * SAFE, size=8.4)
    t, _ = text("light", ct, cs, W / 2, 564, CHARCOAL,
                tracking=0.2, anchor="middle", opacity=0.55)
    p.append(t)
    t, _ = text("light", CONTACT["licence"], 7.0, W / 2, 578, CHARCOAL,
                tracking=0.16, anchor="middle", opacity=0.35)
    p.append(t)
    return "".join(p)


def design_g():
    """G — Editorial. Asymmetric, left-aligned, serif display. Magazine feel."""
    p = [flood(CHAMPAGNE)]
    lx = 48.0
    p.append(rule(26, 56, 26, 544, GOLD, 0.8, opacity=0.8))

    lk_size = 94
    lk_w = measure("mono", "LK", lk_size, LK_TRACK)
    mark, _ = lockup(lx + lk_w / 2, 140, lk_size, CHARCOAL, GOLD)
    p.append(mark)

    for i, line in enumerate(("A considered", "renovation", "in progress.")):
        t, _ = text("serif-light", line, 52, lx, 258 + i * 58, CHARCOAL,
                    tracking=0.005)
        p.append(t)

    p.append(rule(lx, 452, lx + 56, 452, GOLD, 1.2))

    t, _ = text("light", "ENQUIRIES", 7.2, lx, 486, CHARCOAL, tracking=0.3,
                opacity=0.6)
    p.append(t)
    t, _ = text("semibold", CONTACT["phone"], 30, lx, 522, CHARCOAL,
                tracking=0.005)
    p.append(t)
    t, _ = text("regular", CONTACT["website"], 13.3, lx, 546, CHARCOAL,
                tracking=0.03, opacity=0.72)
    p.append(t)
    t, _ = text("light", CONTACT["licence"], 7.0, lx, 570, CHARCOAL,
                tracking=0.16, opacity=0.38)
    p.append(t)

    qs = 54
    p.append(qr_block(W - SAFE - 6 - qs, 486, qs, CHAMPAGNE, CHARCOAL))
    ct, cs = cap("SCAN", maxw=qs + 30, size=8.4)
    t, _ = text("light", ct, cs, W - SAFE - 6 - qs / 2, 552, CHARCOAL,
                tracking=0.24, anchor="middle", opacity=0.55)
    p.append(t)
    return "".join(p)


def design_h():
    """H — Nightfall. Near-black field, full clear space, quiet luxury."""
    p = [flood(NEAR_BLACK)]

    lk_size = 150
    mark, _ = lockup(W / 2, 248, lk_size, CHAMPAGNE, GOLD, k_fill=GOLD)
    p.append(mark)

    t, _ = text("serif-light", "Renovation in progress", 34, W / 2, 392,
                CHAMPAGNE, tracking=0.01, anchor="middle")
    p.append(t)
    p.append(rule(W / 2 - 22, 414, W / 2 + 22, 414, GOLD, 1.0))

    t, _ = text("semibold", CONTACT["phone"], 34, W / 2, 462, CHAMPAGNE,
                tracking=0.005, anchor="middle")
    p.append(t)
    t, _ = text("regular", CONTACT["website"], 15.1, W / 2, 490, GOLD,
                tracking=0.03, anchor="middle")
    p.append(t)

    qs = 50
    p.append(qr_block(W / 2 - qs / 2, 506, qs, CHAMPAGNE, NEAR_BLACK))
    t, _ = text("light", CONTACT["licence"], 7.0, W / 2, 576, CHAMPAGNE,
                tracking=0.16, anchor="middle", opacity=0.3)
    p.append(t)
    return "".join(p)


def design_i():
    """I — Kerbside. Legibility-led: the phone is the largest element on the sign."""
    p = [flood(CREAM)]

    lk_size = 100
    mark, _ = lockup(W / 2, 152, lk_size, CHARCOAL, GOLD)
    p.append(mark)

    t, _ = text("serif-light", "Renovation in progress", 28, W / 2, 238,
                CHARCOAL, tracking=0.01, anchor="middle")
    p.append(t)

    by, bh = 272.0, 200.0
    p.append(flood(INK, x=-BLEED, y=by, w=W + 2 * BLEED, h=bh))
    p.append(f'<rect x="-{BLEED}" y="{by}" width="{W+2*BLEED}" height="3" '
             f'fill="{GOLD}"/>')
    p.append(f'<rect x="-{BLEED}" y="{by+bh-3}" width="{W+2*BLEED}" height="3" '
             f'fill="{GOLD}"/>')

    t, _ = text("light", "PLANNING YOURS?", 10, W / 2, 312, GOLD,
                tracking=0.3, anchor="middle")
    p.append(t)
    t, _ = text("semibold", CONTACT["phone"], 50, W / 2, 380, CHAMPAGNE,
                tracking=0.005, anchor="middle")
    p.append(t)
    t, _ = text("regular", CONTACT["website"], 17.4, W / 2, 424, CHAMPAGNE,
                tracking=0.03, anchor="middle", opacity=0.85)
    p.append(t)
    t, _ = text("light", "INTERIOR DESIGN  ·  RENOVATION  ·  PROJECT MANAGEMENT",
                6.8, W / 2, 452, CHAMPAGNE, tracking=0.12, anchor="middle",
                opacity=0.55)
    p.append(t)

    qs = 56
    p.append(qr_block(W / 2 - qs / 2, 492, qs, CREAM, CHARCOAL))
    ct, cs = cap("SCAN FOR OUR RECENT WORK", maxw=W - 2 * SAFE, size=8.4)
    t, _ = text("light", ct, cs, W / 2, 564, CHARCOAL,
                tracking=0.2, anchor="middle", opacity=0.55)
    p.append(t)
    t, _ = text("light", CONTACT["licence"], 7.0, W / 2, 580, CHARCOAL,
                tracking=0.16, anchor="middle", opacity=0.35)
    p.append(t)
    return "".join(p)



# ------------------------------------------------- round three: softened ----
#
# Lyda's feedback on Monolith: right direction, but "too structured". The hard
# edges in that layout are the rectangular keyline, the wide-tracked uppercase
# headline, the flat near-black ground and the tight stack of centred lines.
# Each one is dialled back here:
#
#   frame      removed entirely; the field does the framing
#   ground     warm charcoal (#241F1D) instead of near-black, so it reads brown-
#              black in daylight rather than switched-off-screen black
#   headline   Cormorant Garamond in sentence case instead of tracked capitals
#   rules      shorter, lighter, round-capped
#   labels     sentence case, tracking roughly halved
#   weights    Inter Medium on the number rather than SemiBold
#   spacing    more air between groups than within them
#   corners    20 mm radius, cut by the router (a specification, not artwork)
#
# The number gives up about 0.3 m of read distance to the lighter weight. That is
# the honest cost of softer.

SOFT_DARK = "#241F1D"       # warm charcoal, reads brown-black outdoors


def soft_rule(cx, y, half, colour, w=0.9, opacity=0.75):
    return (f'<line x1="{cx-half:.2f}" y1="{y}" x2="{cx+half:.2f}" y2="{y}" '
            f'stroke="{colour}" stroke-width="{w}" stroke-opacity="{opacity}" '
            f'stroke-linecap="round"/>')


def _soft_body(bg, ink, accent, k_fill, tag_op=0.9, services_op=0.5,
               caption_op=0.55, licence_op=0.34):
    """Shared skeleton for the two softened flagships (dark and light).

    Headline in capitals per Lyda. Tracked capitals in Cormorant run too wide for
    a 400 mm panel on one line, so they break over two at 40, which lands on the
    same 25 mm cap height the sentence-case version had. The services line and the
    enquiries label follow the same rule; the web address, handle and licence stay
    as literal strings.
    """
    p = [flood(bg)]

    mark, _ = lockup(W / 2, 178, 158, ink, accent, k_fill=k_fill,
                     tag_opacity=tag_op)
    p.append(mark)

    p.append(soft_rule(W / 2, 238, 22, accent))

    for i, line in enumerate(("RENOVATION", "IN PROGRESS")):
        t, _ = text("serif-light", line, 40, W / 2, 282 + i * 44, ink,
                    tracking=0.13, anchor="middle")
        p.append(t)

    t, _ = text("light", "INTERIOR DESIGN  ·  RENOVATION  ·  PROJECT MANAGEMENT",
                7.4, W / 2, 358, ink, tracking=0.10, anchor="middle",
                opacity=services_op)
    p.append(t)

    t, _ = text("serif", "ENQUIRIES", 16, W / 2, 398, accent, tracking=0.18,
                anchor="middle")
    p.append(t)
    t, _ = text("medium", CONTACT["phone"], 38, W / 2, 436, ink,
                tracking=0.01, anchor="middle")
    p.append(t)
    t, _ = text("light", CONTACT["website"], 15.1, W / 2, 462, accent,
                tracking=0.02, anchor="middle")
    p.append(t)

    qs = 58
    p.append(qr_block(W / 2 - qs / 2, 478, qs, CHAMPAGNE if bg != CHAMPAGNE
                      else CREAM, bg if bg != CHAMPAGNE else CHARCOAL))
    ct, cs = cap(CONTACT["website"], maxw=W - 2 * SAFE, size=8.4)
    t, _ = text("light", ct, cs, W / 2, 556, ink, tracking=0.05,
                anchor="middle", opacity=caption_op)
    p.append(t)
    t, _ = text("light", CONTACT["licence"], 7.0, W / 2, 578, ink,
                tracking=0.1, anchor="middle", opacity=licence_op)
    p.append(t)
    return "".join(p)


def design_s1():
    """S1 - Softened, dark. Monolith with every hard edge taken off it."""
    return _soft_body(SOFT_DARK, CHAMPAGNE, GOLD, GOLD)


def design_s2():
    """S2 - Softened, light. The same panel on champagne."""
    return _soft_body(CHAMPAGNE, CHARCOAL, "#9C7A42", "#9C7A42",
                      services_op=0.62, caption_op=0.6, licence_op=0.42)


def design_s3():
    """S3 - Softened, serif-led. The quietest of the set."""
    p = [flood(CREAM)]

    mark, _ = lockup(W / 2, 152, 112, CHARCOAL, "#9C7A42", k_fill="#9C7A42")
    p.append(mark)

    for i, line in enumerate(("RENOVATION", "IN PROGRESS")):
        t, _ = text("serif-light", line, 44, W / 2, 262 + i * 48, CHARCOAL,
                    tracking=0.13, anchor="middle")
        p.append(t)

    p.append(soft_rule(W / 2, 348, 18, "#9C7A42"))

    t, _ = text("light", "INTERIOR DESIGN  ·  RENOVATION  ·  PROJECT MANAGEMENT",
                7.4, W / 2, 380, CHARCOAL, tracking=0.10, anchor="middle",
                opacity=0.6)
    p.append(t)

    t, _ = text("medium", CONTACT["phone"], 34, W / 2, 432, CHARCOAL,
                tracking=0.01, anchor="middle")
    p.append(t)
    t, _ = text("light", CONTACT["website"], 14.5, W / 2, 458, CHARCOAL,
                tracking=0.02, anchor="middle", opacity=0.68)
    p.append(t)

    qs = 58
    p.append(qr_block(W / 2 - qs / 2, 472, qs, CREAM, CHARCOAL))
    ct, cs = cap(CONTACT["website"], maxw=W - 2 * SAFE, size=8.4)
    t, _ = text("light", ct, cs, W / 2, 550, CHARCOAL, tracking=0.05,
                anchor="middle", opacity=0.55)
    p.append(t)
    t, _ = text("light", CONTACT["licence"], 7.0, W / 2, 574, CHARCOAL,
                tracking=0.1, anchor="middle", opacity=0.4)
    p.append(t)
    return "".join(p)


def design_s4():
    """S4 - Softened, two-tone. Warm charcoal above, champagne below."""
    split = 356.0
    p = [flood(CHAMPAGNE)]
    p.append(flood(SOFT_DARK, y=-BLEED, h=split + BLEED))

    mark, _ = lockup(W / 2, 168, 156, CHAMPAGNE, GOLD, k_fill=GOLD)
    p.append(mark)
    p.append(soft_rule(W / 2, 226, 20, GOLD))

    for i, line in enumerate(("RENOVATION", "IN PROGRESS")):
        t, _ = text("serif-light", line, 34, W / 2, 268 + i * 38, CHAMPAGNE,
                    tracking=0.13, anchor="middle")
        p.append(t)

    t, _ = text("serif", "ENQUIRIES", 15, W / 2, 392, "#9C7A42", tracking=0.18,
                anchor="middle")
    p.append(t)
    t, _ = text("medium", CONTACT["phone"], 34, W / 2, 428, CHARCOAL,
                tracking=0.01, anchor="middle")
    p.append(t)
    t, _ = text("light", CONTACT["website"], 14.5, W / 2, 452, CHARCOAL,
                tracking=0.02, anchor="middle", opacity=0.7)
    p.append(t)

    qs = 58
    p.append(qr_block(W / 2 - qs / 2, 468, qs, CREAM, CHARCOAL))
    ct, cs = cap(CONTACT["website"], maxw=W - 2 * SAFE, size=8.4)
    t, _ = text("light", ct, cs, W / 2, 548, CHARCOAL, tracking=0.05,
                anchor="middle", opacity=0.6)
    p.append(t)
    t, _ = text("light", CONTACT["licence"], 7.0, W / 2, 572, CHARCOAL,
                tracking=0.1, anchor="middle", opacity=0.42)
    p.append(t)
    return "".join(p)


def _soft_case_body(upper):
    """S5 - the softened light panel with the sentence case removed.

    Lyda's note: sentence case is out, it should be all caps or all lower. That
    rule is applied down the whole panel, not just the headline, so the headline,
    the services line and the enquiries label all move together. The website
    address, the Instagram handle and the licence number stay as they are; they
    are literal strings rather than styled copy, and an uppercased handle reads
    as a different handle.

    Set in Cormorant Garamond either way. Capitals need tracking to breathe and
    run wide, so they break over two lines at 40, which lands on exactly the same
    25 mm cap height as the sentence-case version. Lower case fits one line at 38.
    """
    ink, accent = CHARCOAL, "#9C7A42"
    p = [flood(CHAMPAGNE)]

    if upper:
        mark, _ = lockup(W / 2, 178, 158, ink, accent, k_fill=accent)
        p.append(mark)
        p.append(soft_rule(W / 2, 238, 22, accent))

        for i, line in enumerate(("RENOVATION", "IN PROGRESS")):
            t, _ = text("serif-light", line, 40, W / 2, 282 + i * 44, ink,
                        tracking=0.13, anchor="middle")
            p.append(t)

        t, _ = text("light",
                    "INTERIOR DESIGN  ·  RENOVATION  ·  PROJECT MANAGEMENT",
                    7.4, W / 2, 358, ink, tracking=0.10, anchor="middle",
                    opacity=0.6)
        p.append(t)

        t, _ = text("serif", "ENQUIRIES", 16, W / 2, 398, accent, tracking=0.18,
                    anchor="middle")
        p.append(t)
        phone_y, web_y, qy, qs = 436, 462, 480, 58
        cap_y, lic_y = 556, 578
    else:
        mark, _ = lockup(W / 2, 190, 158, ink, accent, k_fill=accent)
        p.append(mark)
        p.append(soft_rule(W / 2, 252, 22, accent))

        t, _ = text("serif-light", "renovation in progress", 38, W / 2, 302, ink,
                    tracking=0.015, anchor="middle")
        p.append(t)
        t, _ = text("light",
                    "interior design  ·  renovation  ·  project management",
                    8.6, W / 2, 334, ink, tracking=0.05, anchor="middle",
                    opacity=0.62)
        p.append(t)

        t, _ = text("serif", "enquiries", 17, W / 2, 380, accent, tracking=0.02,
                    anchor="middle")
        p.append(t)
        phone_y, web_y, qy, qs = 420, 448, 468, 58
        cap_y, lic_y = 550, 574

    t, _ = text("medium", CONTACT["phone"], 38, W / 2, phone_y, ink,
                tracking=0.01, anchor="middle")
    p.append(t)
    t, _ = text("light", CONTACT["website"], 15.1, W / 2, web_y, accent,
                tracking=0.02, anchor="middle")
    p.append(t)

    p.append(qr_block(W / 2 - qs / 2, qy, qs, CREAM, CHARCOAL))
    ct, cs = cap(CONTACT["website"], maxw=W - 2 * SAFE, size=8.4)
    t, _ = text("light", ct, cs, W / 2, cap_y, ink, tracking=0.05,
                anchor="middle", opacity=0.6)
    p.append(t)
    t, _ = text("light", CONTACT["licence"], 7.0, W / 2, lic_y, ink,
                tracking=0.1, anchor="middle", opacity=0.42)
    p.append(t)
    return "".join(p)


def design_s5_upper():
    """S5a - all capitals, broken over two lines."""
    return _soft_case_body(upper=True)


def design_s5_lower():
    """S5b - all lower case, one line."""
    return _soft_case_body(upper=False)



# --------------------------------------------------- round four: boutique ----
#
# Brief: less corporate, more boutique. What reads corporate in the set so far is
# specific and removable:
#
#   the centred axis      everything stacked dead centre, evenly weighted
#   the services list     "INTERIOR DESIGN · RENOVATION · PROJECT MANAGEMENT"
#   the call to action    an ENQUIRIES label sitting over a bold sans number
#   full-width bands      colour fields running edge to edge
#   density               five or six pieces of information competing
#
# So these four drop the services list, set the number in Cormorant Garamond
# rather than bold Inter, use asymmetry or a contained panel instead of bands,
# and carry noticeably less copy. The headline moves to italic lower case, which
# is the boutique voice and also respects the no-sentence-case rule.
#
# No new colours: the palette is the same champagne, cream, warm charcoal and
# gold. Boutique here comes from space, asymmetry and type, not from decoration.
#
# The trade: a serif number at 32 to 36 has a cap height around 20 to 22 mm and
# reads at roughly 2.4 to 2.7 m, against 3.3 m for the softened set. These are
# gate-and-doorstep signs rather than across-the-street signs.

ITAL = "serif-italic-light"


def rotated(svg, deg, cx, cy):
    return f'<g transform="rotate({deg} {cx} {cy})">{svg}</g>'


def design_b1():
    """B1 - Atelier. Asymmetric, left-aligned, mostly empty."""
    lx = 52.0
    p = [flood(CREAM)]

    ink_start, ink_w = lk_ink(76)
    mark, _ = lockup(lx + ink_w / 2, 128, 76, CHARCOAL, "#9C7A42",
                     k_fill="#9C7A42")
    p.append(mark)

    for i, line in enumerate(("a considered renovation", "in progress")):
        t, _ = text(ITAL, line, 34, lx, 292 + i * 44, CHARCOAL, tracking=0.01)
        p.append(t)

    p.append(soft_rule(lx + 15, 372, 15, "#9C7A42"))

    t, _ = text("serif-medium", CONTACT["phone"], 32, lx, 448, CHARCOAL,
                tracking=0.02)
    p.append(t)
    t, _ = text("serif-light", CONTACT["website"], 16.2, lx, 474, CHARCOAL,
                tracking=0.02, opacity=0.8)
    p.append(t)
    t, _ = text("light", CONTACT["licence"], 7.0, lx, 560, CHARCOAL,
                tracking=0.1, opacity=0.4)
    p.append(t)

    qs = 60
    qx = W - lx - qs
    p.append(qr_block(qx, 424, qs, CREAM, CHARCOAL))
    ct, cs = cap(CONTACT["website"], maxw=qs + 46, size=8.4)
    t, _ = text("light", ct, cs, qx + qs / 2, 500, CHARCOAL, tracking=0.04,
                anchor="middle", opacity=0.5)
    p.append(t)
    return "".join(p)


def design_b2():
    """B2 - Invitation. A fine keyline held well in, and very little inside it."""
    p = [flood(CHAMPAGNE)]
    p.append(f'<rect x="26" y="26" width="{W-52}" height="{H-52}" fill="none" '
             f'stroke="#9C7A42" stroke-width="0.45" stroke-opacity="0.55"/>')

    mark, _ = lockup(W / 2, 178, 118, CHARCOAL, "#9C7A42", k_fill="#9C7A42")
    p.append(mark)

    t, _ = text(ITAL, "renovation in progress", 34, W / 2, 272, CHARCOAL,
                tracking=0.01, anchor="middle")
    p.append(t)
    p.append(soft_rule(W / 2, 304, 13, "#9C7A42"))

    t, _ = text("serif", "ENQUIRIES", 9.5, W / 2, 344, "#9C7A42", tracking=0.3,
                anchor="middle")
    p.append(t)
    t, _ = text("serif-medium", CONTACT["phone"], 36, W / 2, 388, CHARCOAL,
                tracking=0.02, anchor="middle")
    p.append(t)
    t, _ = text("serif-light", CONTACT["website"], 16.2, W / 2, 414, CHARCOAL,
                tracking=0.02, anchor="middle", opacity=0.8)
    p.append(t)

    qs = 60
    p.append(qr_block(W / 2 - qs / 2, 432, qs, CHAMPAGNE, CHARCOAL))
    ct, cs = cap(CONTACT["website"], maxw=W - 2 * SAFE, size=8.4)
    t, _ = text("light", ct, cs, W / 2, 510, CHARCOAL, tracking=0.04,
                anchor="middle", opacity=0.5)
    p.append(t)
    t, _ = text("light", CONTACT["licence"], 7.0, W / 2, 536, CHARCOAL,
                tracking=0.1, anchor="middle", opacity=0.4)
    p.append(t)
    return "".join(p)


def design_b3():
    """B3 - Label. A champagne label set into a warm dark field."""
    p = [flood(SOFT_DARK)]

    mark, _ = lockup(W / 2, 178, 146, CHAMPAGNE, GOLD, k_fill=GOLD)
    p.append(mark)

    lx, ly, lw, lh = 48.0, 276.0, W - 96.0, 282.0
    p.append(f'<rect x="{lx}" y="{ly}" width="{lw}" height="{lh}" '
             f'fill="{CHAMPAGNE}" rx="3"/>')

    t, _ = text(ITAL, "renovation in progress", 30, W / 2, 326, CHARCOAL,
                tracking=0.01, anchor="middle")
    p.append(t)
    p.append(soft_rule(W / 2, 352, 12, "#9C7A42"))

    t, _ = text("serif-medium", CONTACT["phone"], 34, W / 2, 394, CHARCOAL,
                tracking=0.02, anchor="middle")
    p.append(t)
    t, _ = text("serif-light", CONTACT["website"], 15.1, W / 2, 418, CHARCOAL,
                tracking=0.02, anchor="middle", opacity=0.8)
    p.append(t)

    qs = 56
    p.append(qr_block(W / 2 - qs / 2, 432, qs, CHAMPAGNE, CHARCOAL))
    ct, cs = cap(CONTACT["website"], maxw=lw - 30, size=8.4)
    t, _ = text("light", ct, cs, W / 2, 506, CHARCOAL, tracking=0.04,
                anchor="middle", opacity=0.5)
    p.append(t)
    t, _ = text("light", CONTACT["licence"], 7.0, W / 2, 530, CHARCOAL,
                tracking=0.1, anchor="middle", opacity=0.42)
    p.append(t)
    return "".join(p)


def design_spine(dark=False, upper=False):
    """B4 - Spine. The services run vertically down the left edge.

    Four variants: light or warm dark ground, headline in italic lower case or
    in roman capitals over two lines. Putting the services on the spine is what
    lets the face of the panel stay boutique: the list is still there for anyone
    who wants it, but it is no longer a middle-dot row across the middle of the
    composition.
    """
    if dark:
        bg, ink, accent = SOFT_DARK, CHAMPAGNE, GOLD
        qr_light, qr_dark = CHAMPAGNE, SOFT_DARK
    else:
        bg, ink, accent = CHAMPAGNE, CHARCOAL, "#9C7A42"
        qr_light, qr_dark = CHAMPAGNE, CHARCOAL

    cx, sx = 218.0, 40.0
    p = [flood(bg)]

    spine, _ = text("serif",
                    "INTERIOR DESIGN  ·  RENOVATION  ·  PROJECT MANAGEMENT",
                    11, sx, 300, accent, tracking=0.3, anchor="middle")
    p.append(rotated(spine, -90, sx, 300))

    # finishing ticks above and below the spine, clear of its baseline
    for y0, y1 in ((44, 78), (522, 556)):
        p.append(f'<line x1="{sx}" y1="{y0}" x2="{sx}" y2="{y1}" '
                 f'stroke="{accent}" stroke-width="0.5" stroke-opacity="0.45" '
                 f'stroke-linecap="round"/>')

    if upper:
        mark, _ = lockup(cx, 190, 150, ink, accent, k_fill=accent)
        p.append(mark)
        for i, line in enumerate(("RENOVATION", "IN PROGRESS")):
            t, _ = text("serif-light", line, 34, cx, 286 + i * 42, ink,
                        tracking=0.13, anchor="middle")
            p.append(t)
        rule_y, phone_y, web_y, qy = 356, 410, 436, 454
        cap_y, lic_y = 530, 558
    else:
        mark, _ = lockup(cx, 200, 150, ink, accent, k_fill=accent)
        p.append(mark)
        t, _ = text(ITAL, "renovation in progress", 34, cx, 300, ink,
                    tracking=0.01, anchor="middle")
        p.append(t)
        rule_y, phone_y, web_y, qy = 330, 396, 422, 442
        cap_y, lic_y = 518, 548

    p.append(soft_rule(cx, rule_y, 13, accent))

    t, _ = text("serif-medium", CONTACT["phone"], 34, cx, phone_y, ink,
                tracking=0.02, anchor="middle")
    p.append(t)
    t, _ = text("serif-light", CONTACT["website"], 15.1, cx, web_y, ink,
                tracking=0.02, anchor="middle", opacity=0.8)
    p.append(t)

    qs = 60
    p.append(qr_block(cx - qs / 2, qy, qs, qr_light, qr_dark))
    ct, cs = cap(CONTACT["website"], maxw=170, size=8.4)
    t, _ = text("light", ct, cs, cx, cap_y, ink, tracking=0.04,
                anchor="middle", opacity=0.55)
    p.append(t)
    t, _ = text("light", CONTACT["licence"], 7.0, cx, lic_y, ink,
                tracking=0.1, anchor="middle", opacity=0.42)
    p.append(t)
    return "".join(p)


def design_b4a():
    return design_spine(dark=False, upper=False)


def design_b4b():
    return design_spine(dark=False, upper=True)


def design_b4c():
    return design_spine(dark=True, upper=False)


def design_b4d():
    return design_spine(dark=True, upper=True)



# ------------------------------------------------- round five: simplest ----
#
# Reference images from Lyda: a Laura Abrams Design A-frame (monogram left, name
# right, a hairline row of services and a small QR along the bottom) and a
# Georgie Shepherd Interior Studio panel hung on a picket fence by eyelets, which
# carries the name at the top, the words INTERIOR STUDIO at the bottom, and
# nothing whatsoever in between. No phone, no web address, no QR.
#
# What makes those work is not a style, it is subtraction. One type block at the
# top, one at the bottom, and a void doing the rest. So these four reduce to a
# single contact route each and give up the headline, the services and (on three
# of the four) the QR.
#
# The honest cost: a sign with one contact route and no QR is a brand statement
# rather than a lead generator. M4 keeps a small QR for anyone who wants the
# reduction without losing the scan.
#
# Square corners on all four, since both references are square, and both hang
# rather than sit. Eyelets instead of drilled holes are covered in the spec.


def _minimal(bg, ink, accent, lk_size, mark_baseline, lines, qr=None,
             licence_y=560):
    """One type block at the top, one at the bottom, and a large void between.

    `lines` is a list of (face, text, size, y, opacity) drawn as the bottom block.
    """
    p = [flood(bg)]

    mark, _ = lockup(W / 2, mark_baseline, lk_size, ink, accent, k_fill=accent)
    p.append(mark)

    for face, txt, size, y, op in lines:
        t, _ = text(face, txt, size, W / 2, y, ink, tracking=0.04,
                    anchor="middle", opacity=op)
        p.append(t)

    if qr:
        qs, qy = qr
        p.append(qr_block(W / 2 - qs / 2, qy, qs, bg, ink))

    t, _ = text("light", CONTACT["licence"], 7.0, W / 2, licence_y, ink,
                tracking=0.1, anchor="middle", opacity=0.34)
    p.append(t)
    return "".join(p)


def design_m1():
    """M1 - Hanging. The Georgie Shepherd reduction: mark, void, one address."""
    return _minimal(WHITE, CHARCOAL, "#9C7A42", 150, 172,
                    [("light", CONTACT["website"], 15, 520, 0.75)])


def design_m2():
    """M2 - Two blocks. Mark at the top, number and address at the foot."""
    return _minimal(WHITE, CHARCOAL, "#9C7A42", 150, 172,
                    [("medium", CONTACT["phone"], 30, 502, None),
                     ("light", CONTACT["website"], 13.5, 528, 0.7)])


def design_m3():
    """M3 - Centred. The mark optically centred, one line beneath it."""
    return _minimal(CREAM, CHARCOAL, "#9C7A42", 170, 338,
                    [("light", CONTACT["website"], 14, 470, 0.7)])


def design_m4():
    """M4 - Simplest with a scan. The same reduction, QR kept."""
    return _minimal(CHAMPAGNE, CHARCOAL, "#9C7A42", 140, 168,
                    [("medium", CONTACT["phone"], 28, 438, None),
                     ("light", CONTACT["website"], 13, 462, 0.7)],
                    qr=(60, 480), licence_y=568)


def design_m1q():
    """M1 with a code. Mark, void, code, address."""
    return _minimal(WHITE, CHARCOAL, "#9C7A42", 150, 172,
                    [("light", CONTACT["website"], 15, 540, 0.75)],
                    qr=(60, 452), licence_y=572)


def design_m2q():
    """M2 with a code. Code above the number and address."""
    return _minimal(WHITE, CHARCOAL, "#9C7A42", 150, 172,
                    [("medium", CONTACT["phone"], 30, 524, None),
                     ("light", CONTACT["website"], 13.5, 548, 0.7)],
                    qr=(60, 426), licence_y=576)


def design_m3q():
    """M3 with a code. Centred mark, address, then the code beneath it."""
    return _minimal(CREAM, CHARCOAL, "#9C7A42", 170, 338,
                    [("light", CONTACT["website"], 14, 480, 0.7)],
                    qr=(60, 494), licence_y=576)


# (key, label, builder, corner radius in mm)
DESIGNS = [
    ("m1-hanging", "Hanging", design_m1, 0.0),
    ("m2-two-blocks", "Two Blocks", design_m2, 0.0),
    ("m3-centred", "Centred", design_m3, 0.0),
    ("m1-hanging-qr", "Hanging, with QR", design_m1q, 0.0),
    ("m2-two-blocks-qr", "Two Blocks, with QR", design_m2q, 0.0),
    ("m3-centred-qr", "Centred, with QR", design_m3q, 0.0),
    ("m4-simple-qr", "Simplest with QR", design_m4, 0.0),
    ("s1-soft-dark", "Softened Dark", design_s1, 20.0),
    ("s2-soft-light", "Softened Light", design_s2, 20.0),
    ("s3-soft-serif", "Softened Serif", design_s3, 20.0),
    ("s4-soft-twotone", "Softened Two-tone", design_s4, 20.0),
    ("s5b-lower", "Lower case reference", design_s5_lower, 20.0),
    ("b1-atelier", "Atelier", design_b1, 20.0),
    ("b2-invitation", "Invitation", design_b2, 20.0),
    ("b3-label", "Label", design_b3, 20.0),
    ("b4a-spine-light", "Spine, light", design_b4a, 20.0),
    ("b4b-spine-light-caps", "Spine, light, capitals", design_b4b, 20.0),
    ("b4c-spine-dark", "Spine, dark", design_b4c, 20.0),
    ("b4d-spine-dark-caps", "Spine, dark, capitals", design_b4d, 20.0),
    ("a-monolith", "Monolith", design_a, 0.0),
    ("b-champagne", "Champagne", design_b, 0.0),
    ("c-split", "Split Panel", design_c, 0.0),
    ("d-blueprint", "Blueprint", design_d, 0.0),
    ("e-contact", "Contact First", design_e, 0.0),
    ("f-plaque", "Plaque", design_f, 0.0),
    ("g-editorial", "Editorial", design_g, 0.0),
    ("h-nightfall", "Nightfall", design_h, 0.0),
    ("i-kerbside", "Kerbside", design_i, 0.0),
]


# ------------------------------------------------------------- wrappers ----

def wrap(body, bleed=True, marks=False, radius=0.0, uid="x"):
    """radius is the routed corner radius. The print files stay a full-bleed
    rectangle (the router cuts the curve); the preview clips to it so the panel
    is shown as it will actually look, and the guide layer draws it as a cut line."""
    if bleed:
        vb, w, h = f"{-BLEED} {-BLEED} {W+2*BLEED} {H+2*BLEED}", W + 2 * BLEED, H + 2 * BLEED
    else:
        vb, w, h = f"0 0 {W} {H}", W, H
    rx = f' rx="{radius}"' if radius else ""
    if radius and not bleed:
        body = (f'<defs><clipPath id="trim-{uid}">'
                f'<rect x="0" y="0" width="{W}" height="{H}"{rx}/></clipPath></defs>'
                f'<g clip-path="url(#trim-{uid})">{body}</g>')
    extra = ""
    if marks:
        m = [f'<g stroke="#FF00FF" stroke-width="0.3" fill="none">']
        # trim / cut outline + drill holes, guide layer only
        m.append(f'<rect x="0" y="0" width="{W}" height="{H}"{rx} '
                 f'stroke-dasharray="4 3"/>')
        m.append(f'<rect x="{SAFE}" y="{SAFE}" width="{W-2*SAFE}" '
                 f'height="{H-2*SAFE}" stroke="#00AEEF" stroke-dasharray="2 3"/>')
        for hx, hy in ((30, 30), (W - 30, 30), (30, H - 30), (W - 30, H - 30),
                       (30, H / 2), (W - 30, H / 2)):
            m.append(f'<circle cx="{hx}" cy="{hy}" r="3" stroke="#00AEEF"/>')
        m.append("</g>")
        extra = "".join(m)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}mm" height="{h}mm" '
            f'viewBox="{vb}">{body}{extra}</svg>')


def run(cmd):
    subprocess.run(cmd, check=True)


def qr_swatch(variant, size=72.0, light=CHAMPAGNE, dark=INK):
    """Standalone QR at `size` mm — used for the QR detail on the review page."""
    v = QR_VARIANTS[variant]
    body = qr_block(0, 0, size, light, dark, url=v["url"], style=v["style"])
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}mm" '
            f'height="{size}mm" viewBox="0 0 {size} {size}">{body}</svg>')


def main():
    global ACTIVE
    for sub in ("print-svg", "print-pdf", "print-png", "preview", "guides"):
        os.makedirs(os.path.join(OUT, sub), exist_ok=True)

    for variant in QR_VARIANTS:
        ACTIVE = QR_VARIANTS[variant]
        print(f"\n{variant.upper()} QR → {ACTIVE['url']}")

        for key, label, fn, radius in DESIGNS:
            body = fn()
            stem = f"lk-site-sign-400x600-{key}-{variant}"
            uid = f"{key}-{variant}"

            print_svg = os.path.join(OUT, "print-svg", f"{stem}-print-bleed.svg")
            with open(print_svg, "w") as fh:
                fh.write(wrap(body, bleed=True, radius=radius, uid=uid))

            guide_svg = os.path.join(OUT, "guides", f"{stem}-guides.svg")
            with open(guide_svg, "w") as fh:
                fh.write(wrap(body, bleed=True, marks=True, radius=radius,
                              uid=uid))

            prev_svg = os.path.join(OUT, "preview", f"{stem}.svg")
            with open(prev_svg, "w") as fh:
                fh.write(wrap(body, bleed=False, radius=radius, uid=uid))

            pdf = os.path.join(OUT, "print-pdf", f"{stem}-print-bleed.pdf")
            run(["rsvg-convert", "-f", "pdf", "-o", pdf, print_svg])

            png = os.path.join(OUT, "print-png", f"{stem}-300dpi.png")
            run(["rsvg-convert", "-f", "png", "-d", "300", "-p", "300",
                 "-o", png, print_svg])

            small = os.path.join(OUT, "preview", f"{stem}-900px.png")
            run(["rsvg-convert", "-f", "png", "-w", "900", "-o", small, prev_svg])

            print(f"  ✓ {label:<14} {stem}")

    for variant in QR_VARIANTS:
        path = os.path.join(OUT, "preview", f"qr-detail-{variant}.svg")
        with open(path, "w") as fh:
            fh.write(qr_swatch(variant))

    ACTIVE = QR_VARIANTS["web"]
    print(f"\nOutput: {OUT}")


if __name__ == "__main__":
    main()
