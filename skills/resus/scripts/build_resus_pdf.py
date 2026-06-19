#!/usr/bin/env python3
"""build_resus_pdf.py -- Cover Re branded counterparty due-diligence PDF.

Same coverre.com scheme as the `replace` terms PDF: near-black header band with
a tan (#C49A6C) accent rule and lowercase 'cover re' wordmark, Times serif
title, light printable body with warm zebra rows. Renders the executive risk
matrix, a per-entity section (identity + each dimension with its flag, summary,
and cited findings, plus the S&P financials block), a sources appendix, and a
methodology / limitations note. Reads the spec JSON documented in reference/report_schema.md.
"""
import datetime as _dt
import html as _html
import json
import sys

from reportlab.lib import colors
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    KeepTogether,
    ListFlowable,
    ListItem,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

BLACK = colors.HexColor("#000000")
NEARBLACK = colors.HexColor("#0E0E0F")
ACCENT = colors.HexColor("#C49A6C")
INK = colors.HexColor("#1A1A1A")
MUTE = colors.HexColor("#6B6862")
LINE = colors.HexColor("#E4E1D9")
ZEBRA = colors.HexColor("#FAF7F2")
HEADER_BG = colors.HexColor("#F3EFE7")
TILE_AMBER = colors.HexColor("#F6EEDB")
ON_DARK = colors.HexColor("#FFFFFF")
ON_DARK_MUTE = colors.HexColor("#9A968D")

FLAG = {
    "red":   {"fill": colors.HexColor("#E8C9C4"), "ink": colors.HexColor("#8E2A1C"), "label": "RED"},
    "amber": {"fill": colors.HexColor("#F1E2BE"), "ink": colors.HexColor("#7E6411"), "label": "AMBER"},
    "green": {"fill": colors.HexColor("#CFE0CC"), "ink": colors.HexColor("#3C6536"), "label": "GREEN"},
    "grey":  {"fill": colors.HexColor("#E5E1D8"), "ink": colors.HexColor("#6E6A60"), "label": "N/A"},
}
ASSESS_LABEL = {
    "verified": "verified (2+ sources)",
    "single-source": "single source",
    "inference": "inference",
    "refuted": "refuted",
}
DIM_ORDER = [
    ("financial_distress", "Financial distress", "Financial"),
    ("leadership", "Leadership & governance", "Leadership"),
    ("partners", "Partner relationships", "Partners"),
    ("litigation", "Litigation", "Litigation"),
    ("reviews", "Customer reviews", "Reviews"),
    ("other", "Other relevant intel", "Other"),
]

DEFAULT_REINSURER = (
    "COVER REINSURANCE SPC, LTD. acting on behalf of and for "
    "COVER REINSURANCE SEGREGATED PORTFOLIO #1"
)
DEFAULT_METHODOLOGY = (
    "Findings are point-in-time, gathered from public sources on the report date and from an "
    "authenticated S&amp;P Capital IQ Pro session. Material adverse claims are corroborated by "
    "two or more independent sources before being marked verified; single-source items are "
    "labelled as such. Dimensions with nothing found are stated explicitly. S&amp;P figures were "
    "transcribed from the cited Capital IQ page on the capture date."
)
DEFAULT_LIMITATIONS = (
    "Absence of a finding is not proof of absence; it reflects what was publicly searchable on "
    "the report date. Litigation entries describe status, not adjudicated liability unless "
    "stated. Verify any material item against the cited primary source before relying on it."
)


def esc(v):
    return _html.escape("" if v is None else str(v))


def flag_norm(v):
    v = str(v or "grey").strip().lower()
    return v if v in FLAG else "grey"


def pretty_date(d):
    if not d:
        return ""
    if isinstance(d, str):
        try:
            d = _dt.date.fromisoformat(d.strip())
        except ValueError:
            return d
    return f"{d.strftime('%B')} {d.day}, {d.year}"


# ---- styles ----------------------------------------------------------------
_styles = getSampleStyleSheet()
S_INTRO = ParagraphStyle("intro", parent=_styles["Normal"], fontName="Helvetica",
                         fontSize=10.5, textColor=INK, leading=15)
S_SECT = ParagraphStyle("sect", parent=_styles["Normal"], fontName="Times-Roman",
                        fontSize=13, textColor=ACCENT, leading=16)
