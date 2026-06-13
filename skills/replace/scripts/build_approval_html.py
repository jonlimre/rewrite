#!/usr/bin/env python3
"""build_approval_html.py -- Cover Re branded, Outlook-safe approval request.

LIGHT theme matching coverre.com brand cues (warm tan accent, lowercase
'cover re' wordmark, Cormorant-serif headings) on a white/warm-off-white body.

Why light: pasting a dark email into the Outlook compose window often drops
cell background colors, which would leave light text invisible on white. A light
theme keeps every text element DARK on light, so it stays fully readable even if
Outlook strips the backgrounds on paste. Bars/tiles degrade gracefully (the
numeric value sits beside each bar).

Email-safe: inline CSS only, table layout, table-based bar charts with bgcolor
fills (renders in Outlook), no SVG, no script, no external assets, ASCII source.
"""
import html
import json
import sys

# ---- Cover Re palette (light, paste-robust) -------------------------------
PAGE = "#ECEAE4"        # outer area behind the card (warm light)
CARD = "#FFFFFF"        # card body
HEADER = "#F7F4EE"      # header band (warm off-white; degrades to white safely)
INK = "#15140F"         # headings / wordmark (near-black)
TEXT = "#26241F"        # body text (dark warm gray)
MUTE = "#7A756B"        # muted labels (readable on white)
ACCENT = "#9A6A2E"      # darker tan for TEXT accents (contrast on white)
ACCENT_FILL = "#C49A6C"  # brand tan for bar fills / rules (decorative)
LINE = "#E2DED5"        # hairline
TILE = "#FAF7F2"        # KPI tile / callout fill
ZEBRA = "#F7F4EE"       # alternate row fill
HEADROW = "#F3E9DB"     # weakness header row (tan tint)
BAR = "#C49A6C"         # bar fill (tan)
BAR_BG = "#ECE7DD"      # bar track (light)

SANS = "'Inter', Arial, Helvetica, sans-serif"
SERIF = "'Cormorant Garamond', Georgia, 'Times New Roman', serif"
WORD = "'Outfit', 'Helvetica Neue', Arial, sans-serif"

# --- US tile-grid cartogram -------------------------------------------------
# (row, col) per state on an 8-row x 11-col grid, laid out ~geographically.
GRID_ROWS = 8
GRID_COLS = 11
STATE_GRID = {
    "AK": (0, 0), "ME": (0, 10),
    "VT": (1, 9), "NH": (1, 10),
    "WA": (2, 0), "ID": (2, 1), "MT": (2, 2), "ND": (2, 3), "MN": (2, 4),
    "WI": (2, 5), "MI": (2, 7), "NY": (2, 8), "MA": (2, 9), "RI": (2, 10),
    "OR": (3, 0), "NV": (3, 1), "WY": (3, 2), "SD": (3, 3), "IA": (3, 4),
    "IL": (3, 5), "IN": (3, 6), "OH": (3, 7), "PA": (3, 8), "NJ": (3, 9), "CT": (3, 10),
    "CA": (4, 0), "UT": (4, 1), "CO": (4, 2), "NE": (4, 3), "MO": (4, 4),
    "KY": (4, 5), "WV": (4, 6), "VA": (4, 7), "MD": (4, 8), "DE": (4, 9),
    "AZ": (5, 1), "NM": (5, 2), "KS": (5, 3), "AR": (5, 4), "TN": (5, 5),
    "NC": (5, 6), "SC": (5, 7), "DC": (5, 8),
    "OK": (6, 3), "LA": (6, 4), "MS": (6, 5), "AL": (6, 6), "GA": (6, 7),
    "HI": (7, 0), "TX": (7, 3), "FL": (7, 8),
}
POS2STATE = {pos: code for code, pos in STATE_GRID.items()}
NAME2CODE = {
    "alabama": "AL", "alaska": "AK", "arizona": "AZ", "arkansas": "AR",
    "california": "CA", "colorado": "CO", "connecticut": "CT", "delaware": "DE",
    "district of columbia": "DC", "washington dc": "DC", "florida": "FL",
    "georgia": "GA", "hawaii": "HI", "idaho": "ID", "illinois": "IL",
    "indiana": "IN", "iowa": "IA", "kansas": "KS", "kentucky": "KY",
    "louisiana": "LA", "maine": "ME", "maryland": "MD", "massachusetts": "MA",
    "michigan": "MI", "minnesota": "MN", "mississippi": "MS", "missouri": "MO",
    "montana": "MT", "nebraska": "NE", "nevada": "NV", "new hampshire": "NH",
    "new jersey": "NJ", "new mexico": "NM", "new york": "NY",
    "north carolina": "NC", "north dakota": "ND", "ohio": "OH", "oklahoma": "OK",
    "oregon": "OR", "pennsylvania": "PA", "rhode island": "RI",
    "south carolina": "SC", "south dakota": "SD", "tennessee": "TN",
    "texas": "TX", "utah": "UT", "vermont": "VT", "virginia": "VA",
    "washington": "WA", "west virginia": "WV", "wisconsin": "WI", "wyoming": "WY",
}
MAP_RAMP = ["#F2E2CC", "#E6C99E", "#D6AC72", "#C08C4B", "#9A6A2E"]  # light -> dark tan
MAP_NODATA = "#EDEBE5"      # state present but no premium
MAP_TEXT_DARK = "#2A2520"
MAP_TEXT_LIGHT = "#FFFFFF"
MAP_TEXT_NODATA = "#AAA499"


