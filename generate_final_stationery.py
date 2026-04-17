#!/usr/bin/env python3
"""Generate letterhead/quote DOCX, email signatures, and drawing PDFs for
each colour variant of the approved LK — Courier Slab logo.

Output lands in /assets/branding/final/:
    png/           — rasterized logo PNGs for DOCX embedding
    stationery/{variant}/letterhead.docx
    stationery/{variant}/quote.docx
    stationery/{variant}/email-signature.html
    drawings/drawing-{variant}.pdf

Variants: charcoal (standard), champagne (dark premium), mono (pure B&W),
two-tone (champagne + charcoal on warm mid-tone).
"""

import os
import cairosvg
from docx import Document
from docx.shared import Inches, Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import nsdecls
from docx.oxml import parse_xml
import fitz  # PyMuPDF

ROOT = "/Users/dunderdoon/Projects_Local/primedesign"
FINAL = f"{ROOT}/assets/branding/final"
SVG_DIR = FINAL
PNG_DIR = f"{FINAL}/png"
STAT_DIR = f"{FINAL}/stationery"
DRAW_DIR = f"{FINAL}/drawings"
SOURCE_DRAW_PDF = f"{ROOT}/assets/branding/documents/drawing-options-prime-original.pdf"

GOLD = RGBColor(0xC9, 0xA9, 0x6E)
CHARCOAL = RGBColor(0x2C, 0x2C, 0x2C)
CHAMPAGNE = RGBColor(0xF2, 0xE6, 0xD0)
SLATE = RGBColor(0x66, 0x66, 0x66)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
NEAR_BLACK = RGBColor(0x0A, 0x0A, 0x0A)

CONTACT = {
    "name": "Lyda",
    "phone": "0481 742 026",
    "email": "hello@lkdesignandbuild.com.au",
    "website": "www.lkdesignandbuild.com.au",
    "address": "Adelaide, South Australia",
    "abn": "XX XXX XXX XXX",
}

TAGLINE = "Considered design. Precision build."

# One entry per colour variant.
VARIANTS = [
    {
        "key": "charcoal",
        "label": "Charcoal — Standard",
        "desc": "Charcoal LK on white. Standard business correspondence.",
        "logo_svg": "lk-logo-charcoal.svg",            # transparent
        "page_bg_hex": "FFFFFF",
        "page_bg_rgb": WHITE,
        "ink": CHARCOAL,
        "accent": GOLD,
        "body": CHARCOAL,
        "subtle": SLATE,
        "rule_hex": "C9A96E",
        "footer_is_dark": False,
        "email_bg": "#FFFFFF",
        "email_ink": "#2C2C2C",
        "email_accent": "#C9A96E",
    },
    {
        "key": "champagne",
        "label": "Champagne — Dark Premium",
        "desc": "Champagne LK on near-black. For proposal covers or dark-theme letterhead.",
        "logo_svg": "lk-logo-champagne.svg",
        "page_bg_hex": "0A0A0A",
        "page_bg_rgb": NEAR_BLACK,
        "ink": CHAMPAGNE,
        "accent": GOLD,
        "body": CHAMPAGNE,
        "subtle": RGBColor(0xB0, 0xA8, 0x9A),
        "rule_hex": "C9A96E",
        "footer_is_dark": True,
        "email_bg": "#0A0A0A",
        "email_ink": "#F2E6D0",
        "email_accent": "#C9A96E",
    },
    {
        "key": "mono",
        "label": "Mono — Black & White",
        "desc": "Pure black on white. Copier/fax safe, monochrome print.",
        "logo_svg": "lk-logo-mono-light.svg",          # has white BG rect
        "page_bg_hex": "FFFFFF",
        "page_bg_rgb": WHITE,
        "ink": RGBColor(0x00, 0x00, 0x00),
        "accent": RGBColor(0x00, 0x00, 0x00),
        "body": RGBColor(0x00, 0x00, 0x00),
        "subtle": RGBColor(0x44, 0x44, 0x44),
        "rule_hex": "000000",
        "footer_is_dark": False,
        "email_bg": "#FFFFFF",
        "email_ink": "#000000",
        "email_accent": "#000000",
    },
    {
        "key": "two-tone",
        "label": "Two-Tone — Warm Neutral",
        "desc": "Champagne LK + charcoal tagline on warm mid-tone. Branded marketing & stationery.",
        "logo_svg": "lk-logo-two-tone.svg",
        "page_bg_hex": "F5F0EB",                       # warm cream
        "page_bg_rgb": RGBColor(0xF5, 0xF0, 0xEB),
        "ink": CHARCOAL,
        "accent": GOLD,
        "body": CHARCOAL,
        "subtle": SLATE,
        "rule_hex": "C9A96E",
        "footer_is_dark": False,
        "email_bg": "#F5F0EB",
        "email_ink": "#2C2C2C",
        "email_accent": "#C9A96E",
    },
]


