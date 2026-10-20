#!/usr/bin/env python3
"""
Builds the client review page for the site-sign options.

Inlines the preview SVGs and subsetted brand fonts so the page is fully
self-contained (no external requests), then writes:

    assets/branding/final/signage/review.html
"""

import base64
import os
import subprocess
import tempfile

import generate_site_sign as g

HERE = os.path.dirname(os.path.abspath(__file__))
SIGNAGE = os.path.join(HERE, "assets", "branding", "final", "signage")
OUT = os.path.join(SIGNAGE, "review.html")

# Which QR set the option previews show.
VARIANT = "insta"

GLYPHS = ("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
          "0123456789 .,:;'\"!?()[]–-/@&%+×·°→_")


def font_data_uri(path):
    """Subset a font to the glyphs this page uses and return a woff2 data URI."""
    with tempfile.NamedTemporaryFile(suffix=".woff2", delete=False) as tmp:
        out = tmp.name
    subprocess.run([
        "pyftsubset", path,
        f"--text={GLYPHS}",
        "--flavor=woff2",
        "--layout-features=kern,liga",
        f"--output-file={out}",
    ], check=True)
    with open(out, "rb") as fh:
        b64 = base64.b64encode(fh.read()).decode()
    os.unlink(out)
    return f"data:font/woff2;base64,{b64}"


def lockup_svg():
    """Small outlined LK lockup for the page header, themed via currentColor."""
    f = g.Face.get("mono")
    size = 100.0
    s = size / f.upm
    ink_start, ink_w = g.lk_ink(size)
    cx = ink_start + ink_w / 2
    x = 0.0
    parts = []
    for ch, fill in (("L", "currentColor"), ("K", "var(--gold)")):
        parts.append(f'<path fill="{fill}" d="{f.path_d(ch)}" '
                     f'transform="translate({x:.3f} 0) scale({s:.6f} {-s:.6f})"/>')
        x += f.advance(ch) * s + g.LK_TRACK * size
    tag, _ = g.text(g.TAG_FACE, g.TAGLINE, size * g.TAG_RATIO, cx,
                    size * g.TAG_GAP, "var(--gold)",
                    tracking=g.TAG_TRACK, anchor="middle")
    parts.append(tag)
    return (f'<svg class="lockup" viewBox="-2 {-size*0.62} {x+4} {size*0.78}" '
            f'role="img" aria-label="LK Design and Build">{"".join(parts)}</svg>')


def svg_inline(path, cls):
    with open(path) as fh:
        svg = fh.read()
    return svg.replace(
        "<svg ", f'<svg class="{cls}" preserveAspectRatio="xMidYMid meet" ', 1)


def panel(key):
    return svg_inline(
        os.path.join(SIGNAGE, "preview",
                     f"lk-site-sign-400x600-{key}-{VARIANT}.svg"), "panel")


def qr_detail(variant):
    return svg_inline(os.path.join(SIGNAGE, "preview",
                                   f"qr-detail-{variant}.svg"), "qr")


# ---------------------------------------------------------------- content ----