S_LABEL = ParagraphStyle("label", parent=_styles["Normal"], fontName="Helvetica-Bold",
                         fontSize=9, textColor=NEARBLACK, leading=12)
S_VALUE = ParagraphStyle("value", parent=_styles["Normal"], fontName="Helvetica",
                         fontSize=9.5, textColor=INK, leading=13)
S_DIM = ParagraphStyle("dim", parent=_styles["Normal"], fontName="Helvetica-Bold",
                       fontSize=10.5, textColor=NEARBLACK, leading=14)
S_DIM2 = ParagraphStyle("dim2", parent=_styles["Normal"], fontName="Helvetica-Bold",
                        fontSize=9.5, textColor=NEARBLACK, leading=13)
S_SUM = ParagraphStyle("sum", parent=_styles["Normal"], fontName="Helvetica",
                       fontSize=9.5, textColor=INK, leading=13.5)
S_FIND = ParagraphStyle("find", parent=_styles["Normal"], fontName="Helvetica",
                        fontSize=9, textColor=INK, leading=12.5)
S_SRC = ParagraphStyle("src", parent=_styles["Normal"], fontName="Helvetica",
                       fontSize=8, textColor=MUTE, leading=11)
S_NONE = ParagraphStyle("none", parent=_styles["Normal"], fontName="Helvetica-Oblique",
                        fontSize=9, textColor=MUTE, leading=12)
S_MATRIX = ParagraphStyle("mx", parent=_styles["Normal"], fontName="Helvetica",
                          fontSize=7, textColor=INK, leading=8.5)
S_MATRIX_H = ParagraphStyle("mxh", parent=_styles["Normal"], fontName="Helvetica-Bold",
                            fontSize=6.5, textColor=MUTE, leading=8)
S_NOTE = ParagraphStyle("note", parent=_styles["Normal"], fontName="Helvetica",
                        fontSize=8.5, textColor=MUTE, leading=12.5)
S_APX = ParagraphStyle("apx", parent=_styles["Normal"], fontName="Helvetica",
                       fontSize=8.5, textColor=INK, leading=12)


def section_band(title, avail_w):
    hdr = Table([[Paragraph(esc(title).upper(), S_SECT)]], colWidths=[avail_w])
    hdr.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), NEARBLACK),
        ("TEXTCOLOR", (0, 0), (-1, -1), ACCENT),
        ("LINEBEFORE", (0, 0), (0, -1), 2.5, ACCENT),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    return hdr


def risk_matrix(flags, avail_w):
    if not flags:
        return []
    headers = ["Entity"] + [Paragraph(short, S_MATRIX_H) for _, _, short in DIM_ORDER] + \
              [Paragraph("Overall", S_MATRIX_H)]
    headers[0] = Paragraph("Entity / role", S_MATRIX_H)
    data = [headers]
    for r in flags:
        ent = Paragraph(
            f'<b>{esc(r.get("entity",""))}</b><br/><font color="#6B6862">{esc(r.get("role",""))}</font>',
            S_MATRIX)
        row = [ent]
        for key, _, _ in DIM_ORDER:
            row.append(Paragraph(FLAG[flag_norm(r.get(key))]["label"], S_MATRIX))
        row.append(Paragraph(FLAG[flag_norm(r.get("overall"))]["label"], S_MATRIX))
        data.append(row)
    ent_w = 1.7 * inch
    over_w = 0.62 * inch
    dim_w = (avail_w - ent_w - over_w) / len(DIM_ORDER)
    col_w = [ent_w] + [dim_w] * len(DIM_ORDER) + [over_w]
    tbl = Table(data, colWidths=col_w, repeatRows=1)
    st = [
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
        ("ALIGN", (0, 0), (0, -1), "LEFT"),
        ("BOX", (0, 0), (-1, -1), 0.4, LINE),
        ("INNERGRID", (0, 0), (-1, -1), 0.4, LINE),
        ("BACKGROUND", (0, 0), (-1, 0), HEADER_BG),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
    ]
    for ri, r in enumerate(flags, start=1):
        for ci, (key, _, _) in enumerate(DIM_ORDER, start=1):
            f = FLAG[flag_norm(r.get(key))]
            st.append(("BACKGROUND", (ci, ri), (ci, ri), f["fill"]))
            st.append(("TEXTCOLOR", (ci, ri), (ci, ri), f["ink"]))
        fo = FLAG[flag_norm(r.get("overall"))]
        oc = len(DIM_ORDER) + 1
        st.append(("BACKGROUND", (oc, ri), (oc, ri), fo["fill"]))
        st.append(("TEXTCOLOR", (oc, ri), (oc, ri), fo["ink"]))
    tbl.setStyle(TableStyle(st))
    legend = Paragraph(
        '<font color="#6B6862" size=7>RED = material adverse &nbsp;&bull;&nbsp; '
        'AMBER = caution / monitor &nbsp;&bull;&nbsp; GREEN = no material concern '
        '&nbsp;&bull;&nbsp; N/A = not assessed</font>', S_SRC)
    return [tbl, Spacer(1, 5), legend]