def rasterize_logos():
    """Convert each variant's SVG logo to high-DPI PNG for DOCX embedding."""
    os.makedirs(PNG_DIR, exist_ok=True)
    for v in VARIANTS:
        svg_path = f"{SVG_DIR}/{v['logo_svg']}"
        # Use horizontal variant for DOCX header (wider aspect suits letterhead)
        horiz_svg = svg_path.replace("lk-logo-", "lk-logo-horizontal-")
        # Two-tone and mono may not have distinct horizontal files — fall back to primary.
        if not os.path.exists(horiz_svg):
            horiz_svg = svg_path
        out = f"{PNG_DIR}/{v['key']}.png"
        cairosvg.svg2png(url=horiz_svg, write_to=out, output_width=1800)
        print(f"  rasterized {os.path.basename(horiz_svg)} → {out}")
        v["logo_png"] = out


def set_page_shading(doc, hex_color):
    """Apply a page background colour to an entire section."""
    if hex_color.upper() == "FFFFFF":
        return
    sect = doc.sections[0]
    sectPr = sect._sectPr
    # background fill via <w:background>
    bg = parse_xml(f'<w:background {nsdecls("w")} w:color="{hex_color}"/>')
    doc.element.insert(0, bg)
    # also tell Word to display the bg
    settings = doc.settings.element
    dispBg = parse_xml(f'<w:displayBackgroundShape {nsdecls("w")}/>')
    settings.append(dispBg)


def style_run(run, font_name, size, color, bold=False, italic=False):
    run.font.name = font_name
    run.font.size = Pt(size)
    run.font.color.rgb = color
    run.bold = bold
    run.italic = italic


def rule(doc, hex_color):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(2)
    pPr = p._p.get_or_add_pPr()
    pBdr = parse_xml(
        f'<w:pBdr {nsdecls("w")}><w:bottom w:val="single" w:sz="4" w:space="1" w:color="{hex_color}"/></w:pBdr>'
    )
    pPr.append(pBdr)


def add_logo_header(doc, v):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p.paragraph_format.space_after = Pt(4)
    run = p.add_run()
    run.add_picture(v["logo_png"], height=Cm(1.6))
    rule(doc, v["rule_hex"])
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after = Pt(2)
    contact = f'{CONTACT["phone"]}  |  {CONTACT["email"]}  |  {CONTACT["website"]}  |  {CONTACT["address"]}'
    run = p.add_run(contact)
    style_run(run, "Calibri", 8, v["subtle"])
    doc.add_paragraph().paragraph_format.space_after = Pt(6)


def add_footer(doc, v):
    rule(doc, v["rule_hex"])
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(6)
    run = p.add_run(f'LK Design and Build  |  ABN {CONTACT["abn"]}  |  {TAGLINE}')
    style_run(run, "Calibri", 7.5, v["subtle"], italic=True)


