#!/usr/bin/env python3
"""build_authorization_pdf.py -- Cover Re branded authorization-terms PDF.

coverre.com scheme: near-black header band with tan (#C49A6C) accent rule and
lowercase 'cover re' wordmark, Times serif for the 'Authorization Terms' title
and section labels (Cormorant stand-in), light printable body with warm zebra
rows. Terms only -- no signature blocks.
"""
import datetime as _dt
import json
import sys

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

BLACK = colors.HexColor("#000000")
NEARBLACK = colors.HexColor("#0E0E0F")
ACCENT = colors.HexColor("#C49A6C")   # tan
INK = colors.HexColor("#1A1A1A")
MUTE = colors.HexColor("#6B6862")
LINE = colors.HexColor("#E4E1D9")
ZEBRA = colors.HexColor("#FAF7F2")    # warm zebra
LABEL_INK = colors.HexColor("#0E0E0F")
ON_DARK = colors.HexColor("#FFFFFF")
ON_DARK_MUTE = colors.HexColor("#9A968D")

DEFAULT_REINSURER = (
    "COVER REINSURANCE SPC, LTD. acting on behalf of and for "
    "COVER REINSURANCE SEGREGATED PORTFOLIO #1"
)


def basis_label(basis):
    b = (basis or "").strip().upper()
    if b == "RAD":
        return "Risk Attaching During (RAD)"
    if b == "LOD":
        return "Losses Occurring During (LOD)"
    return basis or ""


def pretty_date(d):
    if isinstance(d, str):
        try:
            d = _dt.date.fromisoformat(d.strip())
        except ValueError:
            return d
    return f"{d.strftime('%B')} {d.day}, {d.year}"


def resolve_expiration(val):
    if not val or str(val).strip().lower() == "auto":
        return pretty_date(_dt.date.today() + _dt.timedelta(days=8))
    return pretty_date(val)


def term_value(term):
    if not term:
        return ""
    basis = basis_label(term.get("basis"))
    eff, exp = term.get("effective"), term.get("expiry")
    if eff or exp:
        rng = f"{pretty_date(eff) if eff else '?'} to {pretty_date(exp) if exp else '?'}"
        return f"{basis}<br/>{rng}" if basis else rng
    return basis


def sliding_scale_value(ss):
    if isinstance(ss, list):
        return "<br/>".join(
            f"{r.get('loss_ratio','')} &rarr; {r.get('commission','')}" for r in ss
        )
    return ss or ""