def identity_table(resolved, avail_w):
    r = resolved or {}
    pairs = [
        ("Legal name", r.get("legal_name")),
        ("Domain", r.get("domain")),
        ("Jurisdiction", r.get("jurisdiction")),
        ("Identifiers", r.get("identifiers")),
        ("Match confidence", r.get("confidence")),
    ]
    if r.get("note"):
        pairs.append(("Note", r.get("note")))
    pairs = [(k, v) for k, v in pairs if v]
    if not pairs:
        return []
    lab_w = 1.5 * inch
    data = [[Paragraph(esc(k), S_LABEL), Paragraph(esc(v), S_VALUE)] for k, v in pairs]
    tbl = Table(data, colWidths=[lab_w, avail_w - lab_w])
    st = [("VALIGN", (0, 0), (-1, -1), "TOP"), ("BOX", (0, 0), (-1, -1), 0.4, LINE),
          ("LINEAFTER", (0, 0), (0, -1), 0.4, LINE), ("LINEBELOW", (0, 0), (-1, -2), 0.4, LINE),
          ("LEFTPADDING", (0, 0), (-1, -1), 9), ("RIGHTPADDING", (0, 0), (-1, -1), 8),
          ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5)]
    for i in range(len(data)):
        if i % 2 == 1:
            st.append(("BACKGROUND", (0, i), (-1, i), ZEBRA))
    tbl.setStyle(TableStyle(st))
    conf = "CONFIRMED" if r.get("confirmed") else "UNCONFIRMED"
    conf_col = "#9A6A2E" if r.get("confirmed") else "#8E2A1C"
    cap = Paragraph(f'<font color="{conf_col}" size=7><b>IDENTITY &mdash; {conf}</b></font>', S_SRC)
    return [cap, Spacer(1, 3), tbl]


def source_inline(sources):
    if not sources:
        return ""
    parts = []
    for s in sources:
        label = esc(s.get("publisher") or s.get("title") or s.get("url") or "source")
        dt = f' ({esc(s.get("date"))})' if s.get("date") else ""
        url = s.get("url")
        if url:
            parts.append(f'<a href="{esc(url)}" color="#9A6A2E"><u>{label}</u></a>{dt}')
        else:
            parts.append(f'{label}{dt}')
    return '<b><font color="#9A6A2E">Sources:</font></b> ' + " &bull; ".join(parts)