def esc(v):
    return html.escape("" if v is None else str(v))


def basis_label(basis):
    b = (basis or "").strip().upper()
    if b == "RAD":
        return "Risk Attaching During (RAD)"
    if b == "LOD":
        return "Losses Occurring During (LOD)"
    return esc(basis)


def wordmark(size=24):
    return (
        f'<span style="font-family:{WORD};font-size:{size}px;letter-spacing:1px;'
        f'color:{INK};"><span style="font-weight:300;">cover </span>'
        f'<span style="font-weight:700;">re</span></span>'
    )


def _bar_row(label, value, vmax):
    pct = (value / vmax * 100.0) if vmax else 0.0
    filled = max(2, min(100, round(pct)))
    rest = 100 - filled
    vtxt = "%g" % value
    cs = "height:13px;line-height:13px;font-size:1px;mso-line-height-rule:exactly;"
    filled_cell = (
        f'<td bgcolor="{BAR}" width="{filled}%" style="background-color:{BAR};{cs}">&#8202;</td>'
    )
    rest_cell = (
        f'<td bgcolor="{BAR_BG}" width="{rest}%" style="background-color:{BAR_BG};{cs}">&#8202;</td>'
        if rest > 0
        else ""
    )
    return (
        f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" '
        f'style="border-collapse:collapse;"><tr>'
        f'<td width="160" valign="middle" style="font-family:{SANS};font-size:13px;'
        f'color:{TEXT};padding:5px 8px 5px 0;">{esc(label)}</td>'
        f'<td valign="middle" style="padding:5px 0;">'
        f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" '
        f'style="border-collapse:collapse;"><tr>{filled_cell}{rest_cell}</tr></table></td>'
        f'<td width="44" align="right" valign="middle" style="font-family:{SANS};'
        f'font-size:12px;color:{MUTE};padding:5px 0 5px 8px;">{esc(vtxt)}</td>'
        f'</tr></table>'
    )


def bar_chart(series):
    rows = [r for r in (series or []) if r.get("value") is not None]
    if not rows:
        return ""
    vmax = max(float(r["value"]) for r in rows) or 1.0
    return "".join(_bar_row(r.get("label", ""), float(r["value"]), vmax) for r in rows)


def _state_code(s):
    s = str(s or "").strip()
    if len(s) == 2 and s.upper() in STATE_GRID:
        return s.upper()
    return NAME2CODE.get(s.lower())