OPTIONS = [
    dict(key="m1-hanging", n="Hanging", round=6,
         line="The Georgie Shepherd reduction. Mark at the top, a single web "
              "address at the foot, and a large void doing the rest of the work.",
         ground="White", hero="LK mark, 86 mm cap",
         read="Mark 10.3 m, address 1.8 m",
         best="The purest of the set. A brand statement, not a lead generator, "
              "and it knows it."),
    dict(key="m1-hanging-qr", n="Hanging, with QR", round=6,
         line="The same panel with a 60 mm code above the address.",
         ground="White", hero="LK mark, 86 mm cap",
         read="Mark 10.3 m, address 1.8 m",
         best="Keeps the purity and adds the one thing it was missing."),
    dict(key="m2-two-blocks", n="Two Blocks", round=6,
         line="The same reduction with the number added, so the foot carries "
              "two lines instead of one.",
         ground="White", hero="LK mark, 86 mm cap",
         read="Mark 10.3 m, number 2.6 m",
         best="Minimal without giving up the phone. The version I would print "
              "of these four."),
    dict(key="m2-two-blocks-qr", n="Two Blocks, with QR", round=6,
         line="Code, then number, then address, stacked at the foot.",
         ground="White", hero="LK mark, 86 mm cap",
         read="Mark 10.3 m, number 2.6 m",
         best="Everything a site sign needs and nothing it does not. My pick of "
              "the eight."),
    dict(key="m3-centred", n="Centred", round=6,
         line="The mark optically centred in the panel with one line beneath "
              "it, so the void sits above and below rather than in the middle.",
         ground="Cream", hero="LK mark, 97 mm cap",
         read="Mark 11.7 m, address 1.7 m",
         best="The most confident composition. Closest to a plaque on a "
              "finished house."),
    dict(key="m3-centred-qr", n="Centred, with QR", round=6,
         line="Centred mark, address, and the code beneath it, so the foot "
              "stays symmetrical.",
         ground="Cream", hero="LK mark, 97 mm cap",
         read="Mark 11.7 m, address 1.7 m",
         best="The plaque composition with a way in for anyone curious."),
    dict(key="m4-simple-qr", n="Simplest with QR", round=6,
         line="The same reduction with the number, the address and a small code "
              "kept at the foot.",
         ground="Champagne", hero="LK mark, 80 mm cap",
         read="Mark 9.6 m, number 2.4 m",
         best="For keeping the scan without the panel getting busy again."),
    dict(key="b1-atelier", n="Atelier", round=4,
         line="Left-aligned and mostly empty, with the mark held small in the "
              "top corner and the line set in italic lower case.",
         ground="Cream", hero="Italic headline, 21 mm cap",
         read="Headline 2.5 m, number 2.4 m",
         best="The least sign-like of everything here. Reads as a studio's "
              "calling card left on the fence."),
    dict(key="b2-invitation", n="Invitation", round=4,
         line="A fine keyline held well in from the edge with very little "
              "inside it. The proportions of a printed invitation.",
         ground="Champagne", hero="Italic headline, 21 mm cap",
         read="Headline 2.6 m, number 2.7 m",
         best="Formal without being corporate. The most classical of the four "
              "and the easiest to love."),
    dict(key="b3-label", n="Label", round=4,
         line="A champagne label set into a warm dark field, so the detail sits "
              "on its own surface rather than floating on the panel.",
         ground="Warm charcoal with champagne label",
         hero="Italic headline, 19 mm cap",
         read="Headline 2.3 m, number 2.6 m",
         best="Keeps the dark presence while staying boutique. The label device "
              "is the most distinctive idea in this round."),
    dict(key="b4a-spine-light", n="Spine, light", round=4,
         line="The services run vertically down the left edge, which keeps the "
              "list available without putting a middle-dot row across the middle "
              "of the composition. Headline in italic lower case.",
         ground="Champagne", hero="Italic headline, 21 mm cap",
         read="Headline 2.6 m, number 2.6 m",
         best="Boutique retail. The vertical spine is the detail people notice "
              "up close, and it earns its place by carrying real information."),
    dict(key="b4b-spine-light-caps", n="Spine, light, capitals", round=4,
         line="The same panel with the headline in roman capitals over two "
              "lines, which is steadier and agrees with the lockup's own "
              "capitals.",
         ground="Champagne", hero="Capitals, 21 mm cap",
         read="Headline 2.6 m, number 2.6 m",
         best="The version to print if the italic reads as too soft for a "
              "building site."),
    dict(key="b4c-spine-dark", n="Spine, dark", round=4,
         line="Warm charcoal ground with the mark and spine in gold and "
              "champagne. Italic lower case headline.",
         ground="Warm charcoal", hero="Italic headline, 21 mm cap",
         read="Headline 2.6 m, number 2.6 m",
         best="The most expensive-looking panel in the whole set, and the best "
              "of these to photograph."),
    dict(key="b4d-spine-dark-caps", n="Spine, dark, capitals", round=4,
         line="Warm charcoal with the headline in roman capitals. The most "
              "formal of the four spines.",
         ground="Warm charcoal", hero="Capitals, 21 mm cap",
         read="Headline 2.6 m, number 2.6 m",
         best="Boutique presence with none of the softness. Closest of the "
              "boutique round to the original Monolith brief."),
    dict(key="s5b-lower", n="Lower case reference", round=5,
         line="The same panel set entirely in lower case, kept as a reference "
              "in case the decision is worth revisiting. Not part of the set.",
         ground="Champagne", hero="Headline, 24 mm cap",
         read="Headline 2.9 m, number 3.3 m",
         best="Comparison only. Softer and more contemporary, but it puts a "
              "second voice directly under the capitals in the lockup."),
    dict(key="s1-soft-dark", n="Softened Dark", round=3,
         line="Monolith with every hard edge taken off it: no frame, warm "
              "charcoal instead of near-black, and the headline in Cormorant "
              "Garamond capitals over two lines.",
         ground="Warm charcoal", hero="LK mark, 90 mm cap",
         read="Mark 10.8 m, number 3.3 m",
         best="The direct answer to the feedback. Same panel, none of the "
              "structure."),
    dict(key="s2-soft-light", n="Softened Light", round=3,
         line="The identical layout on champagne, with charcoal type and a "
              "deeper gold that holds its contrast on a light ground.",
         ground="Champagne", hero="LK mark, 90 mm cap",
         read="Mark 10.8 m, number 3.3 m",
         best="Side-by-side comparison with Softened Dark. This is the one I "
              "would print."),
    dict(key="s3-soft-serif", n="Softened Serif", round=3,
         line="The quietest of the set. The mark steps back and the serif "
              "capitals become the thing you read first.",
         ground="Cream", hero="Serif headline, 34 mm cap",
         read="Headline 4.1 m, number 3 m",
         best="If the sign should feel like an interiors studio rather than a "
              "building site. The softest option here."),
    dict(key="s4-soft-twotone", n="Softened Two-tone", round=3,
         line="Warm charcoal above, champagne below, with the hard gold divider "
              "removed so the two fields simply meet.",
         ground="Warm charcoal over champagne", hero="LK mark, 89 mm cap",
         read="Mark 10.7 m, number 3 m",
         best="Keeps the dark presence at eye level while the detail sits on a "
              "light ground. A middle path on the dark-or-light question."),
    dict(key="a-monolith", n="Monolith", round=1,
         line="A charcoal field with the mark oversized and everything else "
              "held quiet beneath it.",
         ground="Charcoal flood", hero="LK mark, 94 mm cap",
         read="Mark 11 m, number 3.5 m",
         best="Maximum brand presence. Reads as a finished building's plaque "
              "rather than a builder's board."),
    dict(key="b-champagne", n="Champagne", round=1,
         line="The light counterpart, with gold bands top and bottom holding "
              "the panel together against a dark fence.",
         ground="Champagne", hero="LK mark, 90 mm cap",
         read="Mark 11 m, number 3.4 m",
         best="Dark or colourbond fences, and shaded frontages where a black "
              "panel would disappear."),
    dict(key="c-split", n="Split Panel", round=1,
         line="Identity above, information below. The site-board convention, "
              "done properly.",
         ground="Charcoal over champagne", hero="LK mark, 96 mm cap",
         read="Mark 11 m, number 2.9 m",
         best="When passers-by need the detail as well as the name. The safest "
              "all-round choice."),
    dict(key="d-blueprint", n="Blueprint", round=1,
         line="A drafting sheet: 20 mm grid, registration ticks, dimension "
              "line under the mark, spec-table contact block.",
         ground="Charcoal with gold grid", hero="LK mark, 91 mm cap",
         read="Mark 11 m, number 1.5 m",
         best="Leaning on the design half of Design and Build. Rewards a close "
              "look, and is the least legible from distance."),
    dict(key="e-contact", n="Contact First", round=1,
         line="A gold call bar carrying the number, with the mark in a "
              "charcoal band above it.",
         ground="Champagne with gold bar", hero="Phone, 33 mm cap",
         read="Mark 7 m, number 4 m",
         best="Lead generation. The most commercial of the nine: effective, "
              "least restrained."),
    dict(key="f-plaque", n="Plaque", round=2,
         line="A charcoal plate inset on cream, with a Cormorant Garamond "
              "headline below it. An architect's plate, not a builder's board.",
         ground="Cream with charcoal plate", hero="LK mark, 67 mm cap",
         read="Mark 8 m, number 3.5 m",
         best="Heritage frontages and established streets. The plate device "
              "gives the mark its full clear space."),
    dict(key="g-editorial", n="Editorial", round=2,
         line="Asymmetric and left-aligned, with the serif line doing the "
              "talking and the mark held small at the top.",
         ground="Champagne", hero="Serif headline, 33 mm cap",
         read="Headline 4 m, number 2.6 m",
         best="The most distinctive option, and the closest to how the brand "
              "speaks. Message first, mark second."),
    dict(key="h-nightfall", n="Nightfall", round=2,
         line="Near-black, the mark given its full clear space, and nothing "
              "on the panel that does not need to be.",
         ground="Near black", hero="LK mark, 86 mm cap",
         read="Mark 10 m, number 3 m",
         best="Quiet luxury. The most restrained treatment, and the one that "
              "photographs best for the portfolio."),
    dict(key="i-kerbside", n="Kerbside", round=2,
         line="Legibility-led: the number is the largest element a 400 mm "
              "panel can physically carry, on the highest-contrast band.",
         ground="Cream with charcoal band", hero="Phone, 36 mm cap",
         read="Mark 7 m, number 4.4 m",
         best="Doing the job a site sign is actually for, without giving up "
              "the brand. The recommended starting point."),
]