def dimension_flow(dim, avail_w):
    flag = flag_norm(dim.get("flag"))
    f = FLAG[flag]
    label = dim.get("label", "")
    # header row: label | flag pill
    pill = Table([[Paragraph(f["label"], ParagraphStyle(
        "pill", parent=S_FIND, fontName="Helvetica-Bold", fontSize=7.5,
        textColor=f["ink"], alignment=2))]], colWidths=[0.9 * inch])
    pill.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), f["fill"]),
                              ("BOX", (0, 0), (-1, -1), 0.4, LINE),
                              ("TOPPADDING", (0, 0), (-1, -1), 3),
                              ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                              ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                              ("LEFTPADDING", (0, 0), (-1, -1), 7)]))
    hdr = Table([[Paragraph(esc(label), S_DIM), pill]],
                colWidths=[avail_w - 0.9 * inch, 0.9 * inch])
    hdr.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                             ("LEFTPADDING", (0, 0), (-1, -1), 0),
                             ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                             ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]))
    out = [hdr]
    if dim.get("nothing_found"):
        out.append(Paragraph("No adverse findings located.", S_NONE))
        out.append(Spacer(1, 8))
        return out
    if dim.get("summary"):
        out.append(Paragraph(esc(dim["summary"]), S_SUM))
    findings = dim.get("findings") or []
    if findings:
        items = []
        for fnd in findings:
            a = ASSESS_LABEL.get(str(fnd.get("assessment", "")).strip().lower())
            tag = f'<b>[{a}]</b> ' if a else ""
            chunk = [Paragraph(tag + esc(fnd.get("claim", "")), S_FIND)]
            si = source_inline(fnd.get("sources"))
            if si:
                chunk.append(Paragraph(si, S_SRC))
            items.append(ListItem(chunk, leftIndent=10, value=None))
        out.append(Spacer(1, 3))
        out.append(ListFlowable(items, bulletType="bullet", bulletColor=ACCENT,
                                bulletFontSize=7, start="—", leftIndent=12))
    out.append(Spacer(1, 9))
    return out


def outliers_callout(text, avail_w):
    if not text:
        return []
    box = Table([[Paragraph(
        f'<b><font color="#9A6A2E" size=7>CONCERNING TRENDS &amp; OUTLIERS</font></b><br/>'
        f'{esc(text)}', S_SUM)]], colWidths=[avail_w])
    box.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), TILE_AMBER),
                             ("LINEBEFORE", (0, 0), (0, -1), 2.5, ACCENT),
                             ("LEFTPADDING", (0, 0), (-1, -1), 11),
                             ("RIGHTPADDING", (0, 0), (-1, -1), 11),
                             ("TOPPADDING", (0, 0), (-1, -1), 8),
                             ("BOTTOMPADDING", (0, 0), (-1, -1), 8)]))
    return [Spacer(1, 4), box]


