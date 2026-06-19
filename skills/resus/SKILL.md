---
name: resus
description: Run sourced counterparty due diligence on a reinsurance submission's cedent, MGA, and TPA. Resolves each entity (with a confirmation gate), runs cited + adversarially-verified open-web research (financial distress, controversial leadership, partner-relationship problems, ongoing/settled litigation, customer reviews, other relevant intel), and pulls S&P Capital IQ statutory financials (financial highlights, RBC/capital adequacy, reinsurance recoverables, investments, and Schedule P reserves) via an interactive browser session. Produces a standalone, fully-cited PDF diligence report. Use when the user asks to "run resus", "vet the cedent/MGA/TPA", "do due diligence on this submission", "background-check the counterparties", "research this cedent", or "are these counterparties safe to write". Produces diligence_report.pdf.
argument-hint: "[path-to-submission-folder | Reference code | entity names]"
allowed-tools: Read Glob Grep Bash Skill Workflow AskUserQuestion Write WebSearch WebFetch mcp__Claude_in_Chrome__list_connected_browsers mcp__Claude_in_Chrome__select_browser mcp__Claude_in_Chrome__tabs_context_mcp mcp__Claude_in_Chrome__navigate mcp__Claude_in_Chrome__find mcp__Claude_in_Chrome__computer mcp__Claude_in_Chrome__javascript_tool mcp__Claude_in_Chrome__get_page_text mcp__Claude_in_Chrome__read_page mcp__Claude_in_Chrome__read_network_requests mcp__Claude_in_Chrome__resize_window
---

# resus — REinsurance reSearch Underwriting Submissions

`resus` vets the external counterparties on a reinsurance submission — the **cedent**, the
**MGA**, and the **TPA** — and produces a committee-ready, **fully sourced** due-diligence
report: `diligence_report.pdf`, a branded `reportlab` document in Cover Re styling (near-black
header band, tan accent, `cover re` wordmark).

The report opens with a **Counterparties Vetted** strip (role · name · overall flag) and a
**Bottom Line** summary, then an **executive risk matrix** (a red/amber/green flag per entity per
dimension), then a per-entity section (resolved identity, each dimension with its flag + cited
findings, and the S&P financials with a "concerning trends & outliers" callout), a **sources
appendix**, and a methodology/limitations note.

**The report is about the counterparties, not the deal.** Do not put submission/deal details
(deal name, treaty terms, premium, reference codes) in the report — keep it focused purely on
the cedent, MGA, and TPA.

## Core principle: sourced, verified, gated — never fabricated

`resus` runs in **strict mode**. This is the whole point of the skill — do not relax it:

- **Cite everything.** Every factual claim carries a source URL + publisher + date. No source
  → not a finding (at most a labelled `inference`).
- **Two sources for negatives.** Any *material adverse* claim needs ≥2 independent sources to
  be `verified`; one source is `single-source` and flagged as such.
- **Confirm identity before researching.** Resolve each entity, then **stop at Gate 1** for the
  user to confirm the matches *before* any deep research or S&P pull. Wrong-entity reports are
  the worst failure mode.
- **State the negative.** A dimension with nothing found is rendered "No adverse findings
  located" — never left silently blank.
- **Never invent** a figure, quote, case number, date, rating, or URL.

Read these before you start (bundled under `${CLAUDE_PLUGIN_ROOT}/skills/resus/`):

- `reference/research_dimensions.md` — the six dimensions, search recipes per entity type, the
  sourcing/verification rules, and entity-resolution guidance. **Read first.**
- `reference/sp_capitaliq_playbook.md` — how to pull S&P financials via Claude in Chrome.
- `reference/report_schema.md` — the spec-JSON field dictionary the builder consumes.

## Step-by-step flow

### 1. Resolve the submission input → set OUT_DIR

You need to know which submission to vet. In priority order:

- **`$1` is a folder path** → use it. The deal folder name encodes `{Cedent} ({MGA}) {LOB}
  {TreatyType}`; the `Submission` subfolder holds the email PDF + attachments.