def build_letterhead(v):
    doc = Document()
    s = doc.sections[0]
    s.top_margin = Cm(2); s.bottom_margin = Cm(2); s.left_margin = Cm(2.5); s.right_margin = Cm(2.5)
    set_page_shading(doc, v["page_bg_hex"])
    add_logo_header(doc, v)

    p = doc.add_paragraph(); p.paragraph_format.space_after = Pt(12)
    style_run(p.add_run("[Date]"), "Calibri", 10, v["body"])
    for line in ["[Recipient Name]", "[Company / Address Line 1]", "[Address Line 2]", "[City, State, Postcode]"]:
        p = doc.add_paragraph(); p.paragraph_format.space_after = Pt(2)
        style_run(p.add_run(line), "Calibri", 10, v["body"])
    doc.add_paragraph()
    p = doc.add_paragraph(); p.paragraph_format.space_after = Pt(8)
    style_run(p.add_run("Re: [Subject Line]"), "Calibri", 10, v["body"], bold=True)
    p = doc.add_paragraph(); p.paragraph_format.space_after = Pt(8)
    style_run(p.add_run("Dear [Name],"), "Calibri", 10, v["body"])

    body_text = (
        "Thank you for your interest in LK Design and Build. We specialise in premium home renovations, "
        "additions, and new builds across Adelaide, delivering exceptional craftsmanship and thoughtful "
        "design at every stage.\n\n"
        "[Continue your letter here. This template provides the branded letterhead with the approved LK "
        "— Courier Slab logo. Simply replace the placeholder text with your content.]\n\n"
        "We look forward to discussing your project in detail."
    )
    for para in body_text.split("\n\n"):
        p = doc.add_paragraph(); p.paragraph_format.space_after = Pt(8); p.paragraph_format.line_spacing = Pt(14)
        style_run(p.add_run(para), "Calibri", 10, v["body"])

    doc.add_paragraph()
    p = doc.add_paragraph(); style_run(p.add_run("Kind regards,"), "Calibri", 10, v["body"])
    doc.add_paragraph(); doc.add_paragraph()
    p = doc.add_paragraph(); style_run(p.add_run("Lyda"), "Calibri", 10, v["body"], bold=True)
    p = doc.add_paragraph(); p.paragraph_format.space_after = Pt(2)
    style_run(p.add_run("LK Design and Build"), "Calibri", 9, v["accent"])

    add_footer(doc, v)
    out = f"{STAT_DIR}/{v['key']}/letterhead.docx"
    doc.save(out)
    print(f"  letterhead: {out}")


def set_cell_shading(cell, hex_color):
    shading = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{hex_color}" w:val="clear"/>')
    cell._tc.get_or_add_tcPr().append(shading)