def geo_map_block(title, series):
    """US tile-grid cartogram: one shaded table cell per state, colored by
    premium intensity. Pure HTML table + bgcolor, so it renders in Outlook."""
    data = {}
    items = series.items() if isinstance(series, dict) else [
        (r.get("state", r.get("label")), r.get("value")) for r in (series or [])
    ]
    for k, v in items:
        if v is None:
            continue
        code = _state_code(k)
        if code:
            data[code] = float(v)
    if not data:
        return ""
    vmax = max(data.values()) or 1.0
    cell = "width=\"38\" height=\"30\""
    grid_rows = ""
    for r in range(GRID_ROWS):
        cells = ""
        for c in range(GRID_COLS):
            code = POS2STATE.get((r, c))
            if not code:
                cells += f'<td {cell} style="font-size:1px;line-height:1px;">&nbsp;</td>'
                continue
            if code in data:
                b = max(0, min(4, int(data[code] / vmax * 4.999)))
                bg = MAP_RAMP[b]
                tc = MAP_TEXT_DARK if b <= 2 else MAP_TEXT_LIGHT
            else:
                bg, tc = MAP_NODATA, MAP_TEXT_NODATA
            cells += (
                f'<td {cell} align="center" valign="middle" bgcolor="{bg}" '
                f'style="background-color:{bg};font-family:{SANS};font-size:10px;'
                f'font-weight:bold;color:{tc};">{code}</td>'
            )
        grid_rows += f"<tr>{cells}</tr>"
    grid = (
        f'<table role="presentation" cellpadding="0" cellspacing="3" '
        f'style="border-collapse:separate;">{grid_rows}</table>'
    )
    sw = "".join(
        f'<td width="22" height="10" bgcolor="{col}" style="background-color:{col};'
        f'font-size:1px;line-height:1px;">&nbsp;</td>'
        for col in MAP_RAMP
    )
    legend = (
        f'<table role="presentation" cellpadding="0" cellspacing="2"><tr>'
        f'<td style="font-family:{SANS};font-size:10px;color:{MUTE};padding-right:7px;">Lower</td>'
        f'{sw}'
        f'<td style="font-family:{SANS};font-size:10px;color:{MUTE};padding-left:7px;">'
        f'Higher premium share</td></tr></table>'
    )
    return (
        f'<tr><td style="padding:16px 32px 4px 32px;">'
        f'<div style="font-family:{SANS};font-size:11px;font-weight:bold;color:{MUTE};'
        f'text-transform:uppercase;letter-spacing:.09em;padding-bottom:9px;">{esc(title)}</div>'
        f'{grid}<div style="height:9px;line-height:9px;font-size:1px;">&nbsp;</div>{legend}'
        f'</td></tr>'
    )


def section_heading(num, text):
    nlabel = f"{num:02d}"
    return (
        f'<tr><td style="padding:28px 32px 0 32px;">'
        f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0">'
        f'<tr><td style="border-bottom:1px solid {LINE};padding-bottom:9px;">'
        f'<span style="font-family:{SANS};font-size:11px;font-weight:bold;color:{ACCENT};'
        f'letter-spacing:.14em;">{nlabel}</span>'
        f'<span style="font-family:{SANS};font-size:11px;color:{MUTE};">&nbsp;&nbsp;&mdash;&nbsp;&nbsp;</span>'
        f'<span style="font-family:{SERIF};font-size:23px;font-weight:normal;color:{INK};'
        f'letter-spacing:.01em;">{esc(text)}</span>'
        f'</td></tr></table></td></tr>'
    )


def para(text):
    return (
        f'<tr><td style="padding:14px 32px 4px 32px;font-family:{SANS};font-size:14px;'
        f'line-height:1.65;color:{TEXT};">{esc(text)}</td></tr>'
    )


def bullet_list(items):
    if not items:
        return ""
    lis = "".join(
        f'<tr><td valign="top" width="18" style="font-family:{SANS};font-size:14px;'
        f'color:{ACCENT};line-height:1.6;">&#8212;</td>'
        f'<td style="font-family:{SANS};font-size:14px;line-height:1.6;color:{TEXT};'
        f'padding-bottom:8px;padding-left:4px;">{esc(it)}</td></tr>'
        for it in items
    )
    return (
        f'<tr><td style="padding:12px 32px 6px 32px;">'
        f'<table role="presentation" cellpadding="0" cellspacing="0" width="100%">{lis}</table>'
        f'</td></tr>'
    )