- **`$1` is a 4-letter Reference code** → it identifies a row in the ingestion **Submissions**
  sheet (columns typically include `Cedent`, `MGA`, `MGU`, `Broker`, `Attachments Folder`,
  `Reference`). If the user points you at a local export/CSV of that sheet, read it to get the
  entities + deal folder; otherwise ask for the submission folder. The skill does **not** assume
  any particular sheet file exists on disk — work from whatever the user provides.
- **Entity names given directly** → use them, but still try to locate the submission docs (they
  carry the TPA and the legal-entity details).
- **Nothing given** → ask for the submission folder or Reference code.

Set `OUT_DIR` to the deal folder (or a `Diligence` subfolder inside it). Default output:
`<OUT_DIR>/diligence_report.pdf`.

> Background/unattended note: if files live on a shared network drive a background reader can't
> reach, stage them locally first. The interactive S&P step (step 5) only runs when the user is
> present and logged in; in unattended runs, skip S&P and complete it on the next interactive run.

### 2. Identify the counterparties to vet

Extract from the submission. `Glob` the `Submission` folder and read the email PDF + relevant
attachments, running independent extractions in parallel:

| Extension | How to extract |
|---|---|
| `.pdf` | `Skill(anthropic-skills:pdf)` |
| `.xlsx` / `.xlsm` / `.xls` / `.csv` | `Skill(anthropic-skills:xlsx)` |
| `.docx` | `Skill(anthropic-skills:docx)` |
| `.pptx` | `Skill(anthropic-skills:pptx)` |
| `.png` / `.jpg` / `.jpeg` | `Read` (vision) |

Determine the three counterparties:

- **Cedent** and **MGA** — usually in the folder name / sheet row; confirm against the docs.
- **TPA** — *usually not captured at intake.* Derive it from the slip, program summary, or
  claims-handling agreement. If no TPA is named, record that and set its flags to `grey`.
- **The MGU is internal to Cover Re (its own reinsurance underwriting entities) — do NOT vet it.**

### 3. Resolve each entity to a canonical identity

Per `research_dimensions.md` (Entity resolution): establish legal name, domain, jurisdiction,
**regulator identifiers** (NAIC code for US insurers; licensing state for MGAs/TPAs), public-co
status (ticker/CIK), and **affiliate disambiguation** (the same-name agency vs company trap).
Assign a `confidence` (High/Medium/Low). A few targeted web searches here are fine — this is
identity resolution, not the deep dive.

### 4. GATE 1 — confirm the entities (required, before any deep research or S&P)

Present the resolved cedent / MGA / TPA — legal name, domain, jurisdiction, identifiers,
confidence, and the S&P identity you intend to search. Use **`AskUserQuestion`** to have the
user **confirm or correct** each match (especially any Medium/Low confidence or the derived
TPA). Do not proceed to research or S&P until confirmed. Record `resolved.confirmed = true`.

### 5. Open-web due diligence + S&P pull (per confirmed entity)

**5a. Open-web research.** For each entity, work through the six dimensions in
`research_dimensions.md` (`financial_distress`, `leadership`, `partners`, `litigation`,
`reviews`, `other`). Run a small fan-out of targeted searches with `WebSearch`, fetch the
promising hits with `WebFetch`, and extract findings. For a deeper, harder-to-miss sweep you
may delegate to `Skill(deep-research)` or a `Workflow` fan-out — but the sourcing/verification
rules still apply to whatever comes back. Build each dimension object: a `flag`, a synthesized
`summary`, and `findings[]` (each with `claim`, `assessment`, and `sources[]`). Set
`nothing_found: true` where nothing surfaced.

**5b. S&P Capital IQ pull.** Per `sp_capitaliq_playbook.md`, drive the user's authenticated
Capital IQ Pro tab via the **Claude in Chrome** MCP. **Extract each report's data by reading the
grid's DOM with `javascript_tool`** (the snippet is in the playbook) — *not* by screen-grabbing
row by row; the grids are full HTML tables in a same-origin iframe, so one JS call returns every
row exactly (screenshots are a fallback only).