def sp_period_table(t, avail_w):
    """Render one multi-period table: columns are value-column headers; each row is
    {label, values[]} with values aligned to columns. Optional row_header for col 0."""
    cols = [str(c) for c in (t.get("columns") or [])]
    rows = t.get("rows") or []
    if not cols or not rows:
        return []
    n = len(cols)
    row_header = t.get("row_header", "")
    fs = 8.5 if n <= 4 else (7.5 if n <= 7 else 6.5)
    cell = ParagraphStyle("spc", parent=S_VALUE, fontSize=fs, leading=fs + 3)
    cell_r = ParagraphStyle("spcr", parent=cell, alignment=2)
    lab = ParagraphStyle("spl", parent=S_LABEL, fontSize=fs, leading=fs + 3)
    hdr_r = ParagraphStyle("sph", parent=S_LABEL, fontSize=fs, leading=fs + 3,
                           textColor=MUTE, alignment=2)
    hdr_l = ParagraphStyle("sphl", parent=hdr_r, alignment=0)
    first_w = max(1.5 * inch, avail_w * (0.30 if n > 4 else 0.36))
    rest_w = (avail_w - first_w) / n
    colw = [first_w] + [rest_w] * n
    data = [[Paragraph(esc(row_header), hdr_l)] + [Paragraph(esc(c), hdr_r) for c in cols]]
    for r in rows:
        vals = list(r.get("values") or [])
        vals = (vals + [""] * n)[:n]
        data.append([Paragraph(esc(r.get("label", "")), lab)]
                    + [Paragraph(esc(v), cell_r) for v in vals])
    tbl = Table(data, colWidths=colw, repeatRows=1)
    st = [("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
          ("BACKGROUND", (0, 0), (-1, 0), HEADER_BG),
          ("BOX", (0, 0), (-1, -1), 0.4, LINE),
          ("INNERGRID", (0, 0), (-1, -1), 0.3, LINE),
          ("LEFTPADDING", (0, 0), (-1, -1), 7), ("RIGHTPADDING", (0, 0), (-1, -1), 7),
          ("TOPPADDING", (0, 0), (-1, -1), 3.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5)]
    for i in range(1, len(data)):
        if i % 2 == 0:
            st.append(("BACKGROUND", (0, i), (-1, i), ZEBRA))
    tbl.setStyle(TableStyle(st))
    out = [Spacer(1, 6),
           Paragraph(f'<b>{esc(t.get("title", ""))}</b>', S_DIM2),
           Spacer(1, 3), tbl]
    out.extend(outliers_callout(t.get("commentary"), avail_w))
    return out


def sp_flow(spf, avail_w):
    if not spf:
        return []
    out = [Paragraph("S&amp;P Capital IQ &mdash; statutory financials &amp; reserves", S_DIM)]
    if not spf.get("available", True):
        reason = spf.get("not_available_reason") or "Not covered in S&P Capital IQ."
        out.append(Paragraph(esc(reason), S_NONE))
        out.append(Spacer(1, 9))
        return out
    if spf.get("as_of"):
        out.append(Paragraph(f'<font color="#6B6862" size=8>As of: {esc(spf["as_of"])}</font>', S_SRC))
    # Preferred: multi-period tables
    for t in (spf.get("tables") or []):
        out.extend(sp_period_table(t, avail_w))
    # Legacy: flat metrics list
    metrics = spf.get("metrics") or []
    if metrics:
        lab_w = 2.6 * inch
        data = []
        for m in metrics:
            period = f'  ({esc(m.get("period"))})' if m.get("period") else ""
            data.append([Paragraph(esc(m.get("label", "")), S_LABEL),
                         Paragraph(esc(m.get("value", "")) + period, S_VALUE)])
        tbl = Table(data, colWidths=[lab_w, avail_w - lab_w])
        stt = [("VALIGN", (0, 0), (-1, -1), "TOP"), ("BOX", (0, 0), (-1, -1), 0.4, LINE),
               ("LINEAFTER", (0, 0), (0, -1), 0.4, LINE), ("LINEBELOW", (0, 0), (-1, -2), 0.4, LINE),
               ("LEFTPADDING", (0, 0), (-1, -1), 9), ("RIGHTPADDING", (0, 0), (-1, -1), 8),
               ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4)]
        for i in range(len(data)):
            if i % 2 == 1:
                stt.append(("BACKGROUND", (0, i), (-1, i), ZEBRA))
        tbl.setStyle(TableStyle(stt))
        out.append(Spacer(1, 3))
        out.append(tbl)
    if spf.get("annual_statement"):
        out.append(Spacer(1, 6))
        out.append(Paragraph(f'<b>Annual statement:</b> {esc(spf["annual_statement"])}', S_SUM))
    if spf.get("source_url"):
        cap = f' &middot; captured {esc(spf.get("captured"))}' if spf.get("captured") else ""
        out.append(Spacer(1, 4))
        out.append(Paragraph(
            f'<b><font color="#9A6A2E">Source:</font></b> '
            f'<a href="{esc(spf["source_url"])}" color="#9A6A2E"><u>S&amp;P Capital IQ Pro</u></a>{cap}',
            S_SRC))
    out.append(Spacer(1, 9))
    return out


def collect_sources(entities):
    seen, out = set(), []
    for e in entities or []:
        for d in e.get("dimensions") or []:
            for fnd in d.get("findings") or []:
                for s in fnd.get("sources") or []:
                    key = s.get("url") or (s.get("title"), s.get("publisher"))
                    if key in seen:
                        continue
                    seen.add(key)
                    out.append(s)
        spf = e.get("sp_financials") or {}
        if spf.get("source_url") and spf["source_url"] not in seen:
            seen.add(spf["source_url"])
            out.append({"title": "S&P Capital IQ Pro tearsheet", "publisher": "S&P Global",
                        "url": spf["source_url"], "date": spf.get("captured")})
    return out


def ordered_dimensions(entity):
    given = {d.get("key"): d for d in (entity.get("dimensions") or [])}
    out = []
    for key, label, _ in DIM_ORDER:
        if key in given:
            d = dict(given[key])
            d.setdefault("label", label)
            out.append(d)
    for d in entity.get("dimensions") or []:
        if d.get("key") not in {k for k, _, _ in DIM_ORDER}:
            out.append(d)
    return out