def card(o):
    return f"""
      <article class="card">
        <div class="frame">{panel(o['key'])}</div>
        <div class="notes">
          <h3>{o['n']}</h3>
          <p class="lede">{o['line']}</p>
          <dl class="facts">
            <div><dt>Ground</dt><dd>{o['ground']}</dd></div>
            <div><dt>Dominant</dt><dd>{o['hero']}</dd></div>
            <div><dt>Reads from</dt><dd>{o['read']}</dd></div>
          </dl>
          <p class="best"><span>Best for</span>{o['best']}</p>
        </div>
      </article>"""


def build():
    serif = font_data_uri(os.path.join(HERE, "assets/fonts/CormorantGaramond-Light.ttf"))
    serif_m = font_data_uri(os.path.join(HERE, "assets/fonts/CormorantGaramond-Medium.ttf"))
    sans = font_data_uri(g.FONTS["light"])
    sans_m = font_data_uri(g.FONTS["medium"])

    r1 = "".join(card(o) for o in OPTIONS if o["round"] == 1)
    r2 = "".join(card(o) for o in OPTIONS if o["round"] == 2)
    r3 = "".join(card(o) for o in OPTIONS if o["round"] == 3)
    r5 = "".join(card(o) for o in OPTIONS if o["round"] == 5)
    r4 = "".join(card(o) for o in OPTIONS if o["round"] == 4)
    r6 = "".join(card(o) for o in OPTIONS if o["round"] == 6)

    html = f"""<title>LK Site Sign Options</title>
<style>
  @font-face {{ font-family: "CG"; src: url("{serif}") format("woff2");
    font-weight: 300; font-display: swap; }}
  @font-face {{ font-family: "CG"; src: url("{serif_m}") format("woff2");
    font-weight: 500; font-display: swap; }}
  @font-face {{ font-family: "IN"; src: url("{sans}") format("woff2");
    font-weight: 300; font-display: swap; }}
  @font-face {{ font-family: "IN"; src: url("{sans_m}") format("woff2");
    font-weight: 500; font-display: swap; }}

  /* Light palette: the brand's cream and charcoal world. */
  :root {{
    --ground: #F5F0EB;
    --surface: #FFFDF9;
    --ink: #2C2C2C;
    --muted: #6E655A;
    --faint: #A79C8D;
    --gold: #9C7A42;
    --gold-line: #C9A96E;
    --hair: rgba(44, 44, 44, 0.14);
    --shadow: 0 1px 2px rgba(44,34,20,.08), 0 12px 32px -12px rgba(44,34,20,.22);
    --flag: #F7EFE2;
  }}
  @media (prefers-color-scheme: dark) {{
    :root:not([data-theme="light"]) {{
      --ground: #0A0A0A;
      --surface: #141312;
      --ink: #F2E6D0;
      --muted: #A2978A;
      --faint: #6F675D;
      --gold: #C9A96E;
      --gold-line: #C9A96E;
      --hair: rgba(242, 230, 208, 0.14);
      --shadow: 0 1px 2px rgba(0,0,0,.5), 0 18px 40px -14px rgba(0,0,0,.7);
      --flag: #1C1813;
    }}
  }}
  :root[data-theme="dark"] {{
    --ground: #0A0A0A;
    --surface: #141312;
    --ink: #F2E6D0;
    --muted: #A2978A;
    --faint: #6F675D;
    --gold: #C9A96E;
    --gold-line: #C9A96E;
    --hair: rgba(242, 230, 208, 0.14);
    --shadow: 0 1px 2px rgba(0,0,0,.5), 0 18px 40px -14px rgba(0,0,0,.7);
    --flag: #1C1813;
  }}

  * {{ box-sizing: border-box; }}
  body {{
    margin: 0;
    background: var(--ground);
    color: var(--ink);
    font-family: "IN", ui-sans-serif, system-ui, sans-serif;
    font-weight: 300;
    line-height: 1.6;
    -webkit-font-smoothing: antialiased;
  }}
  .wrap {{ max-width: 1120px; margin: 0 auto; padding: 0 28px 96px; }}

  .eyebrow {{
    font-family: "Courier New", Courier, monospace;
    font-size: 11px; letter-spacing: .22em; text-transform: uppercase;
    color: var(--gold); margin: 0;
  }}

  header.top {{
    display: flex; flex-direction: column; gap: 34px;
    padding: 72px 0 46px;
  }}
  .lockup {{ width: 132px; height: auto; color: var(--ink); display: block; }}
  h1 {{
    font-family: "CG", Georgia, serif; font-weight: 300;
    font-size: clamp(38px, 6vw, 66px); line-height: 1.05;
    letter-spacing: -0.01em; margin: 0; max-width: 15ch;
    text-wrap: balance;
  }}
  .standfirst {{ max-width: 62ch; color: var(--muted); font-size: 17px; margin: 0; }}

  .spec {{
    display: flex; flex-wrap: wrap; gap: 0;
    border-top: 1px solid var(--hair); border-bottom: 1px solid var(--hair);
  }}
  .spec div {{
    padding: 16px 28px 16px 0; margin-right: 28px;
    border-right: 1px solid var(--hair); flex: 0 0 auto;
  }}
  .spec div:last-child {{ border-right: 0; margin-right: 0; }}
  .spec dt {{
    font-family: "Courier New", Courier, monospace; font-size: 10px;
    letter-spacing: .2em; text-transform: uppercase; color: var(--faint);
  }}
  .spec dd {{ margin: 3px 0 0; font-size: 15px; font-variant-numeric: tabular-nums; }}

  .flag {{
    background: var(--flag); border-left: 3px solid var(--gold-line);
    padding: 22px 26px; margin: 0 0 12px; display: grid; gap: 8px;
  }}
  .flag h2 {{ font-family: "IN", sans-serif; font-weight: 500; font-size: 15px;
    margin: 0; letter-spacing: .01em; }}
  .flag p {{ margin: 0; color: var(--muted); font-size: 15px; max-width: 74ch; }}
  .flag code {{
    font-family: "Courier New", Courier, monospace; font-size: 14px;
    color: var(--ink); background: transparent;
  }}

  section {{ padding-top: 72px; }}
  .sec-head {{ display: grid; gap: 10px; margin-bottom: 34px; max-width: 66ch; }}
  .sec-head h2 {{
    font-family: "CG", Georgia, serif; font-weight: 300; font-size: 34px;
    margin: 0; line-height: 1.15;
  }}
  .sec-head p {{ margin: 0; color: var(--muted); }}

  .grid {{ display: grid; gap: 52px 40px;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); }}
  .card {{ display: grid; gap: 20px; align-content: start; }}
  .frame {{
    background: var(--surface); padding: 14px; box-shadow: var(--shadow);
    border: 1px solid var(--hair);
  }}
  .panel {{ width: 100%; height: auto; display: block; }}
  .notes h3 {{
    font-family: "CG", Georgia, serif; font-weight: 500; font-size: 25px;
    margin: 0 0 8px; letter-spacing: .01em;
  }}
  .lede {{ margin: 0 0 16px; font-size: 15px; color: var(--muted); }}
  .facts {{ margin: 0 0 16px; display: grid; gap: 6px;
    border-top: 1px solid var(--hair); padding-top: 14px; }}
  .facts > div {{ display: grid; grid-template-columns: 96px 1fr; gap: 10px; }}
  .facts dt {{
    font-family: "Courier New", Courier, monospace; font-size: 10px;
    letter-spacing: .16em; text-transform: uppercase; color: var(--faint);
    padding-top: 3px;
  }}
  .facts dd {{ margin: 0; font-size: 14px; }}
  .best {{ margin: 0; font-size: 14px; color: var(--ink); }}
  .best span {{
    display: block; font-family: "Courier New", Courier, monospace;
    font-size: 10px; letter-spacing: .16em; text-transform: uppercase;
    color: var(--gold); margin-bottom: 4px;
  }}

  .qr-pair {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
    gap: 32px; max-width: 720px; }}
  .qr-item {{ display: grid; gap: 14px; }}
  .qr-swatch {{ background: var(--surface); border: 1px solid var(--hair);
    padding: 18px; box-shadow: var(--shadow); }}
  .qr {{ width: 100%; height: auto; display: block; }}
  .qr-item h3 {{ font-family: "IN", sans-serif; font-weight: 500; font-size: 15px;
    margin: 0 0 4px; }}
  .qr-item p {{ margin: 0; font-size: 14px; color: var(--muted); }}

  .rec {{ display: grid; gap: 18px; max-width: 74ch; }}
  .rec p {{ margin: 0; color: var(--muted); font-size: 16px; }}
  .rec strong {{ color: var(--ink); font-weight: 500; }}
  .note {{ max-width: 74ch; margin: 24px 0 0; color: var(--muted); font-size: 16px; }}
  .note code {{ font-family: "Courier New", Courier, monospace; color: var(--ink); }}

  table {{ border-collapse: collapse; width: 100%; font-size: 14px; }}
  .scroll {{ overflow-x: auto; }}
  th, td {{ text-align: left; padding: 11px 16px 11px 0;
    border-bottom: 1px solid var(--hair); }}
  th {{
    font-family: "Courier New", Courier, monospace; font-size: 10px;
    letter-spacing: .16em; text-transform: uppercase; color: var(--faint);
    font-weight: 400; white-space: nowrap;
  }}
  td.num {{ font-variant-numeric: tabular-nums; white-space: nowrap; }}

  .files {{ display: grid; gap: 2px; }}
  .files div {{ display: grid; grid-template-columns: minmax(180px, 240px) 1fr;
    gap: 18px; padding: 12px 0; border-bottom: 1px solid var(--hair);
    font-size: 14px; }}
  .files code {{ font-family: "Courier New", Courier, monospace; color: var(--gold); }}
  .files span {{ color: var(--muted); }}

  footer {{ padding-top: 72px; color: var(--faint); font-size: 13px; }}
  footer a {{ color: var(--muted); }}
  a:focus-visible {{ outline: 2px solid var(--gold-line); outline-offset: 3px; }}

  @media (max-width: 620px) {{
    .wrap {{ padding: 0 20px 64px; }}
    .facts > div {{ grid-template-columns: 84px 1fr; }}
  }}
</style>

<div class="wrap">
  <header class="top">
    {lockup_svg()}
    <div style="display:grid;gap:18px">
      <p class="eyebrow">Site signage · twenty-eight options</p>
      <h1>A sign for the front fence.</h1>
      <p class="standfirst">Twenty-eight print-ready treatments for a 400 × 600 mm panel on
      3 mm ACM, external, mounted at a house under renovation. Every option uses the
      current LK lockup, the approved palette, and type converted to outlines, so
      what you see here is exactly what comes off the press.</p>
    </div>
    <dl class="spec">
      <div><dt>Panel</dt><dd>400 × 600 mm portrait</dd></div>
      <div><dt>Substrate</dt><dd>3 mm ACM</dd></div>
      <div><dt>Supplied</dt><dd>406 × 606 mm, 3 mm bleed</dd></div>
      <div><dt>Artwork</dt><dd>Vector PDF, type outlined</dd></div>
      <div><dt>Raster</dt><dd>300 dpi, 4795 × 7157 px</dd></div>
    </dl>
  </header>

  <div class="flag">
    <h2>Changes from Lyda's feedback, applied to all twenty-eight</h2>
    <p>Licence <code>BLD 359176</code> now replaces the ABN on every panel. The
    Instagram handle and its QR are updated to <code>@lkdesignandbuild</code>
    with no trailing underscore. Phone <code>0401 061 246</code> and
    <code>lkdesignandbuild.com.au</code> were checked against the live site and
    are unchanged.</p>
  </div>
  <div class="flag">
    <h2>The website still links to the old handle</h2>
    <p>lkdesignandbuild.com.au links to <code>instagram.com/lkdesignandbuild_</code>
    in two places, the contact section and the footer. Both are now corrected in
    the site source, uncommitted, ready to review and deploy.</p>
  </div>
  <div class="flag">
    <h2>Scan the printed proof before the full run</h2>
    <p>All fifty-six codes decode correctly from the finished artwork, but the
    new handle has not been confirmed against a live Instagram profile. Scanning
    the proof takes a second and rules out an expensive reprint.</p>
  </div>

  <section>
    <div class="sec-head">
      <p class="eyebrow">Start here</p>
      <h2>Simplest</h2>
      <p>Both reference signs do the same thing, and it is subtraction rather
      than a style. One type block at the top, one at the bottom, and a void
      doing the rest. The Georgie Shepherd panel goes furthest: the name, the
      words INTERIOR STUDIO, and nothing else at all. No phone, no address, no
      code. The Laura Abrams A-frame keeps a hairline row of services and a small
      code, but still gives most of the panel to empty white.</p>
      <p>So these give up the headline and the services line, and keep one or
      two contact routes and nothing more. Square corners, since both references
      are square and both hang rather than sit.</p>
      <p>Each layout comes in two: without a code, which is the truer reading of
      the references, and with one. The code is 60 mm on every version, the same
      size as the rest of the set, so nothing is given up on scanning to keep the
      panel quiet.</p>
      <p>What that costs, plainly: a panel with one contact route and no code is
      a brand statement rather than a lead generator. It is a completely
      legitimate choice, and the Georgie Shepherd sign is proof, but it is a
      different job from the one the earlier rounds were doing. The versions with
      a code are the compromise, and they cost the composition very little.</p>
    </div>
    <div class="grid">{r6}</div>
  </section>

  <section>
    <div class="sec-head">
      <p class="eyebrow">The round before</p>
      <h2>Boutique, four ways</h2>
      <p>Less corporate, more boutique. What reads corporate in the earlier
      panels is specific and removable: everything stacked on a dead-centre axis
      and evenly weighted, a services list separated by middle dots, an ENQUIRIES
      label sitting over a bold sans number, colour fields running edge to edge,
      and five or six pieces of information competing for the same space.</p>
      <p>So these four drop the services list, set the number in Cormorant
      Garamond rather than bold Inter, use asymmetry or a contained panel instead
      of full-width bands, and simply carry less. The headline moves to italic
      lower case, which is the boutique voice and also keeps the no-sentence-case
      rule. No new colours: same champagne, cream, warm charcoal and gold. The
      boutique quality comes from space, asymmetry and type rather than from
      anything added.</p>
      <p>Spine comes in four: light or warm dark ground, headline in italic lower
      case or in roman capitals. The services list moved onto the spine rather
      than being dropped, so the information is still there for anyone standing
      at the fence, without a middle-dot row running across the composition.</p>
      <p>Two things to weigh. The serif number reads at roughly 2.4 to 2.7 m
      against 3.3 m for the softened set, so these are gate-and-doorstep signs
      rather than across-the-street ones. And Cormorant sets numerals as old-style
      figures, where the 4 and the 7 drop below the line, which is a large part of
      why the number looks elegant here and also makes it fractionally slower to
      read at a glance.</p>
      <p>Latest round of changes, applied across the whole set: the QR is up from
      46 to 60 mm, the website, handle and licence number are up roughly a sixth,
      and the spine has gone from 9 to 11 point.</p>
    </div>
    <div class="grid">{r4}</div>
  </section>

  <section>
    <div class="sec-head">
      <p class="eyebrow">The spine question</p>
      <h2>No, the spine will not be read from a car</h2>
      <p>Worth being straight about it. At 11 point the spine has a 6.9 mm cap
      height, which is comfortable at about 0.8 m. It is a detail for someone
      standing at the fence, and rotated type costs a head tilt on top of that.</p>
      <p>But the honest version of the answer is bigger than the spine. Nothing
      on a 400 mm wide panel carries a services list to a passing car. A 10 m read
      needs about 85 mm of cap height, and INTERIOR DESIGN alone at that size runs
      well over a metre wide. Set horizontally in the middle of the panel it would
      be no more readable from a car than it is on the spine, only less elegant.
      A driver at 40 km/h has one or two seconds of usable glance and takes in a
      single element in that time.</p>
      <p>On these panels that element is the mark, at 86 mm cap, readable at
      around 10 m. That is the thing doing the work from the road, and it is
      doing it well. The spine, the number and the QR are all for people who have
      already slowed down or stopped. If services genuinely need to reach traffic,
      that is a second and much larger panel, not a change to this one.</p>
    </div>
  </section>

  <section>
    <div class="sec-head">
      <p class="eyebrow">The round before</p>
      <h2>Softer, four ways, all in capitals</h2>
      <p>Monolith was the right direction but read as too structured. The
      structure in it comes from four things: a rectangular keyline, a flat
      near-black ground, sans-serif capitals tracked wide across every line, and
      lines stacked at even intervals. All four are dialled back here. The frame
      is gone. The ground is a warm
      charcoal that reads brown-black in daylight instead of switched-off-screen
      black. Rules are shorter, lighter and round-capped, the number drops from
      SemiBold to Medium, and the spacing between groups is now larger than the
      spacing within them. The corners are cut at a 20 mm radius, which is a
      router setting rather than artwork, and does more for softness than
      anything on the panel.</p>
      <p>Capitals return in the headline, but as Cormorant Garamond at display
      size rather than tracked sans, which is a different animal: the serif does
      the work and the tracking only opens it up. The rule is applied down the
      whole panel: the services line and the enquiries label follow the same rule.
      Capitals need letter-spacing to breathe and run wide, so the headline breaks
      over two lines at 40 point, which lands on a 25 mm cap height. The web
      address, the licence number and the Instagram handle stay as they are,
      being literal strings rather than styled copy.</p>
      <p>The one cost of the softening: the lighter number weight gives up roughly
      0.3 m of read distance. That is what softer buys.</p>
    </div>
    <div class="grid">{r3}</div>
  </section>

  <section>
    <div class="sec-head">
      <p class="eyebrow">Reference</p>
      <h2>The same panel in lower case</h2>
      <p>Kept for comparison rather than as a live option. Lower case fits the
      headline back onto one line and reads quieter, but it introduces a second
      voice directly beneath the lockup, whose own tagline, DESIGN AND BUILD, is
      set in capitals.</p>
    </div>
    <div class="grid">{r5}</div>
  </section>

  <section>
    <div class="sec-head">
      <p class="eyebrow">Dark or light</p>
      <h2>I would go light, and keep dark for the door</h2>
      <p>Dark is the more premium read on screen, which is why it is where these
      started. Outdoors on a residential street, light wins on four practical
      counts. It holds contrast in direct sun, where a dark panel flares and goes
      flat. It hides the dust and pollen that settle on a site sign within a week,
      which a dark panel shows as a grey film. It stays cooler, so the panel is
      less prone to bowing on a north-facing fence. And it separates from the
      fence itself, since most Adelaide frontages are dark colourbond, hedging or
      brick, and a near-black panel disappears into all three.</p>
      <p>Champagne also happens to be the softer of the two, which is the thing
      being asked for. <strong>Softened Light</strong> is my recommendation.
      Keep <strong>Softened Dark</strong> for a smaller plaque by the door and for
      portfolio photography, where it is unbeatable.</p>
    </div>
  </section>

  <section>
    <div class="sec-head">
      <p class="eyebrow">First pass</p>
      <h2>Five treatments of the lockup</h2>
      <p>Straight applications of the mark and palette, working through the
      obvious axes: dark or light ground, brand-led or contact-led, and how much
      information a passer-by actually needs.</p>
    </div>
    <div class="grid">{r1}</div>
  </section>

  <section>
    <div class="sec-head">
      <p class="eyebrow">Second pass</p>
      <h2>Four more, against the style guide and the signage rules</h2>
      <p>These add what the first pass missed. The style guide names <em>Cormorant
      Garamond</em> as the display face and the first five used Inter throughout,
      so the serif appears here, along with the full six-colour palette and the
      clear-space rule of one monogram height around the mark. The signage research
      contributed the rest: one dominant message per panel, roughly 25 mm of cap
      height per 3 m of viewing distance, light-on-dark or dark-on-light only, and
      enough empty field that the mark lands before the detail does.</p>
    </div>
    <div class="grid">{r2}</div>
  </section>

  <section>
    <div class="sec-head">
      <p class="eyebrow">QR codes</p>
      <h2>Two sets of artwork, one per destination</h2>
      <p>Every layout is generated twice. The website address is already set in
      type on all twenty-eight panels, so the Instagram code is arguably the more useful
      scan: it takes a passer-by straight to photographs of the work. Every panel above shows the Instagram set.</p>
    </div>
    <div class="qr-pair">
      <div class="qr-item">
        <div class="qr-swatch">{qr_detail("insta")}</div>
        <div>
          <h3>Instagram</h3>
          <p>instagram.com/lkdesignandbuild, with the camera mark knocked out
          of the centre. Error correction steps up to H, which recovers 30% of
          the code, so the mark costs it nothing. Caption on the panel reads
          @lkdesignandbuild. Now 60 mm, which puts a module at 1.33 mm and takes
          the comfortable scan distance to around 600 mm.</p>
        </div>
      </div>
      <div class="qr-item">
        <div class="qr-swatch">{qr_detail("web")}</div>
        <div>
          <h3>Website</h3>
          <p>lkdesignandbuild.com.au, plain, error correction Q. Files are the
          <code>-web</code> set. Use these if the sign should send people to the
          portfolio pages rather than the feed.</p>
        </div>
      </div>
    </div>
    <p class="note">All fifty-six codes were decoded from the finished 300 dpi
    artwork to confirm they scan. A useful check on the enlargement: at 46 mm a
    reader could only find the code once the crop was narrowed to the code
    itself, and at 60 mm every one is found in the full panel image. Dropping
    https:// from the encoded address would buy another 10% in module size, but
    some scanners then treat it as plain text rather than a link, so the scheme
    stays. Both are drawn as vector modules and stay sharp at any size.</p>
  </section>

  <section>
    <div class="sec-head">
      <p class="eyebrow">Recommendation</p>
      <h2>Where I'd land</h2>
    </div>
    <div class="rec">
      <p><strong>Kerbside</strong> is the one I'd print. It gives the number the
      largest cap height a 400 mm panel can physically carry, keeps the mark and
      the serif line above it, and holds the highest contrast of the nine. It does
      the job a site sign is for without the sign looking like it is shouting.</p>
      <p><strong>Nightfall</strong> if the brief is really about presence rather
      than enquiries. It is the most restrained and the best to photograph for
      the portfolio. <strong>Editorial</strong> is the distinctive one, and the
      closest to how the brand actually speaks; it trades about 1.5 m of number
      legibility for that.</p>
      <p>They are not exclusive. The same artwork scales cleanly to a larger panel,
      so a common pattern is Kerbside on the street frontage and Nightfall by the
      door.</p>
    </div>
  </section>

  <section>
    <div class="sec-head">
      <p class="eyebrow">Legibility</p>
      <h2>What a 400 mm panel can and cannot do</h2>
      <p>Sign trade rule of thumb: about 25 mm of cap height per 3 m of comfortable
      reading distance.</p>
    </div>
    <div class="scroll">
      <table>
        <thead><tr><th>Element</th><th>Cap height</th><th>Comfortable read</th></tr></thead>
        <tbody>
          <tr><td>LK mark, largest layouts</td><td class="num">85–94 mm</td><td class="num">10–11 m</td></tr>
          <tr><td>LK mark, Kerbside</td><td class="num">57 mm</td><td class="num">7 m</td></tr>
          <tr><td>Phone, Kerbside</td><td class="num">36 mm</td><td class="num">4.4 m</td></tr>
          <tr><td>Phone, typical</td><td class="num">24–33 mm</td><td class="num">3–4 m</td></tr>
          <tr><td>Serif headline</td><td class="num">22–33 mm</td><td class="num">2.7–4 m</td></tr>
        </tbody>
      </table>
    </div>
    <p class="note">At 400 mm wide the number cannot be made to read from a passing
    car. A 10 m read needs about 85 mm of cap height, which would set
    <code>0401 061 246</code> around 770 mm wide. This is a footpath and driveway
    sign: the mark reads from across the street, the number reads from the fence.
    A second, larger panel is the answer if car traffic matters.</p>
  </section>

  <section>
    <div class="sec-head">
      <p class="eyebrow">Production</p>
      <h2>Files and fixing</h2>
    </div>
    <div class="files">
      <div><code>print-pdf/</code><span>Send this to the printer. 406 × 606 mm, vector, type outlined.</span></div>
      <div><code>print-svg/</code><span>Same artwork, editable.</span></div>
      <div><code>print-png/</code><span>300 dpi fallback, 4795 × 7157 px.</span></div>
      <div><code>preview/</code><span>Trim-only SVG and 900 px PNG for review and email.</span></div>
      <div><code>guides/</code><span>Trim, safe area and hole positions. Reference only, never send to print.</span></div>
      <div><code>PRODUCTION-SPEC.md</code><span>Full spec: colour build, print method, fixing, pre-press checklist.</span></div>
    </div>
    <p class="note">Each option appears twice in every folder, as
    <code>-insta</code> and <code>-web</code>. Fifty-six files per format.</p>
    <div class="rec" style="margin-top:34px">
      <p>Fixing: four Ø6 mm holes, centres 30 mm in from each corner, plus two
      optional at mid-height for a temporary mesh fence. Those positions were
      checked against all twenty-eight layouts: they land in flat colour and clear
      every piece of type. On the softened set the corners are routed at a 20 mm
      radius, which only cuts the corner squares, so the 30 mm hole centres stay
      well clear of the curve. Black nylon cable ties or stainless with black cup washers.
      3 mm ACM at this size needs no frame.</p>
      <p>Ask for a matt or satin anti-glare finish and a rich black build on the
      dark grounds. The gold is a warm tan, not a metallic. Closest reference is
      Pantone 465 C, and it is worth a proof strip.</p>
    </div>
  </section>

  <footer>
    <p>Artwork generated from <code>generate_site_sign.py</code>. Legibility and
    site-board guidance from
    <a href="https://www.signs.com/blog/signage-101-letter-height-visibility/">Signs.com</a>,
    <a href="https://www.signknights.com/sign-visibility-and-viewing-distance-guidelines/">Sign Knights</a>,
    <a href="https://www.stouse.com/4-critical-factors-for-signage-letter-size-and-visibility/">Stouse</a> and
    <a href="https://www.boardprintingcompany.co.uk/architect-signboards/">Board Printing Company</a>.</p>
  </footer>
</div>
"""
    with open(OUT, "w") as fh:
        fh.write(html)
    print(f"wrote {OUT}  ({os.path.getsize(OUT)/1024:.0f} KB)")


if __name__ == "__main__":
    build()
