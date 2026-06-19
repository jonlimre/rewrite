# Actuarial Pricing Analysis

`pricing.py` reads `pricing_inputs.xlsx` from a project directory and writes a
formula-driven `pricing_analysis.xlsx` and a one-page `pricing_report.pdf` to
the same directory.

## Usage

```
python pricing.py <project_dir>
```

`<project_dir>` defaults to the script's own directory if omitted.

## Inputs: `pricing_inputs.xlsx`

AYs are listed oldest-first throughout. The oldest AY is implicitly at the
terminal dev age; each newer AY moves one step earlier.

- **`triangle_paid`, `triangle_reported`** *(optional)* — AY in col A, dev ages
  across row 1, cumulative loss values.
- **`latest_data`** — one row per AY:
  `AccidentYear, EarnedPremium, OnLevelFactor, PaidLoss, ReportedLoss, LossTrend, ExposureTrend`.
- **`ldf_inputs`** — one row per AY:
  `AccidentYear, UserPaid, UserReported, IndustryPaid, IndustryReported, BrokerPaid, BrokerReported`.
  Each value is the AY's current-age-to-next-age ATA (tail factor for the
  oldest AY).
- **`assumptions`** — Parameter / Value pairs:
  - `TargetEffectiveDate` (date) — prospective-trending target
  - `TailFactor_Paid`, `TailFactor_Reported` — used by Section 1 Selected row's
    Tail column
  - `DevAges` — comma-separated dev ages, e.g. `"12,24,36,...,120"`

## Outputs

### `pricing_analysis.xlsx`

Formula-driven Excel (auditable and editable).

- **`Inputs_*`** — verbatim copies of the input sheets.
- **`LDFs_Paid`, `LDFs_Reported`**:
  - *Section 1 (rows 1–27)* — triangle age-to-age analysis: per-AY ratios,
    simple/wtd averages over 3 / 5 / 7 / 10 / all yrs, Selected ATA per dev
    pair (default = wtd 5-yr).
  - *Section 2 (rows 29–40)* — Per-AY table:
    `AccidentYear, CurrentDevAge, Triangle ATA, Industry ATA, Broker ATA, User ATA, Selected ATA, Cumulative LDF`.
    Selected ATA defaults to Triangle ATA; Cumulative LDF = `PRODUCT` down the
    Selected column.
- **`LossRatios`** — per AY: PaidLR/ReportedLR (vs EP), Historical CL ULR
  (developed-to-ult vs EP), trend factors, Prospective CL/BF/CC ULRs
  (trended on-level).
  Totals block: 3yr / 5yr / 7yr / 10yr / All Years / All Yrs × MRY (= all years
  *except* most recent). **BF a priori** = vol-wtd Prosp_CL_ULR over All Yrs ×
  MRY; **CC ELR** = SUM(trended loss) / SUM(used-up EP) over the same subset.
- **`Summary`** — per-AY and totals: Hist CL Paid/Reported and Prosp CL/BF/CC
  Paid/Reported side-by-side.

### `pricing_report.pdf`

One-page landscape: title, the Summary table, bullet observations.
Observations propagate any workbook warnings and flag heuristic issues
(CL ULR spread > 10%, BF vs CL drift > 5% on newest AY, negative ULRs).

## Edge cases handled

- **No triangle**: Section 1 averages stay blank; Per-AY Selected ATA falls
  back to User input.
- **`n_ays` ≠ `n_dev`**: truncates to `min` (drops oldest AYs or largest dev
  ages as appropriate); yellow warning row written to `Inputs_Assumptions`.
- **`n < 3`**: BF/CC anchors fall back to All Years (All Yrs × MRY needs ≥ 3
  AYs); warning written; shorter totals rows whose window exceeds `n` are
  suppressed.

## Dependencies

- Python: `pandas`, `openpyxl`, `reportlab`
- CLI tool: `libreoffice` (or `soffice`) — only needed for the PDF leg, which
  evaluates the analysis workbook's formulas before reading values. If it's
  not on `PATH` the script prints a warning and writes only the xlsx.