def counterparties_block(entities, flags, avail_w):
    """A compact 'who is being vetted' strip: role, name, and overall flag per entity."""
    if not entities:
        return []
    overall = {r.get("entity"): flag_norm(r.get("overall")) for r in (flags or []) if r.get("entity")}
    rows = []
    for e in entities:
        role = (e.get("role") or "").upper()
        name = e.get("name", "")
        f = FLAG[overall.get(name, "grey")]
        pill = Table([[Paragraph(f["label"], ParagraphStyle(
            "cpp", parent=S_FIND, fontName="Helvetica-Bold", fontSize=7.5,
            textColor=f["ink"], alignment=1))]], colWidths=[0.8 * inch])
        pill.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), f["fill"]),
                                  ("BOX", (0, 0), (-1, -1), 0.4, LINE),
                                  ("TOPPADDING", (0, 0), (-1, -1), 2),
                                  ("BOTTOMPADDING", (0, 0), (-1, -1), 2)]))
        rows.append([
            Paragraph(f'<font color="#9A6A2E" size=8><b>{esc(role)}</b></font>', S_SRC),
            Paragraph(f'<b>{esc(name)}</b>', S_VALUE),
            pill,
        ])
    inner_w = avail_w - 24
    role_w, pill_w = 1.1 * inch, 0.85 * inch
    inner = Table(rows, colWidths=[role_w, inner_w - role_w - pill_w, pill_w])
    ist = [("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
           ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0),
           ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4)]
    for i in range(len(rows) - 1):
        ist.append(("LINEBELOW", (0, i), (-1, i), 0.3, LINE))
    inner.setStyle(TableStyle(ist))
    header = Paragraph('<b><font color="#9A6A2E" size=7>COUNTERPARTIES VETTED</font></b>', S_SUM)
    box = Table([[header], [inner]], colWidths=[avail_w])
    box.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), HEADER_BG),
                             ("LINEBEFORE", (0, 0), (0, -1), 2.5, ACCENT),
                             ("LEFTPADDING", (0, 0), (-1, -1), 12), ("RIGHTPADDING", (0, 0), (-1, -1), 12),
                             ("TOPPADDING", (0, 0), (0, 0), 9), ("BOTTOMPADDING", (0, 0), (0, 0), 3),
                             ("TOPPADDING", (0, 1), (0, 1), 0), ("BOTTOMPADDING", (0, 1), (0, 1), 9)]))
    return [box, Spacer(1, 12)]