def build(spec, out_path):
    meta = spec.get("meta", {})
    terms = spec.get("terms", {})
    reinsurer = meta.get("reinsurer", DEFAULT_REINSURER)
    date_str = meta.get("date") or pretty_date(_dt.date.today())

    # Opening recommendation line and sign-off (overridable via meta).
    intro_text = meta.get("intro") or (
        "Cover Re recommends that Cover Reinsurance SPC, Ltd., acting on behalf of "
        "and for Cover Reinsurance Segregated Portfolio #1, authorize the terms set "
        "out in this document."
    )
    sig = meta.get("signatory") or {}
    sig_name = sig.get("name", "Blanca Qin")
    sig_title = sig.get("title", "Head of Underwriting")
    sig_org = sig.get("org", "Cover Re SPC")

    styles = getSampleStyleSheet()
    label_st = ParagraphStyle("label", parent=styles["Normal"], fontName="Helvetica-Bold",
                              fontSize=9, textColor=LABEL_INK, leading=12, alignment=TA_LEFT)
    value_st = ParagraphStyle("value", parent=styles["Normal"], fontName="Helvetica",
                              fontSize=9.5, textColor=INK, leading=13, alignment=TA_LEFT)
    sect_st = ParagraphStyle("sect", parent=styles["Normal"], fontName="Times-Roman",
                             fontSize=13, textColor=ACCENT, leading=16, alignment=TA_LEFT)
    intro_st = ParagraphStyle("intro", parent=styles["Normal"], fontName="Helvetica",
                              fontSize=10.5, textColor=INK, leading=15, alignment=TA_LEFT)
    signed_st = ParagraphStyle("signed", parent=styles["Normal"], fontName="Helvetica",
                               fontSize=10, textColor=INK, leading=14, alignment=TA_LEFT)
    signame_st = ParagraphStyle("signame", parent=styles["Normal"], fontName="Helvetica",
                                fontSize=10.5, textColor=INK, leading=14, alignment=TA_LEFT)
    sigorg_st = ParagraphStyle("sigorg", parent=styles["Normal"], fontName="Helvetica",
                               fontSize=9.5, textColor=MUTE, leading=13, alignment=TA_LEFT)

    def g(*pairs):
        return [(lbl, val) for (lbl, val) in pairs if val]

    sections = []
    parties = g(("Cedent", terms.get("cedent")), ("MGA", terms.get("mga")),
                ("Reinsurance Broker", terms.get("reinsurance_broker")))
    if parties:
        sections.append(("Parties", parties))
    structure = g(("Term", term_value(terms.get("term"))),
                  ("Subject Business", terms.get("subject_business")),
                  ("Subject Premium", terms.get("subject_premium")),
                  ("Share", terms.get("share")), ("Premium Caps", terms.get("premium_caps")))
    if structure:
        sections.append(("Structure & Term", structure))
    economics = g(("Ceding Commission", terms.get("ceding_commission")),
                  ("Sliding Scale", sliding_scale_value(terms.get("sliding_scale"))),
                  ("Loss Corridor", terms.get("loss_corridor")),
                  ("Profit Commission", terms.get("profit_commission")))
    if economics:
        sections.append(("Economics", economics))
    caps = g(("Aggregate CAT Cap", terms.get("aggregate_cat_cap")),
             ("ECO / XPL Cap", terms.get("eco_xpl_cap")),
             ("Aggregate Loss-Ratio Cap", terms.get("aggregate_loss_ratio_cap")))
    if caps:
        sections.append(("Caps & Limits", caps))
    collat = g(("Collateral Factors", terms.get("collateral_factors")
                or "110% of unpaid loss + 100% of unearned ceded premium net of receivables"),
               ("Remittance", terms.get("remittance")
                or "90% to trust account / 10% to operating account"))
    sections.append(("Collateral & Remittance", collat))
    reporting = g(("Reporting Requirements", terms.get("reporting_requirements")))
    if reporting:
        sections.append(("Reporting", reporting))
    sections.append(("Authorization", [("Authorization Expiration",
                     resolve_expiration(terms.get("authorization_expiration")))]))

    def header_footer(canvas, doc):
        canvas.saveState()
        w, h = LETTER
        band_h = 1.15 * inch
        canvas.setFillColor(BLACK)
        canvas.rect(0, h - band_h, w, band_h, fill=1, stroke=0)
        # tan accent rule along the bottom of the band
        canvas.setFillColor(ACCENT)
        canvas.rect(0, h - band_h, w, 2.2, fill=1, stroke=0)
        # wordmark: 'cover re' (light + bold)
        x = 0.75 * inch
        yw = h - 0.4 * inch
        canvas.setFillColor(ON_DARK)
        canvas.setFont("Helvetica", 15)
        canvas.drawString(x, yw, "cover ")
        wlen = canvas.stringWidth("cover ", "Helvetica", 15)
        canvas.setFont("Helvetica-Bold", 15)
        canvas.drawString(x + wlen, yw, "re")
        # title (serif)
        canvas.setFillColor(ON_DARK)
        canvas.setFont("Times-Roman", 20)
        canvas.drawString(x, h - 0.82 * inch, "Authorization Terms")
        # ref / date
        canvas.setFillColor(ON_DARK_MUTE)
        canvas.setFont("Helvetica", 8.5)
        canvas.drawRightString(w - 0.75 * inch, h - 0.82 * inch, date_str)
        canvas.setFont("Helvetica", 7)
        canvas.drawRightString(w - 0.75 * inch, h - 0.45 * inch, reinsurer.upper())
        # footer
        canvas.setStrokeColor(LINE)
        canvas.setLineWidth(0.5)
        canvas.line(0.75 * inch, 0.7 * inch, w - 0.75 * inch, 0.7 * inch)
        canvas.setFillColor(MUTE)
        canvas.setFont("Helvetica", 7)
        canvas.drawString(0.75 * inch, 0.5 * inch,
                          "Confidential authorization terms prepared for committee evaluation.")
        canvas.drawRightString(w - 0.75 * inch, 0.5 * inch, f"Page {doc.page}")
        canvas.restoreState()

    doc = SimpleDocTemplate(out_path, pagesize=LETTER, leftMargin=0.75 * inch,
                            rightMargin=0.75 * inch, topMargin=1.45 * inch,
                            bottomMargin=0.9 * inch, title="Authorization Terms", author=reinsurer)
    flow = [Spacer(1, 4), Paragraph(intro_text, intro_st), Spacer(1, 16)]
    avail_w = LETTER[0] - 1.5 * inch
    lab_w = 2.1 * inch
    val_w = avail_w - lab_w
    for title, pairs in sections:
        hdr = Table([[Paragraph(title.upper(), sect_st)]], colWidths=[avail_w])
        hdr.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), NEARBLACK),
                                 ("LINEBEFORE", (0, 0), (0, -1), 2.5, ACCENT),
                                 ("LEFTPADDING", (0, 0), (-1, -1), 10),
                                 ("TOPPADDING", (0, 0), (-1, -1), 6),
                                 ("BOTTOMPADDING", (0, 0), (-1, -1), 6)]))
        flow.append(hdr)
        data = [[Paragraph(lbl, label_st), Paragraph(str(val), value_st)] for (lbl, val) in pairs]
        tbl = Table(data, colWidths=[lab_w, val_w])
        st = [("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 10),
              ("RIGHTPADDING", (0, 0), (-1, -1), 8), ("TOPPADDING", (0, 0), (-1, -1), 6),
              ("BOTTOMPADDING", (0, 0), (-1, -1), 6), ("LINEBELOW", (0, 0), (-1, -2), 0.4, LINE),
              ("BOX", (0, 0), (-1, -1), 0.4, LINE), ("LINEAFTER", (0, 0), (0, -1), 0.4, LINE)]
        for i in range(len(data)):
            if i % 2 == 1:
                st.append(("BACKGROUND", (0, i), (-1, i), ZEBRA))
        tbl.setStyle(TableStyle(st))
        flow.append(tbl)
        flow.append(Spacer(1, 13))
    # Sign-off block (kept together so it never splits across a page break)
    flow.append(Spacer(1, 20))
    flow.append(KeepTogether([
        Paragraph("Signed,", signed_st),
        Spacer(1, 28),
        Paragraph(f"<b>{sig_name}</b>, {sig_title}", signame_st),
        Paragraph(sig_org, sigorg_st),
    ]))
    doc.build(flow, onFirstPage=header_footer, onLaterPages=header_footer)
    return out_path


def main(argv):
    with open(argv[1], "r", encoding="utf-8") as f:
        spec = json.load(f)
    out = build(spec, argv[2])
    print(f"REPLACE_PDF_OK wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