def kpi_tiles(metrics):
    if not metrics:
        return ""
    tiles = list(metrics)
    rows_html = ""
    for i in range(0, len(tiles), 3):
        chunk = tiles[i : i + 3]
        tds = ""
        for m in chunk:
            tds += (
                f'<td width="33%" valign="top" style="padding:5px;">'
                f'<table role="presentation" cellpadding="0" cellspacing="0" width="100%" '
                f'bgcolor="{TILE}" style="background-color:{TILE};border:1px solid {LINE};">'
                f'<tr><td style="padding:13px 15px;font-family:{SANS};">'
                f'<div style="font-size:10px;color:{MUTE};text-transform:uppercase;'
                f'letter-spacing:.09em;">{esc(m.get("label",""))}</div>'
                f'<div style="font-size:21px;font-weight:bold;color:{INK};'
                f'padding-top:6px;letter-spacing:-.01em;">{esc(m.get("value",""))}</div>'
                f"</td></tr></table></td>"
            )
        for _ in range(3 - len(chunk)):
            tds += '<td width="33%"></td>'
        rows_html += f"<tr>{tds}</tr>"
    return (
        f'<tr><td style="padding:14px 27px 6px 27px;">'
        f'<table role="presentation" cellpadding="0" cellspacing="0" width="100%">{rows_html}</table>'
        f'</td></tr>'
    )


def chart_block(title, series):
    bars = bar_chart(series)
    if not bars:
        return ""
    return (
        f'<tr><td style="padding:16px 32px 4px 32px;">'
        f'<div style="font-family:{SANS};font-size:11px;font-weight:bold;color:{MUTE};'
        f'text-transform:uppercase;letter-spacing:.09em;padding-bottom:9px;">{esc(title)}</div>'
        f'{bars}</td></tr>'
    )


def weaknesses_block(weaknesses):
    if not weaknesses:
        return ""
    header = (
        f'<tr>'
        f'<td width="46%" bgcolor="{HEADROW}" style="background-color:{HEADROW};'
        f'font-family:{SANS};font-size:10px;font-weight:bold;color:{ACCENT};'
        f'text-transform:uppercase;letter-spacing:.11em;padding:10px 13px;'
        f'border:1px solid {LINE};">Concern</td>'
        f'<td bgcolor="{HEADROW}" style="background-color:{HEADROW};font-family:{SANS};'
        f'font-size:10px;font-weight:bold;color:{ACCENT};text-transform:uppercase;'
        f'letter-spacing:.11em;padding:10px 13px;border:1px solid {LINE};">'
        f'Mitigant &mdash; why we&rsquo;re okay</td></tr>'
    )
    rows = ""
    for i, w in enumerate(weaknesses):
        bg = CARD if i % 2 == 0 else ZEBRA
        rows += (
            f'<tr>'
            f'<td valign="top" bgcolor="{bg}" style="background-color:{bg};font-family:{SANS};'
            f'font-size:13.5px;line-height:1.6;color:{TEXT};padding:11px 13px;'
            f'border:1px solid {LINE};">{esc(w.get("point",""))}</td>'
            f'<td valign="top" bgcolor="{bg}" style="background-color:{bg};font-family:{SANS};'
            f'font-size:13.5px;line-height:1.6;color:{TEXT};padding:11px 13px;'
            f'border:1px solid {LINE};">{esc(w.get("mitigant",""))}</td></tr>'
        )
    return (
        f'<tr><td style="padding:12px 32px 6px 32px;">'
        f'<table role="presentation" cellpadding="0" cellspacing="0" width="100%" '
        f'style="border-collapse:collapse;">{header}{rows}</table></td></tr>'
    )