def build_quote(v):
    doc = Document()
    s = doc.sections[0]
    s.top_margin = Cm(2); s.bottom_margin = Cm(2); s.left_margin = Cm(2.5); s.right_margin = Cm(2.5)
    set_page_shading(doc, v["page_bg_hex"])
    add_logo_header(doc, v)

    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.space_after = Pt(4)
    style_run(p.add_run("QUOTATION"), "Calibri", 20, v["accent"], bold=True)
    rule(doc, v["rule_hex"])

    details = [
        ("Quote Number:", "[QTE-0001]"),
        ("Date:", "[Date]"),
        ("Valid Until:", "[Date + 30 days]"),
        ("Project Address:", "[Site Address]"),
    ]
    t = doc.add_table(rows=len(details), cols=2); t.alignment = WD_TABLE_ALIGNMENT.LEFT
    for i, (lbl, val) in enumerate(details):
        c1, c2 = t.cell(i, 0), t.cell(i, 1)
        p = c1.paragraphs[0]; style_run(p.add_run(lbl), "Calibri", 9, v["subtle"], bold=True); p.paragraph_format.space_after = Pt(3)
        p = c2.paragraphs[0]; style_run(p.add_run(val), "Calibri", 9, v["body"]); p.paragraph_format.space_after = Pt(3)
        c1.width = Cm(4); c2.width = Cm(12)
    _no_borders(t)

    doc.add_paragraph()
    p = doc.add_paragraph(); p.paragraph_format.space_after = Pt(2)
    style_run(p.add_run("PREPARED FOR"), "Calibri", 9, v["accent"])
    for line in ["[Client Name]", "[Client Address]", "[Client Email]", "[Client Phone]"]:
        p = doc.add_paragraph(); p.paragraph_format.space_after = Pt(1)
        style_run(p.add_run(line), "Calibri", 9, v["body"])

    doc.add_paragraph()
    p = doc.add_paragraph(); p.paragraph_format.space_after = Pt(6)
    style_run(p.add_run("SCOPE OF WORKS"), "Calibri", 9, v["accent"])
    p = doc.add_paragraph(); p.paragraph_format.space_after = Pt(8)
    style_run(p.add_run("[Describe proposed works, demolition, structural, finishes, fixtures, allowances.]"),
              "Calibri", 9, v["subtle"], italic=True)

    items_table = doc.add_table(rows=1, cols=3); items_table.alignment = WD_TABLE_ALIGNMENT.LEFT
    headers = ["Description", "Qty", "Amount (ex GST)"]
    widths = [Cm(10), Cm(2), Cm(4.5)]
    header_bg = "2C2C2C" if not v["footer_is_dark"] else "F2E6D0"
    header_fg = WHITE if not v["footer_is_dark"] else NEAR_BLACK
    for i, (h, w) in enumerate(zip(headers, widths)):
        c = items_table.cell(0, i); c.width = w
        p = c.paragraphs[0]; style_run(p.add_run(h), "Calibri", 8.5, header_fg, bold=True)
        set_cell_shading(c, header_bg)
        p.paragraph_format.space_before = Pt(4); p.paragraph_format.space_after = Pt(4)

    samples = [
        ("[Demolition & Site Preparation]", "1", "$X,XXX.XX"),
        ("[Structural Works]", "1", "$X,XXX.XX"),
        ("[Carpentry & Framing]", "1", "$X,XXX.XX"),
        ("[Electrical]", "1", "$X,XXX.XX"),
        ("[Plumbing]", "1", "$X,XXX.XX"),
        ("[Tiling & Waterproofing]", "1", "$X,XXX.XX"),
        ("[Joinery & Cabinetry]", "1", "$X,XXX.XX"),
        ("[Painting & Finishes]", "1", "$X,XXX.XX"),
        ("[Fixtures & Fittings — Allowance]", "1", "$X,XXX.XX"),
        ("[Project Management & Supervision]", "1", "$X,XXX.XX"),
    ]
    for desc, qty, amt in samples:
        row = items_table.add_row()
        for i, val in enumerate([desc, qty, amt]):
            c = row.cells[i]; c.width = widths[i]
            p = c.paragraphs[0]; style_run(p.add_run(val), "Calibri", 9, v["body"])
            p.paragraph_format.space_before = Pt(3); p.paragraph_format.space_after = Pt(3)
            if i == 2:
                p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    _items_borders(items_table, v["rule_hex"])

    doc.add_paragraph()
    totals = [("Subtotal (ex GST):", "$XX,XXX.XX"),
              ("GST (10%):", "$X,XXX.XX"),
              ("TOTAL (inc GST):", "$XX,XXX.XX")]
    for lbl, val in totals:
        p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.RIGHT; p.paragraph_format.space_after = Pt(2)
        is_total = "TOTAL" in lbl and "Sub" not in lbl
        style_run(p.add_run(lbl + "  "), "Calibri", 10 if is_total else 9, v["body"], bold=is_total)
        style_run(p.add_run(val), "Calibri", 10 if is_total else 9, v["accent"] if is_total else v["body"], bold=is_total)

    rule(doc, v["rule_hex"]); doc.add_paragraph()
    p = doc.add_paragraph(); p.paragraph_format.space_after = Pt(6)
    style_run(p.add_run("TERMS & CONDITIONS"), "Calibri", 9, v["accent"])
    terms = [
        "This quotation is valid for 30 days from the date of issue.",
        "A 10% deposit is required upon acceptance to secure scheduling.",
        "Progress payments are due at agreed milestones as outlined in the building contract.",
        "All works are carried out in accordance with the Building Code of Australia and relevant South Australian regulations.",
        "Any variations to the scope of works will be documented and agreed in writing before commencement.",
        "LK Design and Build holds comprehensive public liability and construction insurance.",
        "Defects liability period: 12 months from practical completion.",
    ]
    for i, term in enumerate(terms, 1):
        p = doc.add_paragraph(); p.paragraph_format.space_after = Pt(2); p.paragraph_format.left_indent = Cm(0.5)
        style_run(p.add_run(f"{i}. {term}"), "Calibri", 8, v["subtle"])

    doc.add_paragraph()
    p = doc.add_paragraph(); p.paragraph_format.space_after = Pt(6)
    style_run(p.add_run("ACCEPTANCE"), "Calibri", 9, v["accent"])
    p = doc.add_paragraph(); p.paragraph_format.space_after = Pt(4)
    style_run(p.add_run("I/We accept this quotation and the terms and conditions outlined above."), "Calibri", 9, v["body"])

    doc.add_paragraph()
    sig = doc.add_table(rows=2, cols=2); sig.alignment = WD_TABLE_ALIGNMENT.LEFT
    labels = [("Client Signature:", "Date:"), ("Print Name:", "")]
    for r, (l1, l2) in enumerate(labels):
        for c, lbl in enumerate([l1, l2]):
            if not lbl: continue
            cell = sig.cell(r, c)
            p = cell.paragraphs[0]
            style_run(p.add_run(lbl + "  ___________________________"), "Calibri", 9, v["body"])
            p.paragraph_format.space_before = Pt(12)
    _no_borders(sig)

    add_footer(doc, v)
    out = f"{STAT_DIR}/{v['key']}/quote.docx"
    doc.save(out)
    print(f"  quote:      {out}")


