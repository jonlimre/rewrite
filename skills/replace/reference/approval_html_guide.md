# `replace` — HTML approval-request guide

The HTML approval request is the email the underwriter sends to the committee asking for
authorization. It must survive **pasting into an email body**, so the builder enforces:

- **Inline CSS only** — every style attribute lives on its element. No `<style>` block
  (Gmail keeps it, Outlook desktop strips it), no class-based theming.
- **Layout via tables**, not flexbox/grid — Outlook's Word rendering engine ignores modern
  CSS layout.
- **Charts as nested HTML tables with `bgcolor` fills** — no inline `<svg>`, `<canvas>`,
  Chart.js, or external images (Outlook's Word engine renders none of those reliably).
- **Web-safe fonts with brand-first fallback** — the builder names the Cover Re brand
  fonts first then a web-safe fallback the client actually renders: body
  `'Inter', Arial, Helvetica, sans-serif`; serif headings
  `'Cormorant Garamond', Georgia, 'Times New Roman', serif`; wordmark
  `'Outfit', 'Helvetica Neue', Arial, sans-serif`. No `@font-face`, no Google Fonts.
- **No `<script>`** anywhere.
- **Light Cover Re theme (paste-robust)** — white card on warm off-white (`#ECEAE4`), dark
  text (`#15140F` / `#26241F`), warm tan accent for rules / section numbers / bar fills
  (`#C49A6C`), with a slightly darker tan (`#9A6A2E`) for tan *text* so it stays legible on
  white. Chosen because Outlook frequently strips cell background colors when an email is
  pasted into the compose window — a light theme keeps every text element dark-on-light, so
  it remains readable even if the fills drop. Bars are tan on a light track.
- The header carries the lowercase `cover re` wordmark (built as live text, so it renders
  everywhere — no logo image, which Outlook would not show).

You don't hand-write any of this — you supply the spec JSON (see `terms_schema.md`) and the
builder emits compliant HTML. This guide tells you what to put in each part so the draft is
complete and useful.

## Section order (top to bottom)

1. **Header band** — `cover re` wordmark, document title, reinsurer line, date, prepared-by.
2. **Recommendation callout** — `narrative.recommendation`. The single most important
   line: what you're asking the committee to approve and your recommendation.
3. **Subject business summary** — `narrative.business_summary`. What the cedent does, the
   program, the structure in plain terms.
4. **Risk profile** — `narrative.risk_profile_notes` (optional intro) + the charts
   (`charts.geo`, `charts.class`, `charts.limits`) + the optional `charts.geo_map`
   tile-grid cartogram (US state grid shaded by premium intensity, shown under the geo
   bar) + `narrative.other_metrics` as KPI tiles. This is where geography, class mix,
   limits/attachment, policy count, average limit, top exposures go.
5. **Strengths** — `narrative.strengths`.
6. **Weaknesses & mitigants** — `narrative.weaknesses`, each rendered as the concern paired
   with the "why we're okay with it" mitigant. Two columns.
7. **Proposed terms** — a clean table built from `terms` (the same data as the PDF). This
   gives the committee the economics inline without opening the attachment.
8. **Noteworthy items** — `narrative.noteworthy` (optional).

> There is deliberately **no authorization-expiration callout in the HTML.** The expiration
> belongs to the PDF terms sheet only.

## Writing the narrative well

- **Recommendation** — lead with the verb: "We recommend authorizing a 25% quota share of
  …". State the ask and your stance.
- **Strengths / weaknesses** — be specific and quantified where the submission supports it.
  Every weakness MUST carry a mitigant; an unmitigated weakness either needs a mitigant or
  shouldn't be presented as acceptable.
- **other_metrics tiles** — good candidates: total insured value, policy count, average
  limit, largest single risk, top state/region share, prior-year loss ratio.

## Chart data

Each chart series is `[{"label","value"}, …]`. Keep series to ≤ 8 rows and roll the tail
into "Other". Values can be percentages or absolute — the builder scales bars to the series
max and prints the raw value at the end of each bar. Only include a chart if you have real
numbers from the submission; never fabricate a split to fill the section.
