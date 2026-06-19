# `resus` — report spec schema

The builder (`build_resus_pdf.py`) reads a single **spec JSON** and emits
`diligence_report.pdf`. You assemble this object from the confirmed entities + the verified
research findings + the S&P pull, then `Write` it to `<OUT_DIR>/.resus_spec.json` and run the
builder. Nothing in the report is rendered that you did not put in the spec — never let the
builder invent content.

**The report is about the counterparties, not the deal.** Keep submission/deal details (deal
name, treaty terms, premium, reference codes) out of `meta` and the report.

## Top-level shape

```json
{
  "meta":    { ... },
  "summary": { "headline": "...", "flags": [ ... ] },
  "entities": [ { entity }, ... ],
  "methodology": "optional string (a sensible default is used if omitted)",
  "limitations": "optional string (a sensible default is used if omitted)"
}
```

## `meta`

| Field | Required | Notes |
|---|---|---|
| `title` | no | Defaults to "Counterparty Due Diligence". Keep it counterparty-focused — no deal name. |
| `date` | yes | Report date `YYYY-MM-DD` (the day research was run). Shown top-right of the header. |
| `prepared_by` | no | e.g. "Cover Re Underwriting". |
| `reinsurer` | no | Defaults to the Cover Re SPC #1 line used across the toolkit. |

> **Do not** include `submission` or `reference` (deal identifiers) — the report is about the
> counterparties only, and the builder no longer renders deal info.

## `summary`

- The report opens with a **"Counterparties Vetted"** strip (role · name · overall flag) that
  the builder auto-derives from `entities[]` + `flags` — no extra fields needed.
- `headline` — 2–4 sentences: the counterparties vetted and the single most important takeaway
  (e.g. "One red flag: open D&O litigation against the MGA's CEO"). Keep it counterparty-focused.
- `flags` — the **executive risk matrix**, one object per vetted entity. Each carries a flag
  per dimension plus an `overall`:

```json
{
  "entity": "Meridian Coastal Insurance Company",
  "role": "Cedent",
  "financial_distress": "amber",
  "leadership": "green",
  "partners": "green",
  "litigation": "amber",
  "reviews": "red",
  "other": "green",
  "overall": "amber"
}
```

**Flag values (use exactly these):**

| Value | Meaning | Color |
|---|---|---|
| `red` | Material adverse finding | red |
| `amber` | Caution / monitor | amber |
| `green` | No material concern found | green |
| `grey` | Not assessed / not applicable | grey |

The `role` must be one of **`Cedent`**, **`MGA`**, **`TPA`**. (MGU is internal to Cover Re and
is **not** vetted.)

## `entities[]`

```json
{
  "name": "Meridian Coastal Insurance Company",
  "role": "Cedent",
  "resolved": {
    "legal_name": "Meridian Coastal Insurance Company",
    "domain": "meridiancoastal.example",
    "jurisdiction": "Florida, USA",
    "identifiers": "NAIC #99001 (illustrative); FL OIR licensed; S&P Capital IQ ID IQ0000000",
    "confidence": "High",
    "confirmed": true,
    "note": "Distinct from Meridian Coastal Insurance Agency LLC (the affiliated MGA)."
  },
  "dimensions": [ { dimension }, ... ],
  "sp_financials": { ... }
}
```

- `resolved.confidence` — `High` | `Medium` | `Low` (your entity-match confidence).
- `resolved.confirmed` — `true` only after the user confirmed the match at **Gate 1**.
- `resolved.identifiers` — regulator IDs (NAIC for US insurers), domain, and the S&P entity
  identity you searched. This is what makes the report auditable.

### `dimensions[]` — fixed keys, fixed order

Use these six keys (omit a dimension only if truly N/A — prefer including it with
`nothing_found: true`):

| `key` | `label` |
|---|---|
| `financial_distress` | Financial distress |
| `leadership` | Leadership & governance |
| `partners` | Partner relationships |
| `litigation` | Litigation |
| `reviews` | Customer reviews |
| `other` | Other relevant intel |

```json
{
  "key": "litigation",
  "label": "Litigation",
  "flag": "amber",
  "summary": "Two open matters and one settled. Plain-language synthesis goes here.",
  "nothing_found": false,
  "findings": [
    {
      "claim": "Acme Re filed breach-of-contract suit against the cedent in SDNY (2024).",
      "assessment": "verified",
      "sources": [
        {"title": "Acme Re v. Meridian Coastal, Complaint", "publisher": "PACER / CourtListener",
         "url": "https://www.courtlistener.example/docket/...", "date": "2024-08-12"},
        {"title": "Reinsurer sues Florida carrier", "publisher": "Insurance Insider",
         "url": "https://www.example.com/...", "date": "2024-08-15"}
      ]
    }
  ]
}
```

