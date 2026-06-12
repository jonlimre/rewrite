# Extraction hints — where each `pricing_inputs.xlsx` field lives in a typical submission

A reinsurance submission usually contains some mix of:

- a **broker term sheet** or **slip** (PDF / Word) — treaty terms, effective
  date, layer structure
- an **actuarial exhibit pack** (xlsx, sometimes PDF) — premium history,
  loss triangles, LDFs, ULR roll-up
- a **cedent narrative** (Word / PDF) — book description, mix changes, large
  losses, reserving philosophy
- **bordereau / large-loss listings** (xlsx)
- **regulatory filings** (PDF, e.g. Schedule P)
- a **broker pitch** (PowerPoint) — summarised view of all of the above

Below: how to recognise each input field across these sources.

---

## `latest_data` fields

### `AccidentYear`
- Premium/loss roll-up tables: first column, header typically "AY", "Acc Yr",
  "Accident Year", or year only.
- Triangles: row labels in the leftmost column.
- Schedule P (US filings): "Accident Year" column in Parts 1–4.
- Determine the AY range from the longest available history; truncate to
  what is consistently populated across premium AND loss.

### `EarnedPremium`
- Premium history exhibit: column labelled "Earned Premium", "EP",
  "Subject EP", "Net EP" or "GEP" depending on basis.
- If both gross and net are shown, prefer the basis matching the treaty
  (quota share → subject; XOL → subject before loss).
- Currency: keep as supplied; do **not** translate.

### `OnLevelFactor`
- "On-level factor", "OLF", "Rate Adequacy", "Rate Index" columns. Newest AY
  is conventionally 1.0; older AYs > 1.0.
- If only a rate-change history is supplied: cumulate forward from the newest
  AY back. Flag as derived in the draft summary.
- If absent entirely: default 1.0 for every AY and flag.

### `PaidLoss`, `ReportedLoss`
- Take the **latest diagonal** from the triangle if a triangle exists; that
  is the AY's current valuation.
- Otherwise from a "Loss Summary" table with columns like "Paid",
  "Incurred", "Reported", "Case + Paid".
- "Incurred" and "Reported" are synonyms in most US contexts (paid + case
  reserves, no IBNR).
- Be careful: some submissions show **ultimates** in the same table — do not
  use ultimates here.

### `LossTrend`
- Cedent's actuarial memo will state a selected loss trend, often a single
  decimal applied to all AYs.
- If only severity and frequency trends are given: multiply them.
- Default 0.04 if missing; flag.

### `ExposureTrend`
- Usually labelled "Exposure trend", "Premium trend", or "Rate-adjusted
  premium trend". Often near loss trend in the memo.
- Default 0.02 if missing; flag.

---

## `ldf_inputs` fields

### `UserPaid`, `UserReported`
- Cedent's **selected** ATA per AY, if the exhibit shows a selection row
  beneath averages.
- If only a single point estimate per dev age is shown (not per AY), expand
  it across AYs by aligning dev age to AY position.
- If absent: leave blank — Selected ATA will fall back to the Triangle ATA.

### `IndustryPaid`, `IndustryReported`
- Look for "Industry", "RAA", "Schedule P benchmark", "Best's", "Reinsurance
  Association" tables.
- Often a single column of dev-age factors; map by dev-age position.

### `BrokerPaid`, `BrokerReported`
- Broker exhibits often have a "Selected" column or a "Broker Selection"
  row.
- May be identical to Industry or Cedent if the broker has not opined
  independently — note this in the draft summary.

---

## `triangle_paid`, `triangle_reported`

- Look for sheet names containing "Paid", "Reported", "Incurred",
  "Triangle", "Development".
- Cumulative is preferred. If only incremental is supplied, cumulate left to
  right.
- Dev-age column headers usually months (12, 24, 36, …). Quarters (3, 6, 9)
  or years (1, 2, 3) sometimes appear — convert to months.
- Reject any triangle whose newest diagonal does not match the
  `PaidLoss`/`ReportedLoss` you picked for `latest_data` — that signals
  different valuation dates.

---

## `assumptions` fields

### `TargetEffectiveDate`
- Treaty slip / term sheet: "Effective Date", "Inception Date", "Period",
  "12 months from".
- If a renewal window is given (e.g. "1/1 renewal"), pick the first day of
  the upcoming renewal period.

### `TailFactor_Paid`, `TailFactor_Reported`
- Actuarial exhibit may show a "tail" row at the end of the LDF triangle.
- Or stated in the memo: "We select a tail factor of 1.02 on a paid basis".
- Default 1.0 each and flag if no opinion supplied.

### `DevAges`
- Read from triangle column headers if a triangle exists.
- Otherwise default to `[12, 24, 36, …, 12 * n_ays]`.