def build(spec, out_path):
    meta = spec.get("meta", {})
    summary = spec.get("summary", {})
    entities = spec.get("entities", [])
    reinsurer = meta.get("reinsurer", DEFAULT_REINSURER)
    title = meta.get("title", "Counterparty Due Diligence")
    date_str = meta.get("date") or pretty_date(_dt.date.today())
    footer_text = meta.get("confidentiality_footer") or (
        "Confidential and proprietary to Cover Re. Counterparty due diligence; findings are "
        "sourced and point-in-time. Not to be reproduced without prior written consent.")

    avail_w = LETTER[0] - 1.5 * inch

    def header_footer(canvas, doc):
        canvas.saveState()
        w, h = LETTER
        band_h = 1.15 * inch
        canvas.setFillColor(BLACK)
        canvas.rect(0, h - band_h, w, band_h, fill=1, stroke=0)
        canvas.setFillColor(ACCENT)
        canvas.rect(0, h - band_h, w, 2.2, fill=1, stroke=0)
        x = 0.75 * inch
        yw = h - 0.4 * inch
        canvas.setFillColor(ON_DARK)
        canvas.setFont("Helvetica", 15)
        canvas.drawString(x, yw, "cover ")
        wlen = canvas.stringWidth("cover ", "Helvetica", 15)
        canvas.setFont("Helvetica-Bold", 15)
        canvas.drawString(x + wlen, yw, "re")
        canvas.setFillColor(ON_DARK)
        canvas.setFont("Times-Roman", 19)
        canvas.drawString(x, h - 0.82 * inch, title)
        canvas.setFillColor(ON_DARK_MUTE)
        canvas.setFont("Helvetica", 8.5)
        canvas.drawRightString(w - 0.75 * inch, h - 0.82 * inch, date_str)
        canvas.setFont("Helvetica", 7)
        canvas.drawRightString(w - 0.75 * inch, h - 0.45 * inch, reinsurer.upper())
        canvas.setStrokeColor(LINE)
        canvas.setLineWidth(0.5)
        canvas.line(0.75 * inch, 0.7 * inch, w - 0.75 * inch, 0.7 * inch)
        canvas.setFillColor(MUTE)
        canvas.setFont("Helvetica", 6.5)
        canvas.drawString(0.75 * inch, 0.5 * inch, footer_text[:160])
        canvas.setFont("Helvetica", 7)
        canvas.drawRightString(w - 0.75 * inch, 0.5 * inch, f"Page {doc.page}")
        canvas.restoreState()

    doc = SimpleDocTemplate(out_path, pagesize=LETTER, leftMargin=0.75 * inch,
                            rightMargin=0.75 * inch, topMargin=1.45 * inch,
                            bottomMargin=0.9 * inch, title=title, author=reinsurer)
    flow = []
    flow.extend(counterparties_block(entities, summary.get("flags"), avail_w))
    if summary.get("headline"):
        intro = Table([[Paragraph(f'<b><font color="#9A6A2E" size=7>BOTTOM LINE</font></b><br/>'
                                  f'{esc(summary["headline"])}', S_INTRO)]], colWidths=[avail_w])
        intro.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), ZEBRA),
                                   ("LINEBEFORE", (0, 0), (0, -1), 2.5, ACCENT),
                                   ("LEFTPADDING", (0, 0), (-1, -1), 12),
                                   ("RIGHTPADDING", (0, 0), (-1, -1), 12),
                                   ("TOPPADDING", (0, 0), (-1, -1), 10),
                                   ("BOTTOMPADDING", (0, 0), (-1, -1), 10)]))
        flow.append(intro)
        flow.append(Spacer(1, 14))

    if summary.get("flags"):
        flow.append(section_band("Executive Risk Matrix", avail_w))
        flow.append(Spacer(1, 8))
        flow.extend(risk_matrix(summary["flags"], avail_w))
        flow.append(Spacer(1, 16))

    for e in entities:
        role = e.get("role", "")
        head = f'{role}: {e.get("name","")}' if role else e.get("name", "")
        block = [section_band(head, avail_w), Spacer(1, 8)]
        block.extend(identity_table(e.get("resolved"), avail_w))
        block.append(Spacer(1, 10))
        flow.append(KeepTogether(block))
        for d in ordered_dimensions(e):
            flow.extend(dimension_flow(d, avail_w))
        if e.get("sp_financials"):
            flow.extend(sp_flow(e["sp_financials"], avail_w))
        flow.append(Spacer(1, 10))

    srcs = collect_sources(entities)
    if srcs:
        flow.append(section_band("Sources", avail_w))
        flow.append(Spacer(1, 8))
        items = []
        for s in srcs:
            dt = f' &middot; {esc(s.get("date"))}' if s.get("date") else ""
            pub = f' &mdash; {esc(s.get("publisher"))}' if s.get("publisher") else ""
            title_t = esc(s.get("title") or s.get("url") or "source")
            url = s.get("url")
            link = (f'<a href="{esc(url)}" color="#9A6A2E"><u>{title_t}</u></a>' if url else title_t)
            items.append(ListItem([Paragraph(f"{link}{pub}{dt}", S_APX)], leftIndent=12))
        flow.append(ListFlowable(items, bulletType="1", bulletFormat="%s.",
                                 bulletFontSize=8, leftIndent=16))
        flow.append(Spacer(1, 14))

    flow.append(section_band("Methodology & Limitations", avail_w))
    flow.append(Spacer(1, 8))
    flow.append(Paragraph(spec.get("methodology") or DEFAULT_METHODOLOGY, S_NOTE))
    flow.append(Spacer(1, 6))
    flow.append(Paragraph(spec.get("limitations") or DEFAULT_LIMITATIONS, S_NOTE))

    doc.build(flow, onFirstPage=header_footer, onLaterPages=header_footer)
    return out_path


def main(argv):
    if len(argv) < 3:
        print("usage: build_resus_pdf.py <spec.json> <out.pdf>", file=sys.stderr)
        return 2
    with open(argv[1], "r", encoding="utf-8") as f:
        spec = json.load(f)
    out = build(spec, argv[2])
    print(f"RESUS_PDF_OK wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