- `flag` — same four values as the matrix.
- `summary` — your synthesized, plain-language read of the dimension. Keep claims here backed
  by the `findings` below.
- `nothing_found` — when `true`, the builder renders **"No adverse findings located"** for
  that dimension (this is required by the strict posture — never go silent).
- `findings[]` — the evidence. Each finding:
  - `claim` — one factual statement.
  - `assessment` — `verified` (≥2 independent sources), `single-source` (one source — label it),
    `inference` (your reasoning, not directly stated by a source), or `refuted` (checked and
    found false; keep it to document the check).
  - `sources[]` — every finding needs ≥1 source: `title`, `publisher`, `url`, `date`.
    **Material negative claims require ≥2 independent sources to be `verified`.**

### `sp_financials` (optional per entity)

Preferred form is **`tables`** — one or more multi-period tables transcribed from Capital IQ,
each with its own `commentary` calling out **concerning trends/outliers**. For a carrier, the
standard set (see `sp_capitaliq_playbook.md`) is: **P&C Financial Highlights** (three periods —
latest quarter, latest year-end, prior year-end), **RBC & solvency**, **Reinsurance
recoverables & cession**, **Investments**, and **Schedule P** — filtered to the submission's
line of business and capturing **both Incurred and Paid loss ratios** plus reserve development.

```json
{
  "available": true,
  "source_url": "https://www.capitaliq.spglobal.com/web/client#/company/4255497",
  "captured": "2026-06-18",
  "tables": [
    {
      "title": "U.S. Stat — P&C Financial Highlights (group, SNL)",
      "columns": ["FY2024", "FY2025", "Q1 2026"],
      "rows": [
        {"label": "Capital & surplus ($000)", "values": ["223,591", "281,278", "283,232"]},
        {"label": "Return on avg equity (C&S) %", "values": ["5.89", "(7.46)", "4.38"]},
        {"label": "RBC ratio (TAC/ACL) %", "values": ["377", "432", "NA"]}
      ],
      "commentary": "FY2025 was a net loss year (ROAE -7.46%); surplus grew only via $45M of new surplus notes, not earnings. RBC remains strong."
    },
    {
      "title": "Schedule P — Commercial Auto Liability — Incurred Loss Ratios & development (%)",
      "row_header": "Accident Year",
      "columns": ["12mo", "24mo", "36mo", "48mo", "% init dev"],
      "rows": [
        {"label": "Carrier NET (all AYs)", "values": ["~0", "NM", "NM", "NM", "NM"]},
        {"label": "Industry 2024", "values": ["74.07", "74.67", "—", "—", "+0.82"]}
      ],
      "commentary": "Filtered to the program's line of business. Net Schedule P ratios are ~0/NM because the carrier cedes ~100% (fronting); the meaningful figures are the industry benchmark + its adverse development. Add a companion PAID table (payout pattern) the same way."
    }
  ],
  "annual_statement": "Latest statutory annual statement filed 12/31/2025; Q1 2026 quarterly on file.",
  "notes": "Transcribed from Capital IQ Pro (SNL) on the capture date.",
  "not_available_reason": null
}
```

- **`tables[]`** — each: `title`; `columns` (the **value**-column headers only — periods or
  maturities); optional `row_header` (the header for the first/label column, e.g.
  "Accident Year" — leave unset for a blank first-column header); `rows` (`{label, values[]}`
  where `values` aligns 1:1 to `columns` and `label` is the row's first-column text); and
  `commentary` (your trends/outliers call-out, rendered as a tinted box under the table).
  Transcribe figures exactly — never estimate; use `NM`/`NA`/`—` as shown in Capital IQ.
- A legacy flat **`metrics`** list (`{label, value, period}`) is still accepted for simple cases.
- Optional `as_of` string for a single-period summary line.
- When the entity is **not covered** in Capital IQ, set `available: false` and give
  `not_available_reason` (e.g. "Private MGA; no S&P coverage"). The builder states this
  explicitly rather than leaving a blank.
- Always carry `source_url` + `captured` date so every figure is traceable.

## `methodology` / `limitations`

Optional strings. If omitted, the builder inserts a default note covering: search recency,
that findings are point-in-time, the ≥2-source rule for negatives, and that S&P figures were
transcribed from an authenticated Capital IQ Pro session on the capture date. Override when a
specific caveat applies (e.g. "TPA identity inferred from the slip; not independently confirmed
by the cedent").
