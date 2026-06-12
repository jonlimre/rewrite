---
name: regulr
description: Compute a cedent's REinsurance Ground Up Loss Ratio (regulr) from a reinsurance submission. Ingests PDFs, Word, Excel, PowerPoint, and images and produces an actuarial pricing analysis. Use when the user asks to "price a submission", "run regulr", "ingest this submission", "analyze this treaty / cedent", "compute the ground-up loss ratio", or points at a folder of broker/cedent loss exhibits. Produces pricing_inputs.xlsx + a formula-driven pricing_analysis.xlsx + a one-page pricing_report.pdf.
argument-hint: "[path-to-submission-folder]"
allowed-tools: Read Glob Grep Bash Skill AskUserQuestion Write
---

# regulr — REinsurance Ground Up Loss Ratio

The name expands to **REinsurance Ground Up Loss Ratio** — the cedent's
loss ratio before any cession or retention split, which is what the
underlying pricing analysis is built around.

Goal: turn a folder of submission documents into the three artifacts produced
by `pricing.py`:

1. `pricing_inputs.xlsx` (built by this skill)
2. `pricing_analysis.xlsx` (formula-driven, built by `pricing.py`)
3. `pricing_report.pdf` (one-page summary, built by `pricing.py`)

Bundled assets live under `${CLAUDE_PLUGIN_ROOT}/skills/regulr/`:

- `flr/pricing.py` — the pricing engine (do not modify).
- `flr/CLAUDE.md` — the engine's own documentation.
- `reference/schema.md` — the **field dictionary** for `pricing_inputs.xlsx`.
  Read this before populating anything.
- `reference/extraction_hints.md` — where to find each field in typical
  submission documents. Read this before classifying files.
- `scripts/build_inputs_xlsx.py` — writes `pricing_inputs.xlsx` from a JSON
  spec.

## Step-by-step flow

### 1. Resolve the submission source

- If `$1` is set, treat it as the submission folder.
- Else, if files are attached in the conversation, use those.
- Else, prompt the user for a path (do not silently fall back to CWD —
  reinsurance submissions are always grouped).

Set `OUT_DIR` to the resolved submission folder unless the user asks for a
different output location.

### 2. Discover and classify files

`Glob` the submission folder (non-recursive first; recurse only if the top
level has nothing relevant):

```
*.pdf, *.xlsx, *.xlsm, *.xls, *.csv, *.docx, *.pptx, *.png, *.jpg, *.jpeg
```

For each file, extract content using the matching skill:

| Extension | How to extract |
|---|---|
| `.pdf` | `Skill(anthropic-skills:pdf)` |
| `.xlsx` / `.xlsm` / `.xls` / `.csv` | `Skill(anthropic-skills:xlsx)` |
| `.docx` | `Skill(anthropic-skills:docx)` |
| `.pptx` | `Skill(anthropic-skills:pptx)` |
| `.png` / `.jpg` / `.jpeg` | `Read` (multimodal vision) |

Where independent, **run extractions in parallel** (one assistant turn,
multiple tool calls).

Then classify each file into one of these buckets (a file can populate
multiple):

- **premium history / loss roll-up** → drives `latest_data`
- **paid triangle** → `triangle_paid`
- **reported / incurred triangle** → `triangle_reported`
- **LDF benchmark** (industry / broker) → `ldf_inputs`
- **treaty term sheet / slip** → `assumptions.TargetEffectiveDate`
- **actuarial narrative** → `LossTrend`, `ExposureTrend`, tail factors
- **other** (large-loss listings, regulatory filings, marketing decks) →
  context only

Use the patterns in `reference/extraction_hints.md` to do the mapping.

### 3. Build a draft spec

Construct the JSON spec for `build_inputs_xlsx.py` (shape documented in that
script's docstring). For every required field:

- If found in the submission, record the value AND the source
  (`file:page`).
- If missing, mark it.

### 4. Apply safe defaults; collect required gaps

**Auto-fill silently (but list in the draft summary as DEFAULTED):**

| Field | Default |
|---|---|
| `OnLevelFactor` | 1.0 for every AY |
| `LossTrend` | 0.04 |
| `ExposureTrend` | 0.02 |
| `TailFactor_Paid` | 1.0 |
| `TailFactor_Reported` | 1.0 |
| `DevAges` | `12,24,36,...,12*n_ays` |
| Any `User*` / `Industry*` / `Broker*` LDF column missing | blank cells (Selected ATA falls back to Triangle ATA) |

**Required — must come from the submission or the user. Use
`AskUserQuestion` to fill any that are still missing after extraction:**

- The list of `AccidentYear`s.
- `EarnedPremium` per AY.
- `PaidLoss` per AY.
- `ReportedLoss` per AY.
- `TargetEffectiveDate`.

### 5. Present draft summary

Render a markdown table to the user with:

- Every required field, its value, and source citation.
- Every defaulted field, with a `(DEFAULT)` flag.
- Any remaining gaps with the resolution route (asked / waiting).

End with: **"Confirm to write `pricing_inputs.xlsx` and run the pricing
engine, or tell me what to adjust."** Wait for explicit confirmation
before proceeding. Do not write files speculatively.

### 6. Write the spec JSON and build the inputs workbook

Once confirmed:

1. `Write` the spec to `<OUT_DIR>/.regulr_spec.json` (the leading dot keeps
   it out of the way; the user can inspect or re-run from it).
2. Run the inputs-builder. PowerShell example:

   ```powershell
   python "$env:CLAUDE_PLUGIN_ROOT/skills/regulr/scripts/build_inputs_xlsx.py" `
     "<OUT_DIR>" `
     "<OUT_DIR>/.regulr_spec.json"
   ```

   Bash example:

   ```bash
   python "${CLAUDE_PLUGIN_ROOT}/skills/regulr/scripts/build_inputs_xlsx.py" \
     "<OUT_DIR>" \
     "<OUT_DIR>/.regulr_spec.json"
   ```

### 7. Run the pricing engine

```bash
python "${CLAUDE_PLUGIN_ROOT}/skills/regulr/flr/pricing.py" "<OUT_DIR>"
```

Required runtime dependencies (verify before running, install only with the
user's permission): `pandas`, `openpyxl`, `reportlab`, and the `libreoffice`
CLI for formula evaluation prior to PDF generation.

### 8. Report back

Reply with:

- Markdown links to the three output files: `pricing_inputs.xlsx`,
  `pricing_analysis.xlsx`, `pricing_report.pdf` (relative to the working
  directory).
- A 1–2 sentence headline: Hist CL ULR range across AYs, Prospective CL/BF
  ULR for the newest AY, BF a priori.
- Any warnings the engine emitted (it writes them to a row on
  `Inputs_Assumptions` in the analysis workbook; surface them).

## Guardrails

- Never invent loss or premium numbers. If the submission cannot supply
  them, ask.
- Never overwrite a pre-existing `pricing_inputs.xlsx` in `OUT_DIR` without
  warning the user and offering a `.bak` rename.
- If the submission mixes currencies, pause and ask which to use — do not
  silently convert.
- If you find conflicting values for the same field across documents (e.g.
  premium in slip vs. exhibit), surface both in the draft summary and let
  the user pick.
- Do not modify `flr/pricing.py`. If the engine errors, report the
  traceback rather than patching it.