def terms_rows(terms):
    t = terms or {}
    out = []

    def add(label, val):
        if val:
            out.append((label, val))

    add("Cedent", t.get("cedent"))
    add("MGA", t.get("mga"))
    add("Reinsurance broker", t.get("reinsurance_broker"))
    term = t.get("term") or {}
    if term:
        dates = ""
        if term.get("effective") or term.get("expiry"):
            dates = f' ({esc(term.get("effective",""))} to {esc(term.get("expiry",""))})'
        add("Term", f"{basis_label(term.get('basis'))}{dates}")
    add("Subject business", t.get("subject_business"))
    add("Subject premium", t.get("subject_premium"))
    add("Excess allowance", t.get("excess_allowance"))
    add("Share", t.get("share"))
    add("Premium caps", t.get("premium_caps"))
    add("Ceding commission", t.get("ceding_commission"))
    ss = t.get("sliding_scale")
    if isinstance(ss, list) and ss:
        add("Sliding scale", "; ".join(
            f'{esc(r.get("loss_ratio",""))} &rarr; {esc(r.get("commission",""))}' for r in ss))
    elif ss:
        add("Sliding scale", ss)
    add("Loss corridor", t.get("loss_corridor"))
    add("Profit commission", t.get("profit_commission"))
    add("Aggregate CAT cap", t.get("aggregate_cat_cap"))
    add("ECO / XPL cap", t.get("eco_xpl_cap"))
    add("Aggregate loss-ratio cap", t.get("aggregate_loss_ratio_cap"))
    # Exclusions -- always includes Cannabis Operations
    _excl = t.get("exclusions")
    if isinstance(_excl, str):
        _excl = [_excl] if _excl.strip() else []
    _excl = [str(e).strip() for e in (_excl or []) if str(e).strip()]
    if not any("cannabis" in e.lower() for e in _excl):
        _excl.append("Cannabis Operations")
    out.append(("Exclusions", "; ".join(_excl)))
    add("Reporting requirements", t.get("reporting_requirements"))
    add("Collateral factors", t.get("collateral_factors")
        or "110% of unpaid loss + 100% of unearned ceded premium net of receivables")
    add("Remittance", t.get("remittance") or "90% to trust account / 10% to operating account")
    return out


def terms_table(terms):
    rows = terms_rows(terms)
    if not rows:
        return ""
    trs = ""
    for i, (label, val) in enumerate(rows):
        bg = CARD if i % 2 == 0 else ZEBRA
        val_html = val if label in ("Term", "Sliding scale") else esc(val)
        trs += (
            f'<tr>'
            f'<td valign="top" width="34%" bgcolor="{bg}" style="background-color:{bg};'
            f'font-family:{SANS};font-size:12.5px;font-weight:bold;color:{INK};'
            f'letter-spacing:.01em;padding:10px 14px;border:1px solid {LINE};">{esc(label)}</td>'
            f'<td valign="top" bgcolor="{bg}" style="background-color:{bg};font-family:{SANS};'
            f'font-size:12.5px;line-height:1.6;color:{TEXT};padding:10px 14px;'
            f'border:1px solid {LINE};">{val_html}</td></tr>'
        )
    return (
        f'<tr><td style="padding:12px 32px 16px 32px;">'
        f'<table role="presentation" cellpadding="0" cellspacing="0" width="100%" '
        f'style="border-collapse:collapse;">{trs}</table></td></tr>'
    )