def _no_borders(table):
    tbl = table._tbl
    tblPr = tbl.tblPr if tbl.tblPr is not None else parse_xml(f'<w:tblPr {nsdecls("w")}/>')
    borders = parse_xml(
        f'<w:tblBorders {nsdecls("w")}>'
        f'<w:top w:val="none" w:sz="0" w:space="0" w:color="auto"/>'
        f'<w:left w:val="none" w:sz="0" w:space="0" w:color="auto"/>'
        f'<w:bottom w:val="none" w:sz="0" w:space="0" w:color="auto"/>'
        f'<w:right w:val="none" w:sz="0" w:space="0" w:color="auto"/>'
        f'<w:insideH w:val="none" w:sz="0" w:space="0" w:color="auto"/>'
        f'<w:insideV w:val="none" w:sz="0" w:space="0" w:color="auto"/>'
        f'</w:tblBorders>'
    )
    tblPr.append(borders)


def _items_borders(table, hex_color):
    tbl = table._tbl
    tblPr = tbl.tblPr if tbl.tblPr is not None else parse_xml(f'<w:tblPr {nsdecls("w")}/>')
    borders = parse_xml(
        f'<w:tblBorders {nsdecls("w")}>'
        f'<w:top w:val="single" w:sz="4" w:space="0" w:color="{hex_color}"/>'
        f'<w:bottom w:val="single" w:sz="4" w:space="0" w:color="{hex_color}"/>'
        f'<w:insideH w:val="single" w:sz="2" w:space="0" w:color="E8E8E8"/>'
        f'</w:tblBorders>'
    )
    tblPr.append(borders)