For a carrier (the cedent / any risk-bearing entity), the playbook's **S&P coverage checklist**
defines five **mandatory** categories: **P&C Financial Highlights**, **RBC & Capital Adequacy**,
**Reinsurance recoverables & relationships**, **Investments (P&C Investment Analysis)**, and
**Schedule P** (LOB-filtered). Two rules make this comprehensive rather than ad-hoc:

- **No silent skip.** Each category ends as a transcribed table **or** a logged reason it was
  not captured (e.g. Schedule P "NM — ~100% ceded"). A category dropped without a reason —
  Investment Analysis is the easy one to forget — is a defect. Walk the checklist before moving on.
- **Weave it into the dimensions.** Each category feeds a research dimension (Highlights/RBC/
  Investments/Schedule-P → `financial_distress`; recoverables → `partners`; growth & mix →
  `other`). Lift the figures that move a flag into a **cited finding in that dimension**
  (`assessment: "single-source"`, S&P as the source) — the `sp_financials` tables are the
  auditable backup, the dimension is where the number informs the call.

Transcribe verbatim into `sp_financials.tables` (columns + rows) and **call out concerning
trends/outliers** in each table's `commentary` (loss year, yield compression, liquidity decline,
adverse reserve development, heavy unauthorized cession, below-investment-grade asset share,
etc.). Capture `source_url` + `captured` date. If an entity isn't covered at all (e.g. a private
MGA/TPA with no statutory data), set `available: false` with a reason.

### 6. Adversarial verification pass

Before assembling, re-examine every `red`/`amber` finding with the skeptic's checklist in
`research_dimensions.md`: right entity (not a namesake)?, sources truly independent (not one
echoed wire story)?, current (not a stale resolved matter)?, would it survive the user reading
the cited source? Downgrade `verified`→`single-source`, lower flags, or mark `refuted` as
warranted. A finding that can't clear this is removed — not published on a hunch.

### 7. Assemble the spec and build

Per `report_schema.md`:

1. Build the spec object (`meta` — title/date only, **no deal info**; `summary`
   with the risk-matrix `flags`; `entities[]`; optional `methodology`/`limitations`).
2. `Write` it to `<OUT_DIR>/.resus_spec.json`.
3. Build the report:

   ```bash
   python "${CLAUDE_PLUGIN_ROOT}/skills/resus/scripts/build_resus_pdf.py" \
     "<OUT_DIR>/.resus_spec.json" "<OUT_DIR>/diligence_report.pdf"
   ```

   PowerShell uses the same call with `$env:CLAUDE_PLUGIN_ROOT`.

The PDF builder needs `reportlab` (already used by `regulr`/`replace`; verify before running,
install only with the user's permission).

### 8. Report back

Reply with:

- A link to the output (`diligence_report.pdf`).
- The **headline** + the count of red/amber flags by entity (e.g. "MGA: 1 red, 2 amber").
- Any **unconfirmed/low-confidence** identities or **single-source** material findings the user
  should personally check, plus the **S&P trends/outliers** worth their attention.

## Guardrails

- **Never skip Gate 1.** No deep research or S&P pull before the user confirms identities.
- **Never fabricate or over-state.** Missing data stays missing; a wrong figure or a
  mis-attributed lawsuit is a serious error. Material negatives need ≥2 independent sources.
- **Right entity only.** Re-confirm every adverse finding and every S&P figure against the
  resolved identity (NAIC/ticker/legal name) — same-name affiliates are the trap.
- **S&P is interactive and read-only.** Work in the user's logged-in session; never handle
  credentials/MFA; pull only what this submission needs.
- **Don't vet the MGU** — it's an internal Cover Re underwriting entity, not an external counterparty.
- **No deal info in the report** — the PDF is about the counterparties only; keep submission
  name, treaty terms, premium, and reference codes out of it.
- Do not overwrite an existing `diligence_report.pdf` in `OUT_DIR` without warning and offering
  a `.bak` rename.