def build(spec):
    meta = spec.get("meta", {})
    nar = spec.get("narrative", {})
    charts = spec.get("charts", {})
    terms = spec.get("terms", {})

    reinsurer = meta.get(
        "reinsurer",
        "COVER REINSURANCE SPC, LTD. acting on behalf of and for "
        "COVER REINSURANCE SEGREGATED PORTFOLIO #1",
    )
    title = meta.get("title", "Reinsurance Authorization Request")

    head_meta = []
    if meta.get("date"):
        head_meta.append(esc(meta["date"]))
    if meta.get("prepared_by"):
        head_meta.append(f'Prepared by: {esc(meta["prepared_by"])}')
    head_meta_html = (
        f'<div style="font-family:{SANS};font-size:12px;color:{MUTE};'
        f'padding-top:14px;letter-spacing:.02em;">{" &nbsp;&middot;&nbsp; ".join(head_meta)}</div>'
        if head_meta else ""
    )

    rows = []
    n = [0]

    def heading(text):
        n[0] += 1
        return section_heading(n[0], text)

    # header band: wordmark, serif title, meta, tan accent rule (light, paste-robust)
    rows.append(
        f'<tr><td bgcolor="{HEADER}" style="background-color:{HEADER};'
        f'padding:30px 32px 0 32px;border-bottom:1px solid {LINE};">{wordmark(24)}'
        f'<div style="font-family:{SERIF};font-size:31px;font-weight:normal;color:{INK};'
        f'padding-top:16px;letter-spacing:.01em;">{esc(title)}</div>'
        f'<div style="font-family:{SANS};font-size:10px;color:{MUTE};text-transform:uppercase;'
        f'letter-spacing:.14em;padding-top:10px;">{esc(reinsurer)}</div>'
        f'{head_meta_html}'
        f'<div style="font-size:0;line-height:0;height:22px;">&nbsp;</div>'
        f'</td></tr>'
        f'<tr><td bgcolor="{ACCENT_FILL}" style="background-color:{ACCENT_FILL};font-size:0;'
        f'line-height:0;height:3px;mso-line-height-rule:exactly;">&#8202;</td></tr>'
    )

    if nar.get("recommendation"):
        rows.append(
            f'<tr><td style="padding:26px 32px 0 32px;">'
            f'<table role="presentation" cellpadding="0" cellspacing="0" width="100%" '
            f'bgcolor="{TILE}" style="background-color:{TILE};border-left:3px solid {ACCENT_FILL};">'
            f'<tr><td style="padding:17px 21px;font-family:{SANS};">'
            f'<div style="font-size:10px;font-weight:bold;color:{ACCENT};'
            f'text-transform:uppercase;letter-spacing:.13em;">Recommendation</div>'
            f'<div style="font-size:15.5px;line-height:1.65;color:{INK};'
            f'padding-top:8px;">{esc(nar["recommendation"])}</div>'
            f"</td></tr></table></td></tr>"
        )

    if nar.get("business_summary"):
        rows.append(heading("Subject Business Summary"))
        rows.append(para(nar["business_summary"]))

    has_risk = (
        nar.get("risk_profile_notes") or charts.get("geo") or charts.get("class")
        or charts.get("limits") or nar.get("other_metrics")
    )
    if has_risk:
        rows.append(heading("Risk Profile"))
        if nar.get("risk_profile_notes"):
            rows.append(para(nar["risk_profile_notes"]))
        rows.append(kpi_tiles(nar.get("other_metrics")))
        rows.append(chart_block("Geographic mix", charts.get("geo")))
        rows.append(geo_map_block("Geographic premium intensity", charts.get("geo_map")))
        rows.append(chart_block("Class / line-of-business mix", charts.get("class")))
        rows.append(chart_block("Limit / attachment bands", charts.get("limits")))

    if nar.get("strengths"):
        rows.append(heading("Strengths"))
        rows.append(bullet_list(nar["strengths"]))

    if nar.get("weaknesses"):
        rows.append(heading("Weaknesses & Mitigants"))
        rows.append(weaknesses_block(nar["weaknesses"]))

    if terms_rows(terms):
        rows.append(heading("Proposed Terms"))
        rows.append(terms_table(terms))

    if nar.get("noteworthy"):
        rows.append(heading("Other Noteworthy Items"))
        rows.append(bullet_list(nar["noteworthy"]))

    rows.append(
        f'<tr><td style="padding:24px 32px 28px 32px;border-top:1px solid {LINE};">'
        f'<div style="font-family:{SANS};font-size:10.5px;color:{MUTE};line-height:1.65;'
        f'letter-spacing:.01em;">{esc(reinsurer)}. Confidential &mdash; prepared for '
        f'committee evaluation. Detailed authorization terms are provided in the '
        f'accompanying terms sheet.</div></td></tr>'
    )

    body_rows = "".join(r for r in rows if r)

    doc = (
        f'<!DOCTYPE html><html><head><meta charset="utf-8">'
        f'<meta name="viewport" content="width=device-width,initial-scale=1">'
        f"<title>{esc(title)}</title></head>"
        f'<body style="margin:0;padding:0;background-color:{PAGE};">'
        f'<table role="presentation" cellpadding="0" cellspacing="0" width="100%" '
        f'bgcolor="{PAGE}" style="background-color:{PAGE};"><tr>'
        f'<td align="center" style="padding:22px;">'
        f'<table role="presentation" cellpadding="0" cellspacing="0" width="680" '
        f'bgcolor="{CARD}" style="width:680px;max-width:680px;background-color:{CARD};'
        f'border:1px solid {LINE};">'
        f"{body_rows}"
        f"</table></td></tr></table></body></html>"
    )
    return doc


def main(argv):
    with open(argv[1], "r", encoding="utf-8") as f:
        spec = json.load(f)
    doc = build(spec)
    with open(argv[2], "w", encoding="utf-8") as f:
        f.write(doc)
    print(f"REPLACE_HTML_OK wrote {argv[2]} ({len(doc)} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