EMAIL_TEMPLATE = """<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Email Signature — LK Design and Build — {label}</title></head>
<body style="margin:0;padding:20px;background:#f5f5f5;font-family:Arial,sans-serif;">
<div style="max-width:560px;margin:0 auto;background:#fff;padding:30px;border-radius:8px;">
<p style="font-size:12px;color:#888;margin-bottom:16px;">Copy the signature below into your email client settings (Gmail: Settings → Signature, Outlook: File → Options → Mail → Signatures).</p>
<hr style="border:1px dashed #ccc;margin-bottom:20px;">

<!-- ====== EMAIL SIGNATURE START ====== -->
<table cellpadding="0" cellspacing="0" border="0" style="font-family:Calibri,Arial,sans-serif;color:{ink};background:{bg};padding:14px 18px;border-radius:6px;">
<tr>
  <td style="vertical-align:top;padding-right:18px;border-right:1px solid {accent};">
    <img src="https://dunderdoon.com/assets/branding/final/png/{key}.png" alt="LK Design and Build" style="width:150px;height:auto;display:block;">
  </td>
  <td style="vertical-align:top;padding-left:18px;">
    <div style="font-size:15px;font-weight:bold;color:{ink};margin-bottom:1px;">Lyda</div>
    <div style="font-size:10px;color:{accent};font-weight:600;letter-spacing:1.4px;margin-bottom:10px;">DIRECTOR</div>
    <div style="font-size:11px;color:{ink};line-height:1.7;opacity:0.85;">
      <span>M:</span> {phone}<br>
      <span>E:</span> <a href="mailto:{email}" style="color:{accent};text-decoration:none;">{email}</a><br>
      <span>W:</span> <a href="https://{website}" style="color:{accent};text-decoration:none;">{website}</a><br>
      <span>A:</span> {address}
    </div>
    <div style="margin-top:8px;padding-top:8px;border-top:1px solid {accent};font-size:9px;color:{ink};opacity:0.6;font-style:italic;">
      {tagline}
    </div>
  </td>
</tr>
</table>
<!-- ====== EMAIL SIGNATURE END ====== -->

<hr style="border:1px dashed #ccc;margin-top:20px;">
<p style="font-size:11px;color:#999;margin-top:10px;">Variant: <strong>{label}</strong></p>
</div>
</body></html>
"""


def build_email_signature(v):
    html = EMAIL_TEMPLATE.format(
        label=v["label"], key=v["key"],
        bg=v["email_bg"], ink=v["email_ink"], accent=v["email_accent"],
        phone=CONTACT["phone"], email=CONTACT["email"], website=CONTACT["website"],
        address=CONTACT["address"], tagline=TAGLINE,
    )
    out = f"{STAT_DIR}/{v['key']}/email-signature.html"
    with open(out, "w") as f:
        f.write(html)
    print(f"  email:      {out}")


def build_drawing(v):
    """Overlay the LK logo in place of the Prime title-block logo."""
    if not os.path.exists(SOURCE_DRAW_PDF):
        print(f"  drawing skipped: source PDF missing at {SOURCE_DRAW_PDF}")
        return
    doc = fitz.open(SOURCE_DRAW_PDF)
    page = doc[0]
    # Locate the Prime logo image — heuristic: largest raster in the title block (bottom-right).
    images = page.get_images(full=True)
    if not images:
        print("  drawing skipped: no images on page 1")
        doc.close(); return
    # Pick the image whose bbox is in the bottom-right quadrant of the page.
    page_rect = page.rect
    target_xref = None
    target_rect = None
    for img in images:
        xref = img[0]
        for rect in page.get_image_rects(xref):
            if rect.x1 > page_rect.width * 0.55 and rect.y0 > page_rect.height * 0.55:
                if target_rect is None or (rect.width * rect.height) > (target_rect.width * target_rect.height):
                    target_xref = xref; target_rect = rect
    if target_rect is None:
        # Fallback: pick the largest overall
        for img in images:
            xref = img[0]
            for rect in page.get_image_rects(xref):
                if target_rect is None or (rect.width * rect.height) > (target_rect.width * target_rect.height):
                    target_xref = xref; target_rect = rect
    # Hide original with a solid rect matching page bg, then draw new logo on top.
    bg_rgb = tuple(c / 255 for c in v["page_bg_rgb"])
    page.draw_rect(target_rect, color=bg_rgb, fill=bg_rgb, width=0)
    # Insert new logo centred in the same rect, preserving aspect.
    page.insert_image(target_rect, filename=v["logo_png"], keep_proportion=True)
    out = f"{DRAW_DIR}/drawing-{v['key']}.pdf"
    doc.save(out)
    doc.close()
    print(f"  drawing:    {out}")


def main():
    rasterize_logos()
    for v in VARIANTS:
        os.makedirs(f"{STAT_DIR}/{v['key']}", exist_ok=True)
        print(f"\n=== {v['label']} ===")
        build_letterhead(v)
        build_quote(v)
        build_email_signature(v)
        build_drawing(v)
    print(f"\nDone. Generated stationery for {len(VARIANTS)} colour variants.")


if __name__ == "__main__":
    main()
